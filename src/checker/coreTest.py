#!/usr/bin/python
# -*- coding: UTF-8 -*-

import unittest

class TransactionTest(unittest.TestCase):

    def testLoad(self):
        pass

    def testContent(self):
        pass

    def testTouch(self):
        pass

    def testPrefix(self):
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
