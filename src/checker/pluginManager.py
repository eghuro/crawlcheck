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

        # load plugins
        manager = PluginManager()
        manager.setPluginPlaces( [x[0] for x in os.walk(conf.getProperty('pluginDir'))] ) #pluginDir and all subdirs
        manager.collectPlugins()

        for pluginInfo in manager.getAllPlugins():
            log.info(pluginInfo.name)
            if pluginInfo.name in allowed_filters:
                if pluginInfo.plugin_object.category is PluginType.FILTER:
                    filters.append(pluginInfo.plugin_object)
                elif pluginInfo.plugin_object.category is PluginType.HEADER:
                    headers.append(pluginInfo.plugin_object)
            else if pluginInfo.plugin_object.category in plugin_categories:
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
