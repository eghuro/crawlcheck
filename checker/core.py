import logging
import queue
import os
import time
import requests
from urllib.parse import quote
from database import DBAPI, VerificationStatus
from common import PluginType, PluginTypeError
from net import Network, NetworkError, ConditionError, StatusError
from filter import FilterException, Reschedule
from transaction import Transaction, createTransaction, TouchException, RedisTransactionQueue, Journal
from rfc3987 import match


class Core:
    """ The core of the application. Main loop is implemented here."""

    def __init__(self, plugins, filters, headers, conf, defTyp):
        self.plugins = plugins
        self.log = logging.getLogger(__name__)
        self.conf = conf
        self.db = DBAPI(conf)
        self.files = []
        self.__time_subscribers = []
        self.volume = 0

        self.filters = filters
        for f in filters:
            try:
                self.__time_subscribers.append(f.getTimeSubscriber())
            except AttributeError:
                pass
        self.header_filters = headers

        self.queue = RedisTransactionQueue(self.db, self.conf)

        self.journal = Journal(self.db, self.conf, defTyp)

        types = set()
        extended = []
        for plugin in self.plugins:
            try:
                types.update(plugin.contentTypes)
            except:
                extended.append(plugin)

        for plugin in self.plugins+headers+filters:
            self.__initializePlugin(plugin, types, extended)

        self.__push_entry_points()
        self.rack = Rack(self.conf.type_acceptor, self.conf.regex_acceptor,
                         plugins)

    def __push_entry_points(self):
        for entryPoint in self.conf.entry_points:
            self.log.debug("Pushing to queue: %s, data: %s" %
                           (entryPoint.url, str(entryPoint.data)))
            self.queue.push(createTransaction(self.conf, entryPoint.url, 0, -1,
                                              entryPoint.method,
                                              entryPoint.data))

    def run(self):
        """ Run the checker. """
        with requests.Session() as session:
            self.__run(session)

    def __handle_err(self, msg, transaction,
                     status=VerificationStatus.done_ignored):
        self.log.debug(msg)
        self.files.append(transaction.file)
        self.journal.stopChecking(transaction, status)

    def __filter(self, transaction, session):
        # Custom filters: depth, robots.txt
        for tf in self.filters:
            tf.filter(transaction)

        start = time.time()
        r = transaction.testLink(self.conf, self.journal, session)
        # precte hlavicky

        # custom HTTP header filters, incl. test if ct matches expectation
        for hf in self.header_filters:
            hf.filter(transaction, r)

        return start

    def __run(self, session):
        # Queue
        while not self.queue.isEmpty():
            try:
                transaction = self.queue.pop()
            except queue.Empty:
                continue

            try:
                if type(transaction.uri) != str:
                    transaction.uri = str(transaction.uri)

                self.log.info("Processing %s" % (transaction.uri))

                if not match(transaction.uri):
                    if not match(quote(transaction.uri)):
                        self.log.error("Invalid URI: %s" % (transaction.uri))
                        self.journal.foundDefect(transaction.idno, "invaliduri",
                                                 "URI is invalid",
                                                 transaction.uri, 1.0)
                        self.journal.stopChecking(transaction,
                                                  VerificationStatus.done_ko)
                        continue

                if not transaction.isWorthIt(self.conf):
                    # neni zadny plugin, ktery by prijal
                    self.log.debug("%s not worth my time" % (transaction.uri))
                    self.journal.stopChecking(transaction,
                                              VerificationStatus.done_ignored)
                    continue

                start = self.__filter(transaction, session)
                transaction.loadResponse(self.conf, self.journal, session)
                # precte telo
            except TouchException:  # nesmim se toho dotykat
                self.__handle_err("Forbidden to touch %s" %
                                  (transaction.uri), transaction)
                continue
            except ConditionError:  # URI nebo content-type dle konfigurace
                self.__handle_err("Condition failed", transaction)
                continue
            except FilterException:  # filters
                self.__handle_err("%s filtered out" % (transaction.uri),
                                  transaction)
                continue
            except Reschedule:  # eg. long crawl delay
                self.queue.push_rescheduled(transaction)
                continue
            except StatusError as e:  # already logged
                self.journal.stopChecking(transaction,
                                          VerificationStatus.done_ko)
                self.files.append(transaction.file)
                continue
            except NetworkError as e:
                self.__handle_err("Network error: %s" % (format(e)),
                                  transaction, VerificationStatus.done_ko)
                continue
            else:  # Plugins
                self.__process(transaction, start)

    def __process(self, transaction, start):
        for sub in self.__time_subscribers:
            sub.markStart(start, transaction.uri)
        self.files.append(transaction.file)
        transaction.cache = dict()
        transaction.cache['size'] = transaction.size
        self.journal.startChecking(transaction)
        self.rack.run(transaction)
        self.journal.stopChecking(transaction, VerificationStatus.done_ok)

    def __initializePlugin(self, plugin, types, extended):
        plugin.setJournal(self.journal)
        known_categories = set([PluginType.CRAWLER, PluginType.CHECKER,
                                PluginType.FILTER, PluginType.HEADER])

        if plugin.category not in known_categories:
            raise PluginTypeError

        try:
            plugin.setQueue(self.queue)
        except AttributeError:
            pass

        try:
            plugin.setConf(self.conf)
        except AttributeError:
            pass

        try:
            plugin.setDb(self.db)
        except AttributeError:
            pass

        try:
            plugin.setAcceptable(types, extended)
        except AttributeError:
            pass


class Rack:
    """ Rack stores plugins.
    On run it passes the transaction to individual plugins.
    """
    def __init__(self, typeAcceptor, regexAcceptor, plugins=[]):
        self.plugins = plugins
        self.typeAcceptor = typeAcceptor
        self.regexAcceptor = regexAcceptor
        self.log = logging.getLogger(__name__)

    def run(self, transaction):
        """Let plugins handle the transaction one by one in a sequence."""

        for plugin in self.plugins:
            self.__run_one(transaction, plugin)
        transaction.cache = None

    def __run_one(self, transaction, plugin):
        if self.accept(transaction, plugin):
            self.log.info("%s started checking %s" %
                          (plugin.id, transaction.uri))
            plugin.check(transaction)
            self.log.debug("%s stopped checking %s" %
                           (plugin.id, transaction.uri))

    def accept(self, transaction, plugin):
        """Is the transaction accepted by the plugin?"""

        if not self.typeAcceptor.empty:
            self.typeAcceptor.accept(str(transaction.type), plugin.id)
        else:
            try:
                type_cond = str(transaction.type) in plugin.contentTypes
            except AttributeError:
                type_cond = plugin.acceptType(str(transaction.type))
        regex_cond = self.regexAcceptor.accept(transaction.uri, plugin.id)
        return type_cond and regex_cond
