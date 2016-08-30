#!/usr/bin/python
# -*- coding: UTF-8 -*-

import unittest

from acceptor import Acceptor
from acceptor import Resolution
import core


class AcceptorTest(unittest.TestCase):

    def testConstructorTrue(self):
        a = Acceptor(True)
        #t = core.createTransaction('foo', 0)
        self.assertTrue(a.accept(unicode('foo'), 'bar'))

    def testConstructorFalse(self):
        a = Acceptor()
        #t = core.createTransaction('foo', 0)
        self.assertFalse(a.accept(unicode('foo'), 'bar'))

    def testResolutiuonYes(self):
        self.assertEqual(Acceptor.getResolution(True), Resolution.yes)

    def testResolutionNo(self):
        self.assertEqual(Acceptor.getResolution(False), Resolution.no)

    def testResolveFromDefaultYes(self):
        defaults = dict()
        defaults['value'] = True
        self.assertEqual(Acceptor().resolveFromDefault('value', defaults), Resolution.yes)

    def testResolveFromDefaultNo(self):
        defaults = dict()
        defaults['value'] = False
        self.assertEqual(Acceptor().resolveFromDefault('value', defaults), Resolution.no)

    def testResolveFromDefaultNone(self):
        defaults = dict()
        defaults['value'] = True
        self.assertEqual(Acceptor().resolveFromDefault('eulav', defaults), Resolution.none)

    def testResolveFromDefaultDefaultsEmpty(self):
        self.assertEqual(Acceptor().resolveFromDefault('value', dict()), Resolution.none)

    def testResolveFromDefaultValueNone(self):
        self.assertEqual(Acceptor().resolveFromDefault(None, dict()), Resolution.none)

    def testResolveDefaultAcceptValueDefaultTrue(self):
        self.assertTrue(self.__getPreloadedAcceptor().resolveDefaultAcceptValue('foo.baz.net'))

    def testResolveDefaultAcceptValueDefaultFalse(self):
        self.assertFalse(self.__getPreloadedAcceptor(False).resolveDefaultAcceptValue('moo.bar.org'))

    def testResolveDefaultAcceptValueFromDefaultYes(self):
        self.assertTrue(self.__getPreloadedAcceptor().resolveDefaultAcceptValue('foo.bar.org'))

    def testResolveDefaultAcceptValueFromDefaultNo(self):
        self.assertFalse(self.__getPreloadedAcceptor().resolveDefaultAcceptValue('moo.baz.net'))

    def testPreloadedAcceptor(self):
        a = self.__getPreloadedAcceptor()

        self.assertTrue('foo.bar.org' in a.getValues())
        self.assertTrue('moo.baz.net' in a.getValues())
        self.assertTrue('foo.bar.org' in a.getPositiveValues())
        self.assertFalse('moo.baz.net' in a.getPositiveValues())

    def __getPreloadedAcceptor(self, default=True):
        a = Acceptor(default)
        a.setDefaultAcceptValue('foo.bar.org', True)
        a.setDefaultAcceptValue('moo.baz.net', False)
        return a

    def testPreloadedAcceptorPluginAcceptValueMultiple(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple()

        self.assertTrue('foo.bar.org' in a.getValues())
        self.assertTrue('moo.baz.net' in a.getValues())

        self.assertTrue('foo.bar.org' in a.getPositiveValues())
        self.assertFalse('moo.baz.net' in a.getPositiveValues())

        self.assertTrue('goof.org' in a.getValues())
        self.assertTrue('meow.net' in a.getValues())
        self.assertTrue('foog.com' in a.getValues())
        self.assertTrue('woem.edu' in a.getValues())

        self.assertTrue('goof.org' in a.getPositiveValues())
        self.assertTrue('meow.net' in a.getPositiveValues())
        self.assertTrue('foog.com' in a.getPositiveValues())
        self.assertFalse('woem.edu' in a.getPositiveValues())

    def __getPreloadedAcceptor_pluginAcceptValue_multiple(self, default=True):
        a = self.__getPreloadedAcceptor(default)

        a.setPluginAcceptValue('plug', 'goof.org', True)
        a.setPluginAcceptValue('plug', 'meow.net', False)
        a.setPluginAcceptValue('glup', 'goof.org', False)
        a.setPluginAcceptValue('glup', 'meow.net', True)
        a.setPluginAcceptValue('plug', 'foog.com', True)
        a.setPluginAcceptValue('plug', 'woem.edu', False)
        return a

    def testPluginAcceptValueYesOneValue(self):
        a = Acceptor()
        a.setPluginAcceptValue('plug', 'goof.org', True)

        self.assertTrue('goof.org' in a.getValues())
        self.assertEquals(a.pluginAcceptValue('plug', 'goof.org'), Resolution.yes)

    def testPluginAcceptValueYesMultipleValues(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)

        self.assertEquals(a.pluginAcceptValue('plug', 'goof.org'), Resolution.yes)
        self.assertEquals(a.pluginAcceptValue('glup', 'meow.net'), Resolution.yes)

    def testPluginAcceptValueNoOneValue(self):
        a = Acceptor()
        a.setPluginAcceptValue('plug', 'meow.net', False)

        self.assertTrue('meow.net' in a.getValues())
        self.assertEquals(a.pluginAcceptValue('plug', 'meow.net'), Resolution.no)

    def testPluginAcceptValueNoMultipleValues(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)

        self.assertEquals(a.pluginAcceptValue('plug', 'meow.net'), Resolution.no)
        self.assertEquals(a.pluginAcceptValue('glup', 'goof.org'), Resolution.no)

    def testPluginAcceptValueNoUri(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)

        self.assertEquals(a.pluginAcceptValue('plug', 'foo.baz.org'), Resolution.none)

    def testPluginAcceptValueNoPlugin(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)

        self.assertEquals(a.pluginAcceptValue('plugin', 'goof.org'), Resolution.none)

    def testResolvePluginAcceptValueYes(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
        self.assertTrue(a.resolvePluginAcceptValue('plug', 'goof.org'))

    def testResolvePluginAcceptValueNo(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
        self.assertFalse(a.resolvePluginAcceptValue('plug', 'meow.net'))

    #def testResolvePluginAcceptValueDefaultYes(self):
    #    a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
    #    self.assertTrue(a.resolvePluginAcceptValue('plug', 'foo.bar.org'))

    def testResolvePluginAcceptValueDefaultNo(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
        self.assertFalse(a.resolvePluginAcceptValue('plug', 'moo.baz.net'))

    def testMaxPrefixExactValueTrue(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
        self.assertEquals(a.getMaxPrefix(unicode('foo.bar.org')), 'foo.bar.org')
        self.assertEquals(a.getMaxPrefix(unicode('goof.org')), 'goof.org')
        self.assertEquals(a.getMaxPrefix(unicode('foog.com')), 'foog.com')

    def testMaxPrefixExactValueFalse(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
        self.assertEquals(a.getMaxPrefix(unicode('moo.baz.net')), 'moo.baz.net')
        self.assertEquals(a.getMaxPrefix(unicode('meow.net')), 'meow.net')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu')), 'woem.edu')

    def testMaxPrefixOneValue(self):
        a = Acceptor()
        a.setPluginAcceptValue('plug', 'foo.bar.org', True)
        self.assertEquals(a.getValues(), set(['foo.bar.org']))

        self.assertEquals(a.getMaxPrefix(unicode('woem.edu')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/about.html')), 'woem.edu/about.html')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/about/index.html')), 'woem.edu/about/index.html')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/contact.php')), 'woem.edu/contact.php')
        self.assertEquals(a.getMaxPrefix(unicode('meow.net')), 'meow.net')
        self.assertEquals(a.getMaxPrefix(unicode('meow.net/contact.php')), 'meow.net/contact.php')

    def testMaxPrefixOneCorrectValue(self):
        a = Acceptor()
        a.setPluginAcceptValue('plug', 'woem.edu', True)
        self.assertEquals(a.getValues(), set(['woem.edu']))

        self.assertEquals(a.getMaxPrefix(unicode('woem.edu')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/about.html')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/about/index.html')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/contact.php')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('meow.net')), 'meow.net')
        self.assertEquals(a.getMaxPrefix(unicode('meow.net/contact.php')), 'meow.net/contact.php')

    def testMaxPrefixSelectOfOne(self):
        a = Acceptor()
        a.setPluginAcceptValue('plug', 'woem.edu', True)
        a.setPluginAcceptValue('glup', 'foo.bar.org', False)
        a.setPluginAcceptValue('plug', 'foog.com', True)
        a.setPluginAcceptValue('goof', 'moo.baz.net', False)
        
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/about.html')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/about/index.html')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/contact.php')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('meow.net')), 'meow.net')
        self.assertEquals(a.getMaxPrefix(unicode('meow.net/contact.php')), 'meow.net/contact.php')

    def testMaxPrefixSelectOfMany(self):
        a = Acceptor()
        a.setPluginAcceptValue('plug', 'woem.edu', True)
        a.setPluginAcceptValue('plug', 'woem.edu/about', False)
        a.setPluginAcceptValue('glup', 'foo.bar.org', False)
        a.setPluginAcceptValue('plug', 'foog.com', True)
        a.setPluginAcceptValue('goof', 'moo.baz.net', False)
        
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/about.html')), 'woem.edu/about')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/about/index.html')), 'woem.edu/about')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/contact.php')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('meow.net')), 'meow.net')
        self.assertEquals(a.getMaxPrefix(unicode('meow.net/contact.php')), 'meow.net/contact.php')

    def testMaxPrefixValueEmpty(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
        self.assertEquals(a.getMaxPrefix(unicode('')), '')

    #def testMaxPrefixValueNone(self):
    #    a = Acceptor()
    #    self.assertEquals(a.getMaxPrefix(unicode(None)), None)

    #def testMaxPrefixValueNonString(self):
    #    a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
    #    self.assertEquals(a.getMaxPrefix(unicode(123456)), 123456)
    #    self.assertEquals(a.getMaxPrefix(unicode(-13.56)), -13.56)
    #    self.assertEquals(a.getMaxPrefix(unicode(a)), a)

    def testMaxPrefixNoUris(self):
        a = Acceptor()
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu')), 'woem.edu')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/about.html')), 'woem.edu/about.html')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/about/index.html')), 'woem.edu/about/index.html')
        self.assertEquals(a.getMaxPrefix(unicode('woem.edu/contact.php')), 'woem.edu/contact.php')
        self.assertEquals(a.getMaxPrefix(unicode('meow.net')), 'meow.net')
        self.assertEquals(a.getMaxPrefix(unicode('meow.net/contact.php')), 'meow.net/contact.php')

    def testAcceptTrue(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
        t = unicode('goof.org/about/offices/')
        self.assertTrue(a.accept(t, 'plug'))
        t = unicode('meow.net')
        self.assertTrue(a.accept(t, 'glup'))
        t = unicode('foo.bar.org/foobar')
        #self.assertTrue(a.accept(t, ''))
        #self.assertTrue(a.accept(t, None))
        #self.assertTrue(a.accept(t, 12345))
        #self.assertTrue(a.accept(t, -12.35))
        t = unicode('foog.com/')
        self.assertTrue(a.accept(t, 'plug'))

    def testAcceptFalse(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
        t = unicode('meow.net/about/offices/')
        self.assertFalse(a.accept(t, 'plug'))
        t = unicode('goof.org')
        self.assertFalse(a.accept(t, 'glup'))
        t = unicode('woem.edu/about.html')
        self.assertFalse(a.accept(t, 'plug'))
        t = unicode('moo.baz.net/glory')
        self.assertFalse(a.accept(t, ''))
        self.assertFalse(a.accept(t, None))
        self.assertFalse(a.accept(t, 12345))
        self.assertFalse(a.accept(t, -12.35))

    def testMightAccept(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
        lst = [unicode('goof.org/about/offices/'), unicode('meow.net'), unicode('foo.bar.org/foobar'), unicode('foog.com/')]
        for it in lst:
            self.assertTrue(a.mightAccept(it))
        lst = [unicode('moo.baz.net/glory'), unicode('woem.edu/about.html')]
        for it in lst:
            self.assertFalse(a.mightAccept(it))

    def testReverseValues(self):
        a = self.__getPreloadedAcceptor_pluginAcceptValue_multiple(False)
        lst = a.getValues()
        revList = []
        for it in lst:
            revList.append(it[::-1])
        a.reverseValues()
        self.assertEquals(a.getValues(), set(revList))

    def testReverseValuesNoUris(self):
        a = Acceptor(False)
        a.reverseValues()
        self.assertEquals(a.getValues(), set())

if __name__ == '__main__':
    unittest.main()
