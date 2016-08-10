""" Plugin manager is Checker's main module.
    Plugin Manager is using Yapsy to find and load plugins from
    a directory and loads them via PluginRunner.
"""
from yapsy.PluginManager import PluginManager

from configLoader import ConfigLoader
from core import Core

import logging
import signal
import sys
import signal


def handler(signum, frame):
    core.finalize()
    sys.exit(0)

def main():
    """ Load configuration, find plugins, run core.
    """
    global core
    signal.signal(signal.SIGINT, handler)

    if len(sys.argv) == 2:
        # load configuration
        cl = ConfigLoader()
        cl.load(sys.argv[1])

        logging.getLogger("yapsy").addHandler(logging.StreamHandler())
        log = logging.getLogger("crawlcheck")
        log.addHandler(logging.StreamHandler())

        # load plugins
        manager = PluginManager()
        manager.setPluginPlaces(["checker/plugin"])
        manager.collectPlugins()

        plugins = []
        for pluginInfo in manager.getAllPlugins():
            log.info(pluginInfo.name)
            plugins.append(pluginInfo.plugin_object)

        if len(plugins) == 0:
            log.info("No plugins found")

        log.info("Running checker")
        core = Core(plugins)
        core.initialize(cl.get_uri_acceptor(), cl.get_type_acceptor(), cl.get_dbconf(), cl.get_entry_points(), cl.get_max_depth(), cl.get_user_agent())
        core.run()
        core.finalize()
    else:
        print("Usage: "+sys.argv[0]+" <configuration YAML file>")

if __name__ == "__main__":
    main()
