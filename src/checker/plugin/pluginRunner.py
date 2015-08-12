class PluginRunner:

    def __init__(self, api):
        self.api = api

    def run(self, plugin):
        info = self.api.getTransaction()
        while info.getId() != -1:
            if plugin.handleContent(info.getContentType):
                plugin.check(info.getId(), info.getContent())
            info = self.api.getTransaction()
