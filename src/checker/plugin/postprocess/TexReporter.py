from common import PluginType
from yapsy.IPlugin import IPlugin
from pylatex import Document, Section, Tabular, Package, NoEscape
import pylatex.utils
import urllib.parse


class TexReporter(IPlugin):
    """ Generate PDF report via LaTex.
        Generates LaTex document based on contents of the database and creates
        PDF out of it.
    """

    category = PluginType.POSTPROCESS
    id = "TexReporter"

    def __init__(self):
        self.__conf = None
        self.__db = None

    # Create a function called "chunks" with two arguments, l and n:
    @staticmethod
    def __chunks(l, n):
        # See: https://chrisalbon.com/python/break_list_into_chunks_of_equal_size.html
        # For item i in a range that is a length of l,
        for i in range(0, len(l), n):
            # Create an index range for l of n items:
            yield l[i:i+n]

    def printReport(self, out):
        """ All logic is in this method.
            Links and other defects are separated.
            Tables with relevant contents are created. Paging is implemented.

            out : name of output document, .pdf is added automatically
        """
        doc = Document()
        doc.packages.append(Package('geometry', options=['top=1in',
                                                         'bottom=1.25in',
                                                         'left=0.25in',
                                                         'right=1.25in']))

        max_on_page = 47
        with doc.create(Section('Invalid links')):
            pages = self.__chunks(self.__db.get_invalid_links(), max_on_page)
            for page in pages:
                with doc.create(Tabular('|l|l|l|')) as table:
                    table.add_hline()
                    table.add_row(('On page', 'To page', 'Cause'))
                    table.add_hline()

                    for row in page:
                        from_ = urllib.parse.unquote(row[0])
                        to_ = urllib.parse.unquote(row[1])
                        if row[2] == "badlink":
                            cause = "Status error"
                        elif row[2] == "timeout":
                            cause = "Timeout"
                        else:
                            cause = "Unknown"
                        table.add_row((from_, to_, cause))
                        table.add_hline()
                doc.append(NoEscape(r"\newpage"))

        with doc.create(Section('Other defects')):
            pages = self.__chunks(self.__db.get_other_defects(), max_on_page)
            for page in pages:
                with doc.create(Tabular('|l|l|l|l|')) as table:
                    table.add_hline()
                    table.add_row(('On page', 'Description', 'Evidence',
                                   'Severity'))
                    table.add_hline()

                    for row in page:
                        page = urllib.parse.unquote(row[0])
                        description = row[2]
                        evidence = row[1]
                        severity = row[3]
                        table.add_row((page, description, evidence, severity))
                        table.add_hline()

                doc.append(NoEscape(r"\newpage"))

        with doc.create(Section('Cookies')):
            pages = self.__chunks(self.__db.get_cookies(), max_on_page)
            for page in pages:
                with doc.create(Tabular('|l|l|l|')) as table:
                    table.add_hline()
                    table.add_row(('On page', 'Name', 'Value'))
                    table.add_hline()

                    for row in page:
                        page = urllib.parse.unquote(row[0])
                        name = row[1]
                        value = row[2]

                        table.add_row((page, name, value))
                        table.add_hline()

                doc.append(NoEscape(r"\newpage"))

        doc.generate_pdf(out)

    def setConf(self, conf):
        self.__conf = conf

    def setDb(self, db):
        self.__db = db

    def setJournal(self, journal):
        pass

    def process(self):
        outfile = self.__conf.getProperty('report-file', 'report')
        self.printReport(outfile)

if __name__ == "__main__":
    run()
