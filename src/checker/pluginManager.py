""" Plugin manager is Checker's main module.
    Plugin Manager is using Yapsy to find and load plugins from
    a directory and loads them via PluginRunner.
"""
from yapsy.PluginManager import PluginManager

from configLoader import ConfigLoader
from core import Core

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

    if len(sys.argv) == 2:
        # load configuration
        cl = ConfigLoader()
        cl.load(sys.argv[1])

        logging.getLogger("yapsy").addHandler(logging.StreamHandler())
        
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        log = logging.getLogger()
        #ch = logging.StreamHandler(sys.stdout)
        #ch.setLevel(logging.DEBUG)
        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        #ch.setFormatter(formatter)
        #log.addHandler(ch)

        # load plugins
        manager = PluginManager()
        manager.setPluginPlaces(["checker/plugin"])
        manager.collectPlugins()

        plugins = []
        for pluginInfo in manager.getAllPlugins():
            log.info(pluginInfo.name)
            plugins.append(pluginInfo.plugin_object)

        if len(plugins) == 0:
            log.info("No plugins found")

        log.info("Running checker")
        core_instance = Core(plugins, cl.get_configuration())
        try:
            core_instance.run()
        finally:
            core_instance.finalize()
    else:
        print("Usage: "+sys.argv[0]+" <configuration YAML file>")

if __name__ == "__main__":
    main()
