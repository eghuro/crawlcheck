class PluginRunner:

    def __init__(self, api):
        self.api = api

    def runOne(self, plugin):
        info = self.api.getTransaction()
        while info.getId() != -1:
            if plugin.handleContent(info.getContentType):
                plugin.check(info.getId(), info.getContent())
            info = self.api.getTransaction()

    def run(self, plugin, *plugins):
        self.runOne(plugin)
        for nextPlugin in plugins:
            self.runOne(nextPlugin)
