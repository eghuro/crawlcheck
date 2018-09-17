"""Database connector.
To access the database an API is provided.
Configuration is represented by DatabaseConfiguration object.
Class DBAPI represents the database API.
"""

import sys
import logging
import bleach
from enum import Enum, IntEnum
from crawlcheckio.models import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound


class DatabaseConfiguration(object):
    """ Configuration class for DBAPI.

    Configuration is set through respective setters and read through getters.

    Attributes:
        dbname (str): Sqlite3 database file to use
    """

    def __init__(self):
        """Default constructor.
        """

        self.__dbname = ""
        self.__limit = 0

    def getDbname(self):
        """ Database name getter.
        """

        return self.__dbname

    def setDbname(self, dbname):
        """Database name setter.

        Args:
            dbname: database name where data are stored
        """

        self.__dbname = dbname

    def getLimit(self):
        return self.__limit

    def setLimit(self, limit):
        self.__limit = limit


class VerificationStatus(Enum):
    requested = "REQUESTED"
    done_ok = "DONE - OK"
    done_ko = "DONE - KO"
    done_ignored = "DONE - IGNORED"


class DBAPI(object):
    """ API for access to the underlying database.
    """

    def __init__(self, conf):
        self.__conf = conf
        self.__log = logging.getLogger(__name__)
        Session = sessionmaker()
        engine = create_engine(conf.dbconf.getDbname())
        Session.configure(bind=engine)
        self.session = Session()

    def log_transaction(self, transactionId, method, uri, depth, expected, aliases):
        t = Transaction(self.__conf.getProperty("runIdentifier"), transactionId, HttpMethod[method.lower()], uri, depth, expected)
        self.session.add(t)
        for alias in aliases:
            self.session.add(Alias(transactionId, alias))
        return transactionId

    def log_transaction_data(self, transactionId, status, type, size, verificationStatus):
        transaction = self.session.query(Transaction).filter_by(id=transactionId).one()
        transaction.status = status
        transaction.type = type
        transaction.size = size
        statusMap = {VerificationStatus.done_ok: ProcessingStatus.ok,
                     VerificationStatus.done_ko: ProcessingStatus.ko,
                     VerificationStatus.done_ignored: ProcessingStatus.ignored}
        transaction.processing = statusMap[verificationStatus]
        self.session.commit()


    def log_link(self, parent_id, uri, new_id):
        """Log link from parent_id to uri with new_id."""
        link = Link(self.__conf.getProperty("runIdentifier"), parent_id, uri, new_id)
        self.session.add(link)


    def log_defect(self, transactionId, in_name, in_additional, in_evidence,
                   severity=0.5):
        """Log a defect."""
        name = bleach.clean(str(in_name), tags=[], attributes=[], styles=[])
        additional = bleach.clean(str(in_additional), tags=[], attributes=[], styles=[])
        evidence = bleach.clean(str(in_evidence), tags=[], attributes=[], styles=[])

        try:
            defect_type = self.session.query(DefectType).filter_by(name=name, additional=additional).one()
        except NoResultFound:
            self.__log.exception("Defect type not found, creating new.\nSeverity: %s\nName: %s\nAdditional: %s\nEvidence: %s" % (severity, name, additional, evidence))
            defect_type = DefectType(name, additional)
            self.session.add(defect_type)
            self.session.commit()

        self.session.add(Defect(self.__conf.getProperty("runIdentifier"),transactionId, defect_type.id, evidence, str(severity)))


    def log_cookie(self, transactionId, name, value, secure, httpOnly, path):
        """Log a cookie."""
        name = bleach.clean(str(name))
        value = bleach.clean(str(value))
        path = bleach.clean(str(path))
        self.session.add(Cookie(transactionId, name, value, secure, httpOnly, path))


    def log_header(self, transactionId, name, value):
        """ Log a header. """
        name = bleach.clean(str(name))
        value = bleach.clean(str(value))
        self.session.add(Header(transactionId, name, value))


    def log_param(self, transactionId, key, value):
        """ Log an URI parameter. """
        key = bleach.clean(key)
        value = bleach.clean(value)
        self.session.add(Param(transactionId, key, value))
