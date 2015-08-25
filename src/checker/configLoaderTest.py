#!/usr/bin/python
# -*- coding: UTF-8 -*-

import unittest
from configLoader import ConfigLoader

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

if __name__ == '__main__':
    unittest.main()

