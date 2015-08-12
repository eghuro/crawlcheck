from pluginDBAPI import DBAPI
from DBAPIconfiguration import DBAPIconfiguration

class PluginRunner:

    def runOne(self, plugin, api):
        plugin.setDb(api)
        info = api.getTransaction()
        while info.getId() != -1:
            if plugin.handleContent(info.getContentType):
                plugin.check(info.getId(), info.getContent())
            info = api.getTransaction()

    def run(self, plugins):
        api = DBAPI(self.getDbconf())
        for plugin in plugins:
            self.runOne(plugin, api)

    def getDbconf(self):
        dbconf = DBAPIconfiguration()
        dbconf.setUri('localhost')
        dbconf.setUser('test')
        dbconf.setPassword('')
        dbconf.setDbname('crawlcheck')
        return dbconf
