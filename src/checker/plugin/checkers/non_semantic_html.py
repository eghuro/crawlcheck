from common import PluginType, getSoup
from yapsy.IPlugin import IPlugin


class NonSemanticHtml(IPlugin):

    category = PluginType.CHECKER
    id = "non_semantic_html"

    def __init__(self):
        self.__journal = None
        self.__despicable_attrs = dict()
        self.__despicable_attrs['body'] = ['alink', 'background', 'bgcolor',
                                           'link', 'text', 'vlink']
        self.__despicable_attrs['br'] = ['clear']
        self.__despicable_attrs['caption'] = ['align']
        self.__despicable_attrs['col'] = ['align', 'char', 'charoff', 
                                          'valign', 'width']
        self.__despicable_attrs['div'] = ['align']
        self.__despicable_attrs['dl'] = ['compact']
        self.__despicable_attrs['hr'] = ['align', 'noshade', 'size', 'width']
        self.__despicable_attrs['h1'] = ['align']
        self.__despicable_attrs['h2'] = ['align']
        self.__despicable_attrs['h3'] = ['align']
        self.__despicable_attrs['h4'] = ['align']
        self.__despicable_attrs['h5'] = ['align']
        self.__despicable_attrs['h6'] = ['align']
        self.__despicable_attrs['iframe'] = ['align', 'frameborder',
                                             'marginheight', 'marginwidth',
                                             'scrolling']
        self.__despicable_attrs['input'] = ['align']
        self.__despicable_attrs['img'] = ['align', 'border', 'hspace', 'vspace']
        self.__despicable_attrs['legend'] = ['align']
        self.__despicable_attrs['li'] = ['type']
        self.__despicable_attrs['menu'] = ['compact']
        self.__despicable_attrs['object'] = ['align', 'border', 'hspace',
                                             'vspace']
        self.__despicable_attrs['ol'] = ['compact', 'type']
        self.__despicable_attrs['p'] = ['align']
        self.__despicable_attrs['pre'] = ['width']
        self.__despicable_attrs['table'] = ['align', 'border', 'bgcolor',
                                            'cellpadding', 'cellspacing',
                                          'frame', 'rules', 'width']
        self.__despicable_attrs['tbody'] = ['align', 'char', 'charoff', 'valign']
        self.__despicable_attrs['thead'] = ['align', 'char', 'charoff', 'valign']
        self.__despicable_attrs['tfoot'] = ['align', 'char', 'charoff', 'valign']
        self.__despicable_attrs['th'] = ['align', 'bgcolor', 'char', 'charoff',
                                         'height', 'nowrap', 'valign', 'width']
        self.__despicable_attrs['td'] = ['align', 'bgcolor', 'char', 'charoff',
                                         'height', 'nowrap', 'valign', 'width']
        self.__despicable_attrs['tr'] = ['align', 'bgcolor', 'char', 'charoff',
                                         'valign']
        self.__despicable_attrs['ul'] = ['compact', 'type']

        self.__despicable_tags = set(['i', 'b', 'u', 'basefont', 'big', 
                                      'blink', 'center', 'font', 'marquee',
                                      's', 'spacer', 'strike', 'tt'])

    def setJournal(self, journal):
        self.__journal = journal

    def check(self, transaction):
        # https://wiki.whatwg.org/wiki/Presentational_elements_and_attributes
        soup = getSoup(transaction)
        for child in soup.descendants:
            try:
                if child.name in self.__despicable_attrs:
                    for a in self.__despicable_attrs[child.name]:
                        if a in child.attrs:
                            dsc = "Attribute %s in tag %s" % (a, child.name)
                            self.__journal.foundDefect(transaction.idno,
                                                       'nonsem',
                                                       'Non-semantic HTML tag',
                                                       dsc, 0.4)
            except AttributeError:
                pass

            if child.name in self.__despicable_tags:
                dsc = "Tag %s" % child.name
                self.__journal.foundDefect(transaction.idno, 'nonsem',
                                           "Non-semantic HTML tag",
                                           dsc, 0.4)
        return
