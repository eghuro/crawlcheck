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


def handler(signum, frame):
    if core_instance is not None:
        core_instance.finalize()
    sys.exit(0)

def main():
    """ Load configuration, find plugins, run core.
    """
    global core_instance
    core_instance = None
    signal.signal(signal.SIGINT, handler)

    logging.getLogger("yapsy").addHandler(logging.StreamHandler())
        
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    log = logging.getLogger()
    #ch = logging.StreamHandler(sys.stdout)
    #ch.setLevel(logging.DEBUG)
    #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #ch.setFormatter(formatter)
    #log.addHandler(ch)

    if len(sys.argv) == 2:
        # load configuration
        cl = ConfigLoader()
        cl.load(sys.argv[1])
        conf = cl.get_configuration()

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

        for pluginInfo in manager.getAllPlugins():
            log.info(pluginInfo.name)
            if pluginInfo.plugin_object.id in allowed_filters:
                if pluginInfo.plugin_object.category is PluginType.FILTER:
                    log.debug("Filter: "+pluginInfo.name)
                    filters.append(pluginInfo.plugin_object)
                elif pluginInfo.plugin_object.category is PluginType.HEADER:
                    log.debug("Header: "+pluginInfo.name)
                    headers.append(pluginInfo.plugin_object)
            elif pluginInfo.plugin_object.category in plugin_categories:
                log.debug("General plugin: "+pluginInfo.name)
                plugins.append(pluginInfo.plugin_object)

        if len(plugins) == 0:
            log.info("No plugins found")

        log.info("Running checker")
        core_instance = Core(plugins, filters, headers, cl.get_configuration())
        try:
            core_instance.run()
        finally:
            core_instance.finalize()
    else:
        print("Usage: "+sys.argv[0]+" <configuration YAML file>")

if __name__ == "__main__":
    main()
