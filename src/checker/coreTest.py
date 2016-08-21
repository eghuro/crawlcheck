#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import tempfile
import unittest
from mock import patch
import core
from core import TouchException
from acceptor import Acceptor
from net import Network, StatusError, NetworkError
from configLoader import Configuration

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
        t.loadResponse(conf)
        self.assertEqual(t.type, 'text/html')
        self.assertEqual(t.file, '/tmp/foobar')
        mock_get_link.assert_called_with(t, [], conf)

    @patch('net.Network.getLink')
    def testLoadNotTouchable(self, mock):
        mock.return_value = 'text/html', '/tmp/foobar'
        ua = Acceptor(False)
        ua.setDefaultAcceptValue('foobar', False)
        try:
            t = core.createTransaction('foobar')
            conf = Configuration(None, Acceptor(True), ua, Acceptor(True), None, None, None, None, None)
            t.loadResponse(conf)
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
            t.loadResponse(conf)
        except NetworkError:#TODO: expected exception
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
        #TODO: prepare conf: uri_acceptor, uri_map, suffix acceptor, suffix uri map
        conf = Configuration(None, Acceptor(True), Acceptor(True), Acceptor(True), None, None, None, None, None)
        self.assertEqual(core.createTransaction(uri).getAcceptedTypes(conf), types)


class RackTest(unittest.TestCase):

    def testInsert(self):
        pass

    def testRun(self):
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
