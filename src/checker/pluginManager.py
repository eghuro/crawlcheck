""" Plugin manager is Checker's main module.
    Plugin Manager is using Yapsy to find and load plugins from
    a directory and loads them via PluginRunner.
"""
from yapsy.PluginManager import PluginManager

from configLoader import ConfigLoader
from core import Core
from common import PluginType

import click
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
    print("Caught signal")
    if core_instance is not None:
        core_instance.clean()
        core_instance.db.sync(final=True)
        # on kill signal just rm tmp files, sync db and leave
    sys.exit(0)


def __configure_logger(conf, debug=False):
    log = logging.getLogger()
    if debug:
        log.setLevel(logging.DEBUG)
        level = logging.DEBUG
    else:
        log.setLevel(logging.INFO)
        level = logging.INFO

    formatter = logging.Formatter('%(asctime)s - %(processName)-10s - %(name)s'
                                  ' - %(levelname)s - %(message)s')
    if conf and conf.getProperty('logfile') is not None:
        need_roll = os.path.isfile(conf.getProperty('logfile'))
        fh = logging.handlers.RotatingFileHandler(conf.getProperty('logfile'),
                                                  backupCount=50)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        log.addHandler(fh)

        if need_roll:
            # Add timestamp
            log.debug('\n------\nLog closed on %s.\n------\n' % time.asctime())

            # Roll over on application start
            fh.doRollover()

        # Add timestamp
        log.debug('\n-------\nLog started on %s.\n-------\n' % time.asctime())

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    log.addHandler(sh)


def __load_plugins(cl, log, conf):
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
    path = os.path.join(os.path.abspath("checker/"),
                        conf.getProperty('pluginDir'))
    log.info("Plugin directory set to: "+path)
    dirList = [x[0] for x in os.walk(path)]
    for d in dirList:
        log.info("Looking for plugins in "+d)
    manager.setPluginPlaces(dirList)  # pluginDir and all subdirs
    manager.collectPlugins()

    if len(manager.getAllPlugins()) > 0:
        log.info("Loaded plugins:")
        filter_lists = {PluginType.FILTER: filters,
                        PluginType.HEADER: headers}
        for pluginInfo in manager.getAllPlugins():
            __load_plugin(pluginInfo, log, conf, filter_lists,
                          filter_categories, plugin_categories,
                          allowed_filters, plugins, postprocess)
    else:
        log.info("No plugins found")
    return plugins, headers, filters, postprocess


def __load_plugin(pluginInfo, log, conf, filter_lists, filter_categories,
                  plugin_categories, allowed_filters, plugins, postprocess):
    log.info("%s (%s)" % (pluginInfo.name, pluginInfo.plugin_object.id))

    if pluginInfo.plugin_object.category in filter_categories:
        if pluginInfo.plugin_object.id in allowed_filters:
            filter_lists[pluginInfo.plugin_object.category].append(pluginInfo.plugin_object)
    elif pluginInfo.plugin_object.category in plugin_categories:
        log.debug("General plugin")
        plugins.append(pluginInfo.plugin_object)
    elif pluginInfo.plugin_object.category == PluginType.POSTPROCESS:
        log.debug("Postprocessor")
        if pluginInfo.plugin_object.id in conf.postprocess:
            postprocess.append(pluginInfo.plugin_object)
        else:
            log.debug("Not allowed in conf")
    else:
        log.error("Unknown category for " + pluginInfo.name)


def __load_configuration(cfile, log):
    log.info("Loading configuration file: " + cfile)
    cl = ConfigLoader()
    cl.load(cfile)
    conf = cl.get_configuration()
    if conf is None:
        log.error("Failed to load configuration file")
        return None, None
    else:
        return conf, cl


def __prepare_database(conf, log):
    # if database file exists and user wanted to clean it, remove it
    cleaned = False

    if os.path.isfile(conf.dbconf.getDbname()) and conf.getProperty('cleandb'):
        log.info("Removing database file %s as configured" %
                 conf.dbconf.getDbname())
        os.remove(conf.dbconf.getDbname())
        cleaned = True

    # if database file doesn't exist, create & initialize it - or warn use
    if not os.path.isfile(conf.dbconf.getDbname()):
        if conf.getProperty('initdb') or cleaned:
            __initialize_database(log, conf)
        else:
            log.error("Database file %s doesn't exist"
                      % conf.dbconf.getDbname())


def __initialize_database(log, conf):
    log.info('Initializing database file ' + conf.dbconf.getDbname())
    try:
        with open('checker/mysql_tables.sql', 'r') as tables, \
             sqlite3.connect(conf.dbconf.getDbname()) as conn:
            qry0 = tables.read().split(';')
            c = conn.cursor()
            for q in qry0:
                c.execute(q)
            conn.commit()
            c.close()
            log.info("Successfully initialized database: " +
                     conf.dbconf.getDbname())
    except:
        log.error("Failed to initialize database")
        raise


def __run_checker(log, plugins, headers, filters, pps, conf, export_only):
    global core_instance
    log.info("Running checker")
    core_instance = Core(plugins, filters, headers, pps, conf)
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


@click.command()
@click.option('-e', is_flag=True)
@click.option('-d', is_flag=True)
@click.argument('cfile', type=click.Path(exists=True))
def main(e, d, cfile):
    """ Load configuration, find plugins, run core.
    """
    export_only = e
    debug = d

    gc.enable()
    global core_instance
    core_instance = None
    signal.signal(signal.SIGINT, handler)

    log = logging.getLogger(__name__)
    log.info("Crawlcheck started")

    # load configuration
    conf, cl = __load_configuration(cfile, log)
    if conf is None:
        return

    __configure_logger(conf, debug=debug)

    if not export_only:
        __prepare_database(conf, log)

    plugins, headers, filters, pps = __load_plugins(cl, log, conf)
    cl = None
    gc.collect()

    __run_checker(log, plugins, headers, filters, pps, conf, export_only)

if __name__ == "__main__":
    main()
