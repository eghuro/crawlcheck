from multiprocessing import Process, JoinableQueue, Queue
import queue
import logging
import pika
from transaction import TouchException
from net import NetworkError, ConditionError, StatusError
from filter import FilterException
from pluginDBAPI import VerificationStatus

def consumer(q, files, journal, rack):
    log = logging.getLogger(__name__)
    while True:
        log.debug("Consumer iteration")
        try:
            log.debug("Consumer get")
            transaction = q.get(True)
        except queue.Empty:
            log.debug("Consumer queue empty")
            continue
        else:
            log.debug("Consumer running transaction")
            files.append(transaction.file)
            journal.startChecking(transaction)
            rack.run(transaction)
            journal.stopChecking(transaction, VerificationStatus.done_ok)
            q.task_done()


def producer(queue_in, qlock, queue_out, conf, journal, filters, headers):
    log = logging.getLogger(__name__)

    mq_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.conf.getProperty('rabbitHost', 'localhost')))
    mq_channel = self.mq_connection.channel()
    mq_channel.queue_declare(queue='process', durable=True)

    while True:
        log.debug("Producer iteration")
        try:
            log.debug("Lock queue")
            qlock.acquire()
            log.debug("Pop queue")
            transaction = queue_in.pop()
        except queue.Empty:
            log.debug("Queue empty")
            continue
        finally:
            log.debug("Unlock queue")
            qlock.release()

        try:
            if type(transaction.uri) != str:
                transaction.uri = str(transaction.uri)
            log.info("Processing " + transaction.uri)
            r = transaction.testLink(conf, journal)
            if not transaction.isWorthIt(conf):
                log.debug(transaction.uri + " not worth my time")
                journal.stopChecking(transaction, VerificationStatus.done_ignored)
                continue
            for tf in filters:
                tf.filter(transaction)
            for hf in headers:
                hf.filter(transaction, r)
            transaction.loadResponse(conf, journal)
            queue_out.put(transaction, True, None)
        except TouchException:
            log.debug("Forbidden to touch " + transaction.uri)
            journal.stopChecking(transaction, VerificationStatus.done_ignored)
            continue
        except ConditionError:
            log.debug("Condition failed")
            journal.stopChecking(transaction, VerificationStatus.done_ignored)
        except FilterException:
            log.debug(transaction.uri + " filtered out")
            journal.stopChecking(transaction, VerificationStatus.done_ignored)
            continue
        except StatusError:
            journal.stopChecking(transaction, VerificationStatus.done_ko)
            continue
        except NetworkError as e:
            log.error("Network error: " + format(e))
            journal.stopChecking(transaction, VerificationStatus.done_ko)
            continue

def procedure(queue, qlock, conf, journal, filters, headers, files, rack):
    log = logging.getLogger(__name__)
    while not queue.isEmpty():
        qlock.acquire()
        try:
            transaction = queue.pop()
        except queue.empty:
            continue
        finally:
            qlock.release()

        try:
            if type(transaction.uri) != str:
                transaction.uri = str(transaction.uri)
            log.info("Processing " + transaction.uri)
            r = transaction.testLink(conf, journal)
            if not transaction.isWorthIt(conf):
                log.debug(transaction.uri + " not worth my time")
                journal.stopChecking(transaction, VerificationStatus.done_ignored)
                continue
            for tf in filters:
                tf.filter(transaction)
            for hf in headers:
                hf.filter(transaction, r)
            transaction.loadResponse(conf, journal)
            #queue_out.put(transaction, True, None)
        except TouchException:
            log.debug("Forbidden to touch " + transaction.uri)
            journal.stopChecking(transaction, VerificationStatus.done_ignored)
            continue
        except ConditionError:
            log.debug("Condition failed")
            journal.stopChecking(transaction, VerificationStatus.done_ignored)
        except FilterException:
            log.debug(transaction.uri + " filtered out")
            journal.stopChecking(transaction, VerificationStatus.done_ignored)
            continue
        except StatusError:
            journal.stopChecking(transaction, VerificationStatus.done_ko)
            continue
        except NetworkError as e:
            log.error("Network error: " + format(e))
            journal.stopChecking(transaction, VerificationStatus.done_ko)
            continue
        else:
            log.debug("Consumer running transaction")
            files.append(transaction.file)
            journal.startChecking(transaction)
            rack.run(transaction)
            journal.stopChecking(transaction, VerificationStatus.done_ok)

        
        
def start_prod_con(count_prod, count_cons, queue, qlock, conf, journal, filters, headers, files, rack):
    #queue_sync = JoinableQueue()
    #producers = []
    #for i in range(count_prod):
    #    p = Process(target=producer, args=(queue, qlock, queue_sync, conf, journal, filters, headers))
    #    producers.append(p)
    #    p.start()

    #consumers = []
    #for i in range(count_cons):
    #    p = Process(target=consumer, args=(queue_sync, files, journal, rack))
    #    consumers.append(p)
    #    p.start()

    #queue_sync.join()
    #for p in producers:
    #    p.join()
    #for c in consumers:
    #    c.join()

    processes = []
    for i in range(count_prod):
        p = Process(target=procedure, args=(queue, qlock, conf, journal, filters, headers, files, rack))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
