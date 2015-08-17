from pluginDBAPI import DBAPI

class PluginRunner:
    def __init__(self, dbconf):
        self.dbconf = dbconf
        self.pluginsById = {}

    def runTransaction(self, plugins, info):
        for plugin in plugins:
            if accept(self, plugin.getId(), info):
                plugin.check(info.getId(), info.getContent())

    def run(self, plugins):
        api = DBAPI(self.dbconf)
        for plugin in plugins:
            plugin.setDb(api)
            self.pluginsById[plugin.getId()] = plugin
        info = api.getTransaction()
        while info.getId() != -1:
            runTransaction(self, plugins, info)
            info = api.getTransaction()

    def accept(self, pluginId, transaction):
        return self.pluginsById[pluginId].handleContent(transaction)
