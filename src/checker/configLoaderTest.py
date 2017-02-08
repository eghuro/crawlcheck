#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import unittest
from configLoader import ConfigLoader
from acceptor import Resolution
import core


class ConfigLoaderTest(unittest.TestCase):
    def setUp(self):
        self.cl = ConfigLoader()
        self.cl.load('testConf.yml')

    def testLoadDbConf(self):
        dbconf = self.cl.get_configuration().dbconf
        self.assertEqual(dbconf.getDbname(), 'crawlcheck')

    def testTypeAcceptor(self):
        ta = self.cl.get_configuration().type_acceptor
        t = core.createTransaction('boo')
        self.assertEqual(type(t.uri), str)
        self.assertFalse(ta.accept(t.uri, 'text/javascript'))

    def testUriAcceptor(self):
        ua = self.cl.get_configuration().uri_acceptor
        # self.assertTrue(ua.accept('moo',  'http://www.mff.cuni.cz/'))

    def testLFPUriAcceptor(self):
        ua = self.cl.get_configuration().uri_acceptor
        for val in ua.getValues():
            print(val)
        self.assertTrue('http://mj.ucw.cz/vyuka/' in ua.getValues())

class ConfigLoaderTestInvalid(unittest.TestCase):
    def setUp(self):
        self.cl = ConfigLoader()

    def testLoad(self):
        self.cl.load('invalidTestConf0.yml')
        self.assertNone(self.cl.get_configuration())

    def testConfigurationVersion(self):
        self.cl.load('invalidTestConf1.yml')
        self.assertNone(self.cl.get_configuration())

    def maxDepthEntryPoints(self, config, depth, entry):
        self.cl.load(config)
        self.assertEqual(depth, self.cl.get_configuration().properties["maxDepth"])
        self.assertEqual(entry, self.cl.get_configuration().entry_points)

    def testMaxDepthEmptyEntryPoints(self):
        self.maxDepthEntryPoints('testConf0.yml', 5, [])

    #def testNegativeMaxDepthNoEntryPoints(self):
    #    self.maxDepthEntryPoints('testConf1.yml', 0, [])

    def testUrlNoPlugins(self):
        self.cl.load('testConf2.yml')
        acceptor = self.cl.get_configuration().uri_acceptor
        accept = acceptor.accept(core.createTransaction('http://mj.ucw.cz/vyuka/rp/').uri, 'foobar')
        self.assertFalse(accept)

    def testPluginsNoContentType(self):
        self.cl.load('invalidTestConf2.yml')
        self.assertNone(self.cl.get_configuration())

    def assertNone(self, obj):
        self.assertEqual(obj, None)

if __name__ == '__main__':
    unittest.main()
