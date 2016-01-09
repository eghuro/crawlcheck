import unittest
from bs4 import BeautifulSoup
import css_scraper

class CssScraperTest(unittest.TestCase):
    def test_id(self):
        scrap = CssScraper()
        self.assertEquals("css_scraper", scrap.getId())
    
    def test_internal_detection(self):
        sample = "<html><head><<title>foobar</title><style>TODO</style></head><body><p>Lorem ipsum.</p></body></html>"
        scrap = CssScraper()
        soup = BeautifulSoup(sample, 'html.parser')
        self.assertEquals(scrap.scan_internal(soup), "TODO")

    def test_internal_none(self):
        sample = "<html><head><title>foobar</title></head><body><p>Lorem ipsum.</p></body></html>"
        scrap = CssScraper()
        soup = BeautifulSoup(sample, 'html.parser')
        self.assertEquals(scrap.scan_internal(soup), None)

    def test_inline_detection_one(self):
        sample = '<html><head><title>foobar</title><style>TODO</style></head><body><p style="BOOM">Lorem ipsum.</p></body></head>'
        scrap = CssScraper()
        soup = BeautifulSoup(sample, 'html.parser')
        self.assertEquals(scrap.scan_internal(soup), ['BOOM'])

    def test_inline_detection_many(self):
        sample = '<html><body><p style="TODO>Lorem.</p><span style="BOOM"><img src="http://foobar.org/foo.bar" /></span></body></html>'
        scrap = CssScraper()
        soup = BeautifulSoup(sample, 'html.parser')
        self.assertEquals(scrap.scan_inline(soup), ['TODO', 'BOOM'])

    def test_inline_detection_none(self):
        sample = '<html><body><p>Lorem ipsum.</p></body></html>'
        scrap = CssScraper()
        soup = BeautifulSoup(sample, 'html.parser')
        self.assertEquals(scrap.scan_inline(soup), [])
