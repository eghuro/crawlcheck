from common import PluginType
from yapsy.IPlugin import IPlugin
import requests
import yaml
import logging


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

        #prepare YAML payload
        payload = yaml.dump(self.__db.create_report_payload())
        self.__log.info("Payload size: " + str(len(payload)))

        if payload is not None:
            #DELETE request on /data
            if self.__conf.getProperty('cleanreport'):
                url = self.__conf.getProperty('report') + '/data'
                requests.delete(url)

            #POST request on /data
            requests.post(url, data={'payload' : yaml.dump(payload)})
        else:
            self.__log.error("Reporting failed")
