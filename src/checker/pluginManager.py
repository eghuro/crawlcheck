from yapsy.PluginManager import PluginManager

from pluginRunner import PluginRunner
from pluginDBAPI import DBAPIconfiguration
from configLoader import ConfigLoader

import logging
import sys

def main():
    if len(sys.argv) == 2:
        cl = ConfigLoader()
        cl.load(sys.argv[1])

        logging.getLogger("yapsy").addHandler(logging.StreamHandler())

        manager = PluginManager()
        manager.setPluginPlaces(["plugin"])
        manager.collectPlugins()

        plugins = []
        for pluginInfo in manager.getAllPlugins():
            print pluginInfo.name
            plugins.append(pluginInfo.plugin_object)

        runner = PluginRunner(cl.getDbconf(), cl.getUriAcceptor(), cl.getTypeAcceptor())
        runner.run(plugins)
    else:
        print "Usage: "+sys.argv[0]+" <configuration XML file>"

if __name__ == "__main__":
    main()
