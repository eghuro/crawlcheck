from enum import Enum

class PluginType(Enum):
    
    CRAWLER = 0
    CHECKER = 1
    FILTER = 2
    HEADER = 3    

    
    
class PluginTypeError(Exception):

    def __str__(self):
        return "Unknown plugin type"
