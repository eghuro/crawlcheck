from yapsy.PluginManager import PluginManager

from pluginRunner import PluginRunner
from pluginDBAPI import DBAPIconfiguration

import logging

def main():
    logging.getLogger("yapsy").addHandler(logging.StreamHandler())

    manager = PluginManager()
    manager.setPluginPlaces(["plugin"])
    manager.collectPlugins()

    plugins = []
    for pluginInfo in manager.getAllPlugins():
        print pluginInfo.name
        plugins.append(pluginInfo.plugin_object)

    runner = PluginRunner(getDbconf())
    runner.run(plugins)

def getDbconf():
    dbconf = DBAPIconfiguration()
    dbconf.setUri('localhost')
    dbconf.setUser('test')
    dbconf.setPassword('')
    dbconf.setDbname('crawlcheck')
    return dbconf

if __name__ == "__main__":
    main()
