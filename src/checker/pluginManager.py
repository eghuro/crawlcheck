""" Plugin manager is Checker's main module.
    Plugin Manager is using Yapsy to find and load plugins from
    a directory and loads them via PluginRunner.
"""
from yapsy.PluginManager import PluginManager

from configLoader import ConfigLoader, EntryPointRecord
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
    """ Handle signal. """
    print("Caught signal")
    if core_instance is not None:
        core_instance.clean()
        core_instance.db.sync(final=True)
        # on kill signal just rm tmp files, sync db and leave
    sys.exit(0)


def __get_level(log, debug):
    if debug:
        log.setLevel(logging.DEBUG)
        level = logging.DEBUG
    else:
        log.setLevel(logging.INFO)
        level = logging.INFO
    return level


def __rolling(lf, fh, log):
    need_roll = os.path.isfile(lf)
    if need_roll:
        # Add timestamp
        log.debug('\n------\nLog closed on %s.\n------\n' % time.asctime())

        # Roll over on application start
        fh.doRollover()

    # Add timestamp
    log.debug('\n-------\nLog started on %s.\n-------\n' % time.asctime())


def __configure_logger(conf, debug=False):
    log = logging.getLogger()
    level = __get_level(log, debug)
    formatter = logging.Formatter('%(asctime)s - %(processName)-10s - %(name)s'
                                  ' - %(levelname)s - %(message)s',
                                  '%d %b %Y %H:%M:%S')
    if conf and conf.getProperty('logfile') is not None:
        try:
            lf = conf.getProperty('logfile')
            fh = logging.handlers.RotatingFileHandler(lf, backupCount=50)
            fh.setLevel(level)
            fh.setFormatter(formatter)
            log.addHandler(fh)
            __rolling(lf, fh, log)

        except FileNotFoundError:
            log.exception("Error creating log file")
            raise

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    log.addHandler(sh)


def __print_allowed_filters(log, allowed_filters):
    log.info("Allowed filters")
    for x in allowed_filters:
        log.info(x)


def __plugin_dirs(path, log, manager):
    log.info("Plugin directory set to: "+path)
    dirList = [x[0] for x in os.walk(path)]
    for d in dirList:
        log.info("Looking for plugins in "+d)
    manager.setPluginPlaces(dirList)  # pluginDir and all subdirs


def __load_plugins(cl, log, conf):
    allowed_filters = set(cl.get_allowed_filters())

    plugins = []
    filters = []
    headers = []
    postprocess = []

    filter_categories = [PluginType.FILTER, PluginType.HEADER]
    plugin_categories = [PluginType.CHECKER, PluginType.CRAWLER]

    __print_allowed_filters(log, allowed_filters)

    # load plugins
    manager = PluginManager()
    path = os.path.join(os.path.abspath("checker/"),
                        conf.getProperty('pluginDir'))
    __plugin_dirs(path, log, manager)
    manager.collectPlugins()

    if len(manager.getAllPlugins()) > 0:
        log.debug("Loaded plugins:")
        filter_lists = {PluginType.FILTER: filters,
                        PluginType.HEADER: headers}
        for pluginInfo in manager.getAllPlugins():
            __load_plugin(pluginInfo, log, conf, filter_lists,
                          filter_categories, plugin_categories,
                          allowed_filters, plugins, postprocess)
    else:
        log.warn("No plugins found")
    return plugins, headers, filters, postprocess


def __load_plugin(pluginInfo, log, conf, filter_lists, filter_categories,
                  plugin_categories, allowed_filters, plugins, postprocess):
    log.debug("%s (%s)" % (pluginInfo.name, pluginInfo.plugin_object.id))

    if pluginInfo.plugin_object.category in filter_categories:
        if pluginInfo.plugin_object.id in allowed_filters or conf.properties['all_filters']:
            filter_lists[pluginInfo.plugin_object.category].append(pluginInfo.plugin_object)
    elif pluginInfo.plugin_object.category in plugin_categories:
        log.debug("General plugin")
        plugins.append(pluginInfo.plugin_object)
    elif pluginInfo.plugin_object.category == PluginType.POSTPROCESS:
        log.debug("Postprocessor")
        if 'all_postprocess' in conf.properties:
            if conf.properties['all_postprocess']:
                postprocess.append(pluginInfo.plugin_object)
            else:
                log.debug("Not allowed in conf")
        elif pluginInfo.plugin_object.id in conf.postprocess:
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


def __clean_database(conf, log):
    if os.path.isfile(conf.dbconf.getDbname()) and conf.getProperty('cleandb'):
        log.info("Removing database file %s as configured" %
                 conf.dbconf.getDbname())
        os.remove(conf.dbconf.getDbname())
        return True
    return False


def __prepare_database(conf, log):
    # if database file exists and user wanted to clean it, remove it
    cleaned = __clean_database(conf, log)

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
        log.exception("Failed to initialize database")
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

def validate_param(ctx, param, values):
    try:
        for value in values:
            key, val = value.split('=', 2)
            yield (key, val)
    except ValueError:
        raise click.BadParameter('parameters need to be in format key=value')

@click.command()
@click.option('-e', '--export', is_flag=True, help="Just run postprocessing on existing database.")
@click.option('-d', '--debug', is_flag=True, help="Write detailed information into log file.")
@click.option('-p', '--param', multiple=True, callback=validate_param, help="Additional configuration parameters.")
@click.option('--entry', multiple=True, help="Additional entry points.")
@click.argument('cfile', type=click.Path(exists=True))
def main(export, debug, param, entry, cfile):
    """ Load configuration, find plugins, run core.
    """
    export_only = export

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

    for ep in entry:
        conf.entry_points.append(EntryPointRecord(ep))

    # load flags onto configuration
    for p in param:
        if p[0] == 'database':
            conf.dbconf.setDbname(p[1])
        else:
            conf.properties[p[0]] = p[1]

    try:
        __configure_logger(conf, debug=debug)
    except FileNotFoundError:
        return

    if not export_only:
        try:
            __prepare_database(conf, log)
        except:
            return

    plugins, headers, filters, pps = __load_plugins(cl, log, conf)
    cl = None
    gc.collect()

    __run_checker(log, plugins, headers, filters, pps, conf, export_only)

if __name__ == "__main__":
    main()
