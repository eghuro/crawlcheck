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

        runner = PluginRunner(cl.getDbconf())
        runner.run(plugins)
    else:
        print "Usage: "+sys.argv[0]+" <configuration XML file>"

def getDbconf():
    dbconf = DBAPIconfiguration()
    dbconf.setUri('localhost')
    dbconf.setUser('test')
    dbconf.setPassword('')
    dbconf.setDbname('crawlcheck')
    return dbconf

if __name__ == "__main__":
    main()
