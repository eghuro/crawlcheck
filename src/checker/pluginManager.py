""" Plugin manager is Checker's main module.
    Plugin Manager is using Yapsy to find and load plugins from
    a directory and loads them via PluginRunner.
"""
from yapsy.PluginManager import PluginManager

from configLoader import ConfigLoader
from core import Core
from common import PluginType

import logging
import logging.handlers
import signal
import sys
import signal
import os
import os.path
import sqlite3
import time
import gc


def handler(signum, frame):
    if core_instance is not None:
        core_instance.finalize()
    sys.exit(0)

def configure_logger(conf, debug=False):
    log = logging.getLogger()
    if debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(processName)-10s - %(name)s - %(levelname)s - %(message)s')
    if conf:
        if conf.getProperty('logfile') is not None:
            need_roll = os.path.isfile(conf.getProperty('logfile'))
            fh = logging.handlers.RotatingFileHandler(conf.getProperty('logfile'), backupCount=50)
            if debug:
                fh.setLevel(logging.DEBUG)
            else:
                fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            log.addHandler(fh)

            if need_roll:
                # Add timestamp
                log.debug('\n---------\nLog closed on %s.\n---------\n' % time.asctime())

                # Roll over on application start
                fh.doRollover()
            # Add timestamp
            log.debug('\n---------\nLog started on %s.\n---------\n' % time.asctime())


    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    log.addHandler(sh)

def load_plugins(cl, log, conf):
    allowed_filters = set(cl.get_allowed_filters())

    plugins = []
    filters = []
    headers = []
    postprocess = []

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
            if pluginInfo.plugin_object.category is PluginType.FILTER or pluginInfo.plugin_object.category is PluginType.HEADER:
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
            elif pluginInfo.plugin_object.category is PluginType.POSTPROCESS:
                log.debug("Postprocessor")
                if pluginInfo.plugin_object.id in conf.postprocess: 
                    postprocess.append(pluginInfo.plugin_object)
                else:
                    log.debug("Not allowed in conf")
            else:
                log.error("Unknown category for " + pluginInfo.name)
    else:
        log.info("No plugins found")
    return plugins, headers, filters, postprocess

def main():
    """ Load configuration, find plugins, run core.
    """
    gc.enable()
    global core_instance
    core_instance = None
    signal.signal(signal.SIGINT, handler)
    
    log = logging.getLogger(__name__)
    log.info("Crawlcheck started")

    if len(sys.argv) >= 2:
        # load configuration
        if not os.path.isfile(sys.argv[1]):
            log.error("Invalid configuration file: " + sys.argv[1])
            return

        log.info("Loading configuration file: " + sys.argv[1])
        cl = ConfigLoader()
        cl.load(sys.argv[1])
        conf = cl.get_configuration()
        if conf is None:
            log.error("Failed to load configuration file")
            return

        export_only = False
        debug = False
        if len(sys.argv) >= 3:
            if sys.argv[2] == '-d':
                debug = True
                if len(sys.argv) == 4:
                    if sys.argv[3] == '-e':
                        export_only = True
            elif sys.argv[2] == '-e': #TODO: properly
                export_only = True
                if len(sys.argv) == 4:
                    if sys.argv[3] == '-d':
                        debug=True
            else:
                log.error("Input error: " + sys.argv[2])
                return
        print("Debug: " + str(debug))
        print("Export only: " + str(export_only))
        configure_logger(conf, debug=debug)

        #if database file exists and user wanted to clean it, remove it
        cleaned = False

        if os.path.isfile(conf.dbconf.getDbname()) and conf.getProperty('cleandb') and not export_only:
            log.info("Removing database file " + conf.dbconf.getDbname() + " as configured")
            os.remove(conf.dbconf.getDbname())
            cleaned = True
        #if database file doesn't exist, create & initialize it - or warn use
        if not os.path.isfile(conf.dbconf.getDbname()) and not export_only:
            if not cleaned:
                log.warn("Database file " + conf.dbconf.getDbname() + " doesn't exist")
            if conf.getProperty('initdb') or cleaned:
                log.info('Initializing database file ' + conf.dbconf.getDbname())
                try:
                    with open('checker/mysql_tables.sql', 'r') as tables, sqlite3.connect(conf.dbconf.getDbname()) as conn:
                        qry0 = tables.read().split(';')
                        c = conn.cursor()
                        for q in qry0:
                            c.execute(q)
                        conn.commit()
                        c.close()
                        log.info("Successfully initialized database: " + conf.dbconf.getDbname())
                except:
                    log.error("Failed to initialize database")
                    raise

        plugins, headers, filters, pps = load_plugins(cl, log, conf)

        log.info("Running checker")
        core_instance = Core(plugins, filters, headers, pps, conf)
        cl = None
        gc.collect()
        if not export_only:
            try:
                t = time.time()
                core_instance.run()
                log.debug("Execution lasted: " + str(time.time() - t))
            except Exception as e:
                log.exception("Unexpected exception")
            finally:
                core_instance.finalize()
                log.info("The End.")
        else:
           core_instance.postprocess() 
    else:
        print("Usage: "+sys.argv[0]+" <configuration YAML file>")

if __name__ == "__main__":
    main()
