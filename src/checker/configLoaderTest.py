#!/usr/bin/python
# -*- coding: UTF-8 -*-

import unittest
from configLoader import ConfigLoader

class ConfigLoaderTest(unittest.TestCase):
  def testLoadDbConf(self):
    cl = ConfigLoader();
    cl.load('testConf.xml')
    dbconf = cl.getDbconf()
    self.assertEqual(dbconf.getUri(), 'localhost')
    self.assertEqual(dbconf.getUser(), 'test')
    self.assertEqual(dbconf.getPassword(), '')
    self.assertEqual(dbconf.getDbname(), 'crawlcheck')

if __name__ == '__main__':
    unittest.main()

