""" Plugin manager is Checker's main module.
    Plugin Manager is using Yapsy to find and load plugins from
    a directory and loads them via PluginRunner.
"""
from yapsy.PluginManager import PluginManager

from configLoader import ConfigLoader
from core import Core
from common import PluginType

import logging
import signal
import sys
import signal
import os
import os.path
import sqlite3


def handler(signum, frame):
    if core_instance is not None:
        core_instance.finalize()
    sys.exit(0)

def configure_logger(conf):
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if conf.getProperty('logfile') is not None:
        fh = logging.FileHandler(conf.getProperty('logfile'))
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        log.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    log.addHandler(sh)

def load_plugins(cl, log, conf):
    allowed_filters = set(cl.get_allowed_filters())

    plugins = []
    filters = []
    headers = []

    filter_categories = [PluginType.FILTER, PluginType.HEADER]
    plugin_categories = [PluginType.CHECKER, PluginType.CRAWLER]

    log.info("Allowed filters")
    for x in allowed_filters:
        log.info(x)

    # load plugins
    manager = PluginManager()
    path = os.path.join(os.path.abspath("checker/"), conf.getProperty('pluginDir'))
    log.info("Plugin directory set to: "+path)
    dirList = [x[0] for x in os.walk(path)]
    for d in dirList:
        log.info("Looking for plugins in "+d)
    manager.setPluginPlaces(dirList) #pluginDir and all subdirs
    manager.collectPlugins()

    if len(manager.getAllPlugins()) > 0:
        log.info("Loaded plugins:")
        for pluginInfo in manager.getAllPlugins():
            log.info(pluginInfo.name)
            if pluginInfo.plugin_object.id in allowed_filters:
                if pluginInfo.plugin_object.category is PluginType.FILTER:
                    log.debug("Filter")
                    filters.append(pluginInfo.plugin_object)
                elif pluginInfo.plugin_object.category is PluginType.HEADER:
                    log.debug("Header")
                    headers.append(pluginInfo.plugin_object)
            elif pluginInfo.plugin_object.category in plugin_categories:
                log.debug("General plugin")
                plugins.append(pluginInfo.plugin_object)
    else:
        log.info("No plugins found")
    return plugins, headers, filters

def main():
    """ Load configuration, find plugins, run core.
    """
    global core_instance
    core_instance = None
    signal.signal(signal.SIGINT, handler)
    
    log = logging.getLogger(__name__)

    if len(sys.argv) == 2:
        # load configuration
        cl = ConfigLoader()
        cl.load(sys.argv[1])
        conf = cl.get_configuration()

        configure_logger(conf)

        #if database file exists and user wanted to clean it, remove it
        cleaned = False

        if os.path.isfile(conf.dbconf.getDbname()) and conf.getProperty('cleandb'):
            log.info("Removing database file " + conf.dbconf.getDbname() + " as configured")
            os.remove(conf.dbconf.getDbname())
            cleaned = True
        #if database file doesn't exist, create & initialize it - or warn use
        if not os.path.isfile(conf.dbconf.getDbname()):
            if not cleaned:
                log.warn("Database file " + conf.dbconf.getDbname() + " doesn't exist")
            if conf.getProperty('initdb') or cleaned:
                log.info('Initializing database file ' + conf.dbconf.getDbname())
                try:
                    with open('checker/mysql_tables.sql', 'r') as tables, open('checker/sql_values.sql', 'r') as values, sqlite3.connect(conf.dbconf.getDbname()) as conn:
                        qry0 = tables.read().split(';')
                        qry1 = values.read().split(';')
                        c = conn.cursor()
                        for q in qry0:
                            c.execute(q)
                        for q in qry1:
                            c.execute(q)
                        conn.commit()
                        c.close()
                        log.info("Successfully initialized database: " + conf.dbconf.getDbname())
                except:
                    log.error("Failed to initialize database")
                    raise
        
        plugins, headers, filters = load_plugins(cl, log, conf)

        log.info("Running checker")
        core_instance = Core(plugins, filters, headers, cl.get_configuration())
        try:
            core_instance.run()
        except Exception as e:
            log.exception("Unexpected exception")
        finally:
            core_instance.finalize()
    else:
        print("Usage: "+sys.argv[0]+" <configuration YAML file>")

if __name__ == "__main__":
    main()
