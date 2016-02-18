""" Plugin manager is Checker's main module.
    Plugin Manager is using Yapsy to find and load plugins from
    a directory and loads them via PluginRunner.
"""
from yapsy.PluginManager import PluginManager

from pluginRunner import PluginRunner
from configLoader import ConfigLoader
from down import Scraper

import logging
import sys


def main():
    """ Load configuration, find plugins, run plugin runner.
    """
    if len(sys.argv) == 2:
        # load configuration
        cl = ConfigLoader()
        cl.load(sys.argv[1])

        # download initial transactions
        s = Scraper(cl.getDbconf())
        s.scrap(cl.getEntryPoints())

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
        runner = PluginRunner(cl.getDbconf(), cl.getUriAcceptor(),
                              cl.getTypeAcceptor(), cl.getMaxDepth())

        # verify
        runner.run(plugins)
    else:
        print("Usage: "+sys.argv[0]+" <configuration XML file>")

if __name__ == "__main__":
    main()
