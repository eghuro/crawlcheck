from yapsy.PluginManager import PluginManager

from pluginRunner import PluginRunner

import logging

def main():
    logging.getLogger("yapsy").addHandler(logging.StreamHandler())

    manager = PluginManager()
    manager.setPluginPlaces(["plugin"])
    manager.collectPlugins()

    plugins = []
    for pluginInfo in manager.getAllPlugins():
        print pluginInfo.name
        plugins.append(pluginInfo.plugin_object)
    
    runner = PluginRunner()
    runner.run(plugins)

if __name__ == "__main__":
    main()
