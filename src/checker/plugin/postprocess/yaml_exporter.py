from common import PluginType
from yapsy.IPlugin import IPlugin
from ruamel import yaml
import logging


class YamlExporter(IPlugin):

    category = PluginType.POSTPROCESS
    id = "yaml_exporter"

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
        if self.__conf.getProperty('yaml-out-file') is not None:
            with open(self.__conf.getProperty('yaml-out-file'), 'w',
                      encoding="utf-8") as out:
                out.write(yaml.dump(self.__db.create_report_payload(
                                    self.__conf.getProperty("cores", 4))))
        else:
            self.__log.info("Reporting not required")
