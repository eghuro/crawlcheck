from checker.pluginDBAPI import DBAPI

class PluginRunner:
    def __init__(self, dbconf):
        self.dbconf = dbconf

    def runOne(self, plugin, api):
        plugin.setDb(api)
        info = api.getTransaction()
        while info.getId() != -1:
            if plugin.handleContent(info.getContentType):
                plugin.check(info.getId(), info.getContent())
            info = api.getTransaction()

    def run(self, plugins):
        api = DBAPI(self.dbconf)
        for plugin in plugins:
            self.runOne(plugin, api)
