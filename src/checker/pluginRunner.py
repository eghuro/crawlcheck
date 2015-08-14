from pluginDBAPI import DBAPI

class PluginRunner:
    def __init__(self, dbconf):
        self.dbconf = dbconf

    def runTransaction(self, plugins, info):
        for plugin in plugins:
            if plugin.handleContent(info.getContentType):
                plugin.check(info.getId(), info.getContent())

    def run(self, plugins):
        api = DBAPI(self.dbconf)
        for plugin in plugins:
            plugin.setDb(api)
        info = api.getTransaction()
        while info.getId() != -1:
            runTransaction(self, plugins, info)
            info = api.getTransaction()
