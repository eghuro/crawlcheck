* pluginManager - Initializes the application and loads available plugins.
* configLoader - Parses the configuration file.
* core
  - Core class with main loop.
  - Transaction class containing information about a web page with it's factory method.
  - TransactionQueue and Journal. TransactionQueue is a wrapper over Python's queue providing methods for storing links and other custom application logic. Journal is used for signaling various events - eg. defect was found.
* net - In charge of content downloading.
* acceptor - Parsed configuration rules. Acceptor objects decide if a plugin should handle a transaction.
* database - Communication with database. DBAPI object handles actual communication.
* common - For plugins there are plugin types and getSoup method which is often used. In addition some common exceptions.
* filter - Several exception objects for filters
