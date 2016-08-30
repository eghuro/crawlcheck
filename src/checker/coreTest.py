#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import tempfile
import unittest
from mock import patch
import core
from core import TouchException, Rack
from acceptor import Acceptor
from net import Network, StatusError, NetworkError
from configLoader import Configuration, ConfigLoader

class TransactionTest(unittest.TestCase):

    def testFactory(self):
        core.transactionId = 0
        t1 = core.createTransaction('foobar')
        self.assertEqual(t1.idno, 0)
        self.assertEqual(core.transactionId, 1)
        t2 = core.createTransaction('foobar')
        self.assertEqual(t2.idno, 1)
        self.assertEqual(core.transactionId, 2)

    @patch('net.Network.getLink')
    def testLoad(self, mock_get_link):
        mock_get_link.return_value = 'text/html', '/tmp/foobar'
        conf = Configuration(None, Acceptor(True), Acceptor(True), Acceptor(True), None, None, None, None, None)
        t = core.createTransaction('foobar')
        t.loadResponse(conf, None)
        self.assertEqual(t.type, 'text/html')
        self.assertEqual(t.file, '/tmp/foobar')
        mock_get_link.assert_called_with(t, [], conf, None)

    @patch('net.Network.getLink')
    def testLoadNotTouchable(self, mock):
        mock.return_value = 'text/html', '/tmp/foobar'
        ua = Acceptor(False)
        ua.setDefaultAcceptValue('foobar', False)
        sa = Acceptor(False)
        sa.setDefaultAcceptValue('raboof', False)
        try:
            t = core.createTransaction('foobar')
            conf = Configuration(None, Acceptor(True), ua, sa, None, None, None, None, None)
            t.loadResponse(conf, None)
        except TouchException:#TODO: expected exception
            return
        self.assertFalse(True)
            

    @patch('net.Network.getLink')
    def testLoadNetworkError(self, mock_get_link):
        #set mock to raise NetworkException
        mock_get_link.side_effect = StatusError(404)
        try:
            conf = Configuration(None, Acceptor(True), Acceptor(True), Acceptor(True), None, None, None, None, None)
            t = core.createTransaction('foobar')
            t.loadResponse(conf, None)
        except StatusError:#TODO: expected exception
            return
        self.assertFalse(True)
        

    def testContent(self):
        content = 'foobar content'
        name = None
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            name = tmp.name
        t = core.createTransaction('moo')
        t.file = tmp.name
        self.assertEqual(t.getContent(), content)
        os.remove(name)

    def testAcceptedTypes(self):
        uri = 'foo'
        types = ['one', 'two', 'three']

        ua = Acceptor(False)
        ua.setPluginAcceptValue('p1', 'fo', True)
        ua.setPluginAcceptValue('p3', 'f', True)
        self.assertEqual(ua.getValues(), set(['fo', 'f']))
        self.assertEqual(ua.getPositiveValues(), set(['fo', 'f']))

        sa = Acceptor(False)
        sa.setPluginAcceptValue('p2', 'oo', True)
        sa.setPluginAcceptValue('p3', 'oo', True)
        self.assertEqual(sa.getValues(), set(['oo']))
        self.assertEqual(sa.getPositiveValues(), set(['oo']))

        ta = Acceptor(False)
        ta.setPluginAcceptValue('p1', 'one', True)
        ta.setPluginAcceptValue('p1', 'five', False)
        ta.setPluginAcceptValue('p2', 'one', False)
        ta.setPluginAcceptValue('p2', 'two', True)
        ta.setPluginAcceptValue('p3', 'three', True)
        ta.setPluginAcceptValue('p3', 'two', True)
        self.assertEqual(ta.getValues(), set(['one', 'five', 'two', 'three']))
        self.assertEqual(ta.getPositiveValues(), set(['one', 'two', 'three']))

        r1 = dict() #uriPlugins
        r1['fo'] = set(['p1'])
        r1['f'] = set(['p3'])
        
        r2 = dict() #suffixUriPlugins
        r2['oo'] = set(['p2'])
        r2['oo'].add('p3')
        
        r3 = dict() #pluginTypes
        r3['p1'] = set(['one'])
        r3['p2'] = set(['two'])
        r3['p3'] = set(['three'])
        r3['p3'].add('two')

        r2 = ConfigLoader.reverse_dict_keys(r2)

        uri_map = ConfigLoader.create_uri_plugin_map(r1, r3, ua)
        self.assertEqual(uri_map.keys(), ['fo', 'f'])

        suffix_map = ConfigLoader.create_uri_plugin_map(r2, r3, sa)
        self.assertEqual(suffix_map.keys(), ['oo'])
        
        conf = Configuration(None, ta, ua, sa, None, None, None, uri_map, suffix_map)
        t = core.createTransaction(uri)
        self.assertFalse(conf.suffix_uri_map is None)
        self.assertEqual(t.getAcceptedTypes(conf), types)


class FakePlugin():

    def __init__(self, name):
        self.counter = 0
        self.id = name
        self.checked = []

    def check(self, transaction):
        #print ("Check invoked on "+self.id+" with uri "+transaction.uri)
        self.counter = self.counter + 1
        self.checked.append(transaction.idno)


class RackTest(unittest.TestCase):

    def testRun(self):

        pp = []
        ps = ["p1", "p2", "p3"]
        for s in ps:
            pp.append(FakePlugin(s))

        uri = "foo"
        rotUri = "oof"
        ctype = "bar"

        ta = Acceptor(False)
        for s in ps:
            ta.setPluginAcceptValue(s, ctype, True)

        ua = Acceptor(False)
        for s in ps:
            ua.setPluginAcceptValue(s, uri, True)

        sa = Acceptor(False)
        for s in ps:
            sa.setPluginAcceptValue(s, rotUri, True)

        t = core.createTransaction(uri)
        t.type = ctype

        r = Rack(ua, ta, sa, pp)

        for p in pp:
            self.assertTrue(r.accept(t, p))

        r.run(t)

        for p in pp:
            self.assertEqual(p.counter, 1)
            self.assertEqual(p.checked, [t.idno])

    def testAccept(self):
        pass


class QueueTest(unittest.TestCase):

    def testEmpty(self):
        pass

    def testPushEmpty(self):
        pass

    def testPushNonEmpty(self):
        pass

    def testPopEmpty(self):
        pass

    def testPopNonEmpty(self):
        pass

    def testPushPop(self):
        pass

    def testLoadStore(self):
        pass


class JournalTest(unittest.TestCase):

    def testLoadStore(self):
        pass

    def testStartChecking(self):
        pass

    def testStopChecking(self):
        pass

    def testFoundDefect(self):
        pass


class CoreTest(unittest.TestCase):

    def testInit(self):
        pass

    def testRun(self):
        pass

    def testFin(self):
        pass


if __name__ == '__main__':
    unittest.main()
