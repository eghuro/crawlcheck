#!/usr/bin/python
# -*- coding: UTF-8 -*-

import unittest

from acceptor import Acceptor
from acceptor import Resolution

class AcceptorTest(unittest.TestCase):

  def testConstructorTrue(self):
    a = Acceptor(True)
    self.assertTrue(a.accept('foo', 'bar'))

  def testConstructorFalse(self):
    a = Acceptor(False)
    self.assertFalse(a.accept('foo', 'bar'))

  def testResolutiuonYes(self):
    self.assertEqual(Acceptor.getResolution(True), Resolution.yes)

  def testResolutionNo(self):
    self.assertEqual(Acceptor.getResolution(False), Resolution.no)

  def testDefaultAcceptValueNone(self):
    a = Acceptor(False)
    self.assertEqual(a.defaultAcceptValue(''), Resolution.none)
    self.assertEqual(a.getValues(), set([]))

  def testDefaultAcceptValueTrue(self):
    a = Acceptor(False)
    a.setDefaultAcceptValue('foo', True)
    self.assertEqual(a.defaultAcceptValue('bar'), Resolution.none)
    self.assertEqual(a.defaultAcceptValue('foo'), Resolution.yes)
    self.assertEqual(a.getValues(), set(['foo']))

  def testDefaultAcceptValueFalse(self):
    a = Acceptor(False)
    a.setDefaultAcceptValue('moo', False)
    self.assertEqual(a.defaultAcceptValue('moo'), Resolution.no)
    self.assertEqual(a.defaultAcceptValue('boo'), Resolution.none)

  def testDefaultAcceptValueOverwrite(self):
    a = Acceptor(False)
    a.setDefaultAcceptValue('foo', True)
    a.setDefaultAcceptValue('foo', False)
    self.assertEqual(a.defaultAcceptValue('foo'), Resolution.no)
    self.assertEqual(a.getValues(), set(['foo']))

  def testDefaultAcceptValueMultiple(self):
    a = Acceptor(False)
    a.setDefaultAcceptValue('foo', True)
    a.setDefaultAcceptValue('bar', False)
    a.setDefaultAcceptValue('baz', False)
    self.assertEqual(a.getValues(), set(['foo', 'baz', 'bar']))
    self.assertEqual(a.defaultAcceptValue('foo'), Resolution.yes)
    self.assertTrue(a.accept('','foo'))
    self.assertEqual(a.defaultAcceptValue('bar'), Resolution.no)
    self.assertFalse(a.accept('','bar'))
    self.assertEqual(a.defaultAcceptValue('baz'), Resolution.no)
    self.assertFalse(a.accept('', 'baz'))
    self.assertEqual(a.defaultAcceptValue('moo'), Resolution.none)

  def testPluginAcceptValueDefault(self):
    a = Acceptor(False)
    self.assertEqual(a.pluginAcceptValueDefault('foo'), Resolution.none)
    a.setPluginAcceptValueDefault('foo', True)
    self.assertEqual(a.pluginAcceptValueDefault('foo'), Resolution.yes)
    self.assertTrue(a.accept('foo',''))
    a.setPluginAcceptValueDefault('bar', False)
    self.assertEqual(a.pluginAcceptValueDefault('bar'), Resolution.no)
    self.assertFalse(a.accept('bar', ''))
    self.assertEqual(a.pluginAcceptValueDefault('baz'), Resolution.none)

  def testPluginAcceptValueNoPlugin(self):
    a = Acceptor(False)
    self.assertEqual(a.pluginAcceptValue('',''), Resolution.none)

  def testPluginAcceptValueNoUri(self):
    a = Acceptor(False)
    a.setPluginAcceptValue('foo', '', False)
    self.assertEqual(a.pluginAcceptValue('foo', 'bar'), Resolution.none)
    
    a.setPluginAcceptValueDefault('foo', False)
    self.assertFalse(a.accept('foo', 'bar'))
    a.setPluginAcceptValueDefault('foo', True)
    self.assertTrue(a.accept('foo', 'bar'))

  def testPluginAcceptValueMultipleValues(self):
    a = Acceptor(False)
    a.setPluginAcceptValue('foo', 'bar', False)
    a.setPluginAcceptValue('foo', 'baz', True)
    self.assertEquals(a.pluginAcceptValue('foo','bar'), Resolution.no)
    self.assertEquals(a.pluginAcceptValue('foo', 'baz'), Resolution.yes)
    self.assertFalse(a.accept('foo', 'bar'))
    self.assertTrue(a.accept('foo', 'baz'))
    self.assertEquals(a.getValues(), set(['bar', 'baz']))

  def testPluginAcceptValueMultiplePlugins(self):
    a = Acceptor(False)
    a.setPluginAcceptValue('foo', 'bar', False)
    a.setPluginAcceptValue('foo', 'baz', True)
    a.setPluginAcceptValue('moo', 'bar', True)
    a.setPluginAcceptValue('moo', 'baz', False)
    self.assertEquals(a.pluginAcceptValue('foo', 'bar'), Resolution.no)
    self.assertEquals(a.pluginAcceptValue('foo', 'baz'), Resolution.yes)
    self.assertEquals(a.pluginAcceptValue('moo', 'bar'), Resolution.yes)
    self.assertEquals(a.pluginAcceptValue('moo', 'baz'), Resolution.no)
    self.assertFalse(a.accept('foo', 'bar'))
    self.assertFalse(a.accept('moo', 'baz'))
    self.assertTrue(a.accept('foo', 'baz'))
    self.assertTrue(a.accept('moo', 'bar'))
    self.assertEquals(a.getValues(), set(['bar', 'baz']))

if __name__ == '__main__':
    unittest.main()
