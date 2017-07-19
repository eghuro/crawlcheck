from common import PluginType, getSoup
from yapsy.IPlugin import IPlugin


class NonSemanticHtml(IPlugin):

    category = PluginType.CHECKER
    id = "non_semantic_html"

    def __init__(self):
        self.journal = None
        self.despicable_attrs = dict()
        self.despicable_attrs['body'] = ['alink', 'background', 'bgcolor',
                                         'link', 'text', 'vlink']
        self.despicable_attrs['br'] = ['clear']
        self.despicable_attrs['caption'] = ['align']
        self.despicable_attrs['col'] = ['align', 'char', 'charoff', 'valign',
                                        'width']
        self.despicable_attrs['div'] = ['align']
        self.despicable_attrs['dl'] = ['compact']
        self.despicable_attrs['hr'] = ['align', 'noshade', 'size', 'width']
        self.despicable_attrs['h1'] = ['align']
        self.despicable_attrs['h2'] = ['align']
        self.despicable_attrs['h3'] = ['align']
        self.despicable_attrs['h4'] = ['align']
        self.despicable_attrs['h5'] = ['align']
        self.despicable_attrs['h6'] = ['align']
        self.despicable_attrs['iframe'] = ['align', 'frameborder',
                                           'marginheight', 'marginwidth',
                                           'scrolling']
        self.despicable_attrs['input'] = ['align']
        self.despicable_attrs['img'] = ['align', 'border', 'hspace', 'vspace']
        self.despicable_attrs['legend'] = ['align']
        self.despicable_attrs['li'] = ['type']
        self.despicable_attrs['menu'] = ['compact']
        self.despicable_attrs['object'] = ['align', 'border', 'hspace',
                                           'vspace']
        self.despicable_attrs['ol'] = ['compact', 'type']
        self.despicable_attrs['p'] = ['align']
        self.despicable_attrs['pre'] = ['width']
        self.despicable_attrs['table'] = ['align', 'border', 'bgcolor',
                                          'cellpadding', 'cellspacing',
                                          'frame', 'rules', 'width']
        self.despicable_attrs['tbody'] = ['align', 'char', 'charoff', 'valign']
        self.despicable_attrs['thead'] = ['align', 'char', 'charoff', 'valign']
        self.despicable_attrs['tfoot'] = ['align', 'char', 'charoff', 'valign']
        self.despicable_attrs['th'] = ['align', 'bgcolor', 'char', 'charoff',
                                       'height', 'nowrap', 'valign', 'width']
        self.despicable_attrs['td'] = ['align', 'bgcolor', 'char', 'charoff',
                                       'height', 'nowrap', 'valign', 'width']
        self.despicable_attrs['tr'] = ['align', 'bgcolor', 'char', 'charoff',
                                       'valign']
        self.despicable_attrs['ul'] = ['compact', 'type']

        self.despicable_tags = set(['i', 'b', 'u', 'basefont', 'big', 'blink',
                                    'center', 'font', 'marquee', 's', 'spacer',
                                    'strike', 'tt'])

    def setJournal(self, journal):
        self.journal = journal

    def check(self, transaction):
        # https://wiki.whatwg.org/wiki/Presentational_elements_and_attributes
        soup = getSoup(transaction)
        for child in soup.descendants:
            try:
                if child.name in self.despicable_attrs:
                    for a in self.despicable_attrs[child.name]:
                        if a in child.attrs:
                            dsc = "Attribute %s in tag %s" % (a, child.name)
                            self.journal.foundDefect(transaction.idno, 'nonsem',
                                                     'Non-semantic HTML tag',
                                                     dsc, 0.4)
            except AttributeError:
                pass

            if child.name in despicable_tabs:
                dsc = "Tag %s" % child.name
                self.journal.foundDefect(transaction.idno, 'nonsem',
                                         "Non-semantic HTML tag",
                                         dsc, 0.4)
        return
