#!/usr/bin/python
# -*- coding: UTF-8 -*-

import unittest

from acceptor import Acceptor

class AcceptorTest(unittest.TestCase):

  def testConstructorTrue(self):
    a = Acceptor(True)
    self.assertTrue(a.accept('foo', 'bar'))

  def testConstructorFalse(self):
    a = Acceptor(False)
    self.assertFalse(a.accept('foo', 'bar'))

if __name__ == '__main__':
    unittest.main()
