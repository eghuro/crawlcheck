#!/usr/bin/python
# -*- coding: UTF-8 -*-

import unittest
from configLoader import ConfigLoader
from acceptor import Resolution


class ConfigLoaderTest(unittest.TestCase):
    def setUp(self):
        self.cl = ConfigLoader()
        self.cl.load('testConf.yml')

    def testLoadDbConf(self):
        dbconf = self.cl.getDbconf()
        self.assertEqual(dbconf.getDbname(), 'test.sqlite')

    def testTypeAcceptor(self):
        ta = self.cl.getTypeAcceptor()
        self.assertFalse(ta.accept('boo', 'text/javascript'))

    def testUriAcceptor(self):
        ua = self.cl.getUriAcceptor()
        # self.assertTrue(ua.accept('moo',  'http://www.mff.cuni.cz/'))

    def testLFPUriAcceptor(self):
        ua = self.cl.getUriAcceptor()
        for val in ua.getValues():
            print(val)
        self.assertTrue('http://mj.ucw.cz/vyuka/' in ua.getValues())

class ConfigLoaderTestInvalid(unittest.TestCase):
    def setUp(self):
        self.cl = ConfigLoader()

    def testLoad(self):
        self.cl.load('invalidTestConf0.yml')
        self.assertAllNone()

    def testConfigurationVersion(self):
        self.cl.load('invalidTestConf1.yml')
        self.assertAllNone()

    def maxDepthEntryPoints(self, config, depth, entry):
        self.cl.load(config)
        self.assertEqual(depth, self.cl.getMaxDepth())
        self.assertEqual(entry, self.cl.getEntryPoints())

    def testMaxDepthEmptyEntryPoints(self):
        self.maxDepthEntryPoints('testConf0.yml', 5, [])

    def testNegativeMaxDepthNoEntryPoints(self):
        self.maxDepthEntryPoints('testConf1.yml', 0, [])

    def assertNone(self, obj):
        self.assertEqual(obj, None)

    def assertAllNone(self):
        self.assertNone(self.cl.getDbconf())
        self.assertNone(self.cl.getTypeAcceptor())
        self.assertNone(self.cl.getUriAcceptor())
        self.assertNone(self.cl.getEntryPoints())
        self.assertNone(self.cl.getMaxDepth())
if __name__ == '__main__':
    unittest.main()
