""" Plugin manager is Checker's main module.
    Plugin Manager is using Yapsy to find and load plugins from
    a directory and loads them via PluginRunner.
"""
from yapsy.PluginManager import PluginManager

from configLoader import ConfigLoader
from core import Core

import logging
import sys


def main():
    """ Load configuration, find plugins, run core.
    """
    if len(sys.argv) == 2:
        # load configuration
        cl = ConfigLoader()
        cl.load(sys.argv[1])

        logging.getLogger("yapsy").addHandler(logging.StreamHandler())

        # load plugins
        manager = PluginManager()
        manager.setPluginPlaces(["checker/plugin"])
        manager.collectPlugins()

        plugins = []
        for pluginInfo in manager.getAllPlugins():
            print(pluginInfo.name)
            plugins.append(pluginInfo.plugin_object)

        if len(plugins) == 0:
            print("No plugins found")

        core = Core(plugins)
        core.initialize(cl.getUriAcceptor(), cl.getTypeAcceptor(), cl.getDbconf(), cl.getEntryPoints())
        core.run()
        core.finalize()
    else:
        print("Usage: "+sys.argv[0]+" <configuration YAML file>")

if __name__ == "__main__":
    main()
