from yapsy.PluginManager import PluginManager

from pluginRunner import PluginRunner
from DBAPIconfiguration import DBAPIconfiguration
from pluginDBAPI import DBAPI

import logging

def main():
    logging.getLogger("yapsy").addHandler(logging.StreamHandler())

    manager = PluginManager()
    manager.setPluginPlaces(["plugin"])
    manager.collectPlugins()

    for pluginInfo in manager.getAllPlugins():
        print pluginInfo.name
        api = DBAPI(getDbconf())

        runner = PluginRunner(api)
        runner.run(pluginInfo.plugin_object)

def getDbconf():
    dbconf = DBAPIconfiguration()
    dbconf.setUri('localhost')
    dbconf.setUser('test')
    dbconf.setPassword('')
    dbconf.setDbname('crawlcheck')
    return dbconf

if __name__ == "__main__":
    main()
