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

if __name__ == '__main__':
    unittest.main()
