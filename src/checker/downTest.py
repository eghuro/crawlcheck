import unittest
from down import Scraper
from pluginDBAPI import DBAPIconfiguration

class ScraperTest(unittest.TestCase):
    def setUp(self):
        c = DBAPIconfiguration()
        c.setDbname('test.sqlite')
        self.s = Scraper(c)
    def testScrapOneRP(self):
        self.s.scrapOne('http://ulita.ms.mff.cuni.cz/mff/sylaby/rp.html')

    def testScrapOneMJ(self):
        self.s.scrapOne('http://mj.ucw.cz/vyuka/zap/')

    def testScrapOneKSP(self):
        self.s.scrapOne('http://ksp.mff.cuni.cz/about/intro.html')

    def testScrapMany(self):
        self.s.scrap(['http://ulita.ms.mff.cuni.cz/mff/sylaby/rp.html', 'http://mj.ucw.cz/vyuka/zap/', 'http://ksp.mff.cuni.cz/about/intro.html'])


if __name__ == '__main__':
    unittest.main()
