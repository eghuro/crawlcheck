from common import PluginType
from yapsy.IPlugin import IPlugin
import requests
from requests.exceptions import ConnectionError
import yaml
import logging
import gc


class ReportExporter(IPlugin):

    category = PluginType.POSTPROCESS
    id = "report_exporter"

    def __init__(self):
        self.__log = logging.getLogger(__name__)

    def setConf(self, conf):
        self.__conf = conf

    def setDb(self, db):
        self.__db = db

    def setJournal(self, journal):
        pass

    def process(self):
        self.__log.info("Preparing report")
        if self.__conf.getProperty('report') is not None:
            url = self.__conf.getProperty('report') + '/data'
            try:
                if requests.head(url).status_code != 200:
                    self.__log.warn("Is report REST API running?")
            except ConnectionError:
                self.__log.warn("Is report REST API running?")

            #prepare YAML payload
            payload = yaml.dump(self.__db.create_report_payload())
            self.__log.info("Payload size: " + str(len(payload)))
            self.__log.debug(payload)

            if payload is not None:
                gc.collect()
                #DELETE request on /data
                if self.__conf.getProperty('cleanreport'):
                    try:
                        r = requests.delete(url)
                        if r.status_code != 200:
                            self.__log.error("Delete failed")
                    except ConnectionError:
                        self.__log.error("Connection error while deleting old report")
                #POST request on /data
                try:
                    r = requests.post(url, data={'payload' : payload})
                    if r.status_code != 200:
                        self.__log.error("Upload failed")
                except ConnectionError:
                    self.__log.error("Connection error while uploading report")
        else:
            self.__log.info("Reporting not required")
