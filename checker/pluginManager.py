""" Plugin manager is Checker's main module.
    Plugin Manager is using Yapsy to find and load plugins from
    a directory and loads them via PluginRunner.
"""
from yapsy.PluginManager import PluginManager

try:
    from .configLoader import ConfigLoader, EntryPointRecord
    from .core import Core
    from .common import PluginType
except ImportError:
    try:
        from configLoader import ConfigLoader, EntryPointRecord
        from core import Core
        from common import PluginType
    except ModuleNotFoundError:
        from crawlcheck.checker.configLoader import ConfigLoader, EntryPointRecord
        from crawlcheck.checker.core import Core
        from crawlchheck.checker.common import PluginType

from crawlcheck.checker.database import DBAPI

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
    print("Caught signal - data remain only in redis")
    sys.exit(1)


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
    sh.setLevel(level)
    sh.setFormatter(formatter)
    log.addHandler(sh)


def __print_allowed_filters(log, allowed_filters):
    log.info("Allowed filters")
    for x in allowed_filters:
        log.info(x)


def __plugin_dirs(path, log, manager):
    log.info("Plugin directory set to: "+path)
    manager.setPluginPlaces([path])  # pluginDir and all subdirs


def __load_plugins(cl, log, conf):
    log.debug(conf.postprocess)
    allowed_filters = set(cl.get_allowed_filters())

    plugins = []
    filters = []
    headers = []
    postprocess = []

    __print_allowed_filters(log, allowed_filters)

    # load plugins
    manager = PluginManager()
    path = conf.getProperty('pluginDir')
    log.debug("Plugin dirs")
    __plugin_dirs(path, log, manager)
    log.debug("Collect plugins")
    manager.collectPlugins()
    log.debug("Collected")

    p = manager.getAllPlugins()
    if len(p) > 0:
        __do_load_plugins(p, plugins, conf, log, allowed_filters, filters, headers, postprocess)
    else:
        log.warn("No plugins found")
    log.debug("Loaded plugins: %s" % str(plugins))
    log.debug("Loaded headers: %s" % str(headers))
    log.debug("Loaded filters: %s" % str(filters))
    log.debug("Loaded postprocessors: %s" % str(postprocess))
    return plugins, headers, filters, postprocess


def list_plugins(path):
    manager = PluginManager()
    __plugin_dirs(path, logging.getLogger(__name__), manager)
    manager.collectPlugins()

    typenames = { PluginType.FILTER: 'filter', PluginType.HEADER: 'header', PluginType.CHECKER: 'checker', PluginType.CRAWLER: 'crawler' }
    for p in manager.getAllPlugins():
        if p.plugin_object.category in typenames:
            yield {'type': typenames[p.plugin_object.category], 'tag': p.plugin_object.id, 'description': p.name, 'checked': True}


def __do_load_plugins(all_plugs, plugins, conf, log, allowed_filters, filters, headers, postprocess):
    filter_categories = [PluginType.FILTER, PluginType.HEADER]
    plugin_categories = [PluginType.CHECKER, PluginType.CRAWLER]

    log.debug("Loading plugins")
    filter_lists = {PluginType.FILTER: filters,
                    PluginType.HEADER: headers}
    t = set(conf.regex_acceptor.getAllPlugins())
    log.debug(t) 
    if not conf.type_acceptor.empty:
        t.intersection(conf.type_acceptor.getAllPlugins())
    t.update(conf.postprocess)
    t.update(allowed_filters)

    for pluginInfo in all_plugs:
        if pluginInfo.plugin_object.id in t or \
           (pluginInfo.plugin_object.category in filter_categories and conf.getProperty('all_filters')) or \
           (pluginInfo.plugin_object.category == PluginType.POSTPROCESS and conf.getProperty('all_postprocess')):
            __load_plugin(pluginInfo, log, conf, filter_lists,
                          filter_categories, plugin_categories,
                          allowed_filters, plugins, postprocess)
        else:
            log.debug("Found plugin %s that no rule in config mentions - skipping" % str(pluginInfo.plugin_object.id))


def __load_plugin(pluginInfo, log, conf, filter_lists, filter_categories,
                  plugin_categories, allowed_filters, plugins, postprocess):
    log.debug("%s (%s)" % (pluginInfo.name, pluginInfo.plugin_object.id))

    if pluginInfo.plugin_object.category in filter_categories:
        __load_filter(pluginInfo, allowed_filters, conf, filter_lists)
    elif pluginInfo.plugin_object.category in plugin_categories:
        log.debug("General plugin")
        plugins.append(pluginInfo.plugin_object)
    elif pluginInfo.plugin_object.category == PluginType.POSTPROCESS:
        __load_postprocessor(pluginInfo, log, conf, postprocess)
    else:
        log.error("Unknown category for " + pluginInfo.name)


def __load_filter(pluginInfo, allowed_filters, conf, filter_lists):
    if pluginInfo.plugin_object.id in allowed_filters or conf.properties['all_filters']:
        filter_lists[pluginInfo.plugin_object.category].append(pluginInfo.plugin_object)


def __load_postprocessor(pluginInfo, log, conf, postprocess):
    log.debug("Postprocessor")
    if 'all_postprocess' in conf.properties and conf.properties['all_postprocess']:
        postprocess.append(pluginInfo.plugin_object)
    elif pluginInfo.plugin_object.id in conf.postprocess:
        postprocess.append(pluginInfo.plugin_object)
    else:
        log.debug("Not allowed in conf")


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


def __run_checker(log, plugins, headers, filters, pps, conf):
    global core_instance
    log.info("Running checker")
    core_instance = Core(plugins, filters, headers, conf, [])
    try:
        t = time.time()
        core_instance.run()
        log.debug("Execution lasted: " + str(time.time() - t))
    finally:
        gc.collect()


def validate_param(ctx, param, values):
    try:
        for value in values:
            key, val = value.split('=', 2)
            yield (key, val)
    except ValueError:
        raise click.BadParameter('parameters need to be in format key=value')


def __loadFlags(param, conf):
    for p in param:
        if p[0] == 'database':
            conf.dbconf.setDbname(p[1])
        else:
            conf.properties[p[0]] = p[1]


def __loadEntryPoints(entry, conf):
    for ep in entry:
        conf.entry_points.append(EntryPointRecord(ep))


@click.command()
@click.option('-d', '--debug', is_flag=True, help="Write detailed information into log file.")
@click.option('-p', '--param', multiple=True, callback=validate_param, help="Additional configuration parameters.")
@click.option('--entry', multiple=True, help="Additional entry points.")
@click.argument('cfile', type=click.Path(exists=True))
def main(debug, param, entry, cfile):
    """ Load configuration, find plugins, run core.
    """
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

    __loadEntryPoints(entry, conf)

    # load flags onto configuration
    __loadFlags(param, conf)
    try:
        execute(conf, cl, debug)
    except:
        pass

def execute(conf, cl, debug):
    try:
        __configure_logger(conf, debug=debug)
    except FileNotFoundError:
        return

    log = logging.getLogger(__name__)
    plugins, headers, filters, pps = __load_plugins(cl, log, conf)
    cl = None
    gc.collect()

    __run_checker(log, plugins, headers, filters, pps, conf)

if __name__ == "__main__":
    main()

