from enum import Enum

class PluginType(Enum):
    
    CRAWLER = 0
    CHECKER = 1
    
    
    
class PluginTypeError(Exception):

    def __str__(self):
        return "Unknown plugin type"
