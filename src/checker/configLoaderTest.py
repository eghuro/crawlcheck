#!/usr/bin/python
# -*- coding: UTF-8 -*-

import unittest
from configLoader import ConfigLoader
from acceptor import Resolution

class ConfigLoaderTest(unittest.TestCase):
  def setUp(self):
    self.cl = ConfigLoader();
    self.cl.load('testConf.xml')

  def testLoadDbConf(self):
    dbconf = self.cl.getDbconf()
    self.assertEqual(dbconf.getUri(), 'localhost')
    self.assertEqual(dbconf.getUser(), 'test')
    self.assertEqual(dbconf.getPassword(), '')
    self.assertEqual(dbconf.getDbname(), 'crawlcheck')

  def testTypeAcceptor(self):
    ta = self.cl.getTypeAcceptor()
    self.assertTrue(ta.accept('moo', 'text/html'))
    self.assertFalse(ta.accept('boo', 'text/javascript'))

  def testUriAcceptor(self):
    ua = self.cl.getUriAcceptor()
    self.assertTrue(ua.accept('moo',  'http://www.mff.cuni.cz/'))

  def testLFPUriAcceptor(self):
    ua = self.cl.getUriAcceptor()
    self.assertTrue('http://olga.majling.eu/Vyuka' in ua.getValues())
    self.assertEqual(ua.pluginAcceptValue('links_finder_plugin', 'http://olga.majling.eu/Vyuka'), Resolution.no)
    self.assertFalse(ua.accept('links_finder_plugin', 'http://olga.majling.eu/Vyuka'))
    self.assertTrue(ua.accept('links_finder_plugin', 'http://olga.majling.eu'))

if __name__ == '__main__':
    unittest.main()

