#!/usr/bin/python
# -*- coding: UTF-8 -*-

import unittest
from unittest.mock import patch
import core
from net import Network
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
        conf = Configuration(None, None, None, None, None, None, None, None, None)
        t = core.createTransaction('foobar')
        t.loadResponse(conf)
        self.assertEqual(t.type, 'text/html')
        self.assertEqual(t.file, '/tmp/foobar')
        mock_get_link.assert_called_with(t, [], conf)

    def testLoadNotTouchable(self):
        pass

    def testLoadNetworkError(self):
        pass

    def testContent(self):
        # create temp
        # put content in
        # create transaction
        # set file
        # get content and assert
        pass

    def testAcceptedTypes(self):
        #prepare conf
        #call
        #assert
        pass


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
