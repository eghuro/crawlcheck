

class Core:

    def __init__(self, plugins):
        self.plugins = plugins

    def initialize(self, uriAcceptor, typeAcceptor, db, entryPoints):
        self.queue = Queue(db)
        self.rack = Rack(self.plugins, uriAcceptor, typeAcceptor)
        self.db = db

        for entryPoint in entryPoints:
            self.queue.push(Transaction(entryPoint, 0))

    def run(self):
        while not self.queue.isEmpty():
            transaction = self.queue.pop()
            try:
                transaction.loadResponse(self.uriAcceptor, self.db) #DB potrebuji pro zapsani pripadnych defektu
                self.rack.run(transaction)
            except TouchException:
                raise
            except NetworkError:
                raise

    def finalize(self):
        pass


class TouchException(Exception):

    pass


class Transaction:

   def __init__(self, uri, depth, srcId = -1):
       self.uri = uri
       self.depth = depth
       self.type = None
       self.file = None
       self.srcId = srcId

   def loadResponse(self, uriAcceptor, db):
       if self.isTouchable(uriAcceptor):
           try:
               self.type, self.file = Network.getLink(self.uri, self.srcId, db)
           except NetworkError:
               raise
       else:
           raise TouchException()

   def isTouchable(self, uriAcceptor):
       return uriAcceptor.defaultAcceptValue(self.uri) != Resolution.no


class Rack:

    def __init__(self, plugins = [], uriAcceptor, typeAcceptor):
        self.plugins = plugins
        self.uriAcceptor = uriAcceptor
        self.typeAcceptor = typeAcceptor

    def run(self, transaction):
        for plugin in self.plugins:
            if self.typeAcceptor.accept(transaction, plugin) and self.uriAcceptor.accept(transaction, plugin):
                plugin.check(transaction)

    def insert(self, plugin):
        self.plugins.insert(plugin)

class Queue:

    def __init__(self, db):
        pass

    def isEmpty(self):
        pass

    def pop(self):
        pass

    def push(self, transaction):
        pass
