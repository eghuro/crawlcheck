import sqlite3 as mdb
from pylatex import Document, Section, Tabular, Package
import pylatex.utils
import sys
import urllib

class TexReporter(object):
    """ Generate PDF report via LaTex.
        Generates LaTex document based on contents of the database and creates PDF out of it.
    """

    def __init__(self, dbname):
        self.con = mdb.connect(dbname)
        self.cursor = self.con.cursor()

    def __del__(self):
        if self.con:
            self.con.close()


    def printReport(self, out):
        """ All logic is in this method. 
            Links and other defects are separated. Tables with relevant contents are created. Paging is implemented.

            out : name of output document, .pdf is added automatically
        """
        doc = Document()
        doc.packages.append(Package('geometry', options = ['top=1in', 'bottom=1.25in', 'left=0.25in', 'right=1.25in']))
        self.links(doc)
        self.defects(doc)
        doc.generate_pdf(out)

    def links(self, doc):
        with doc.create(Section('Invalid links')):
            query = ('select defectType.description, transactions.uri, '
                         'location, evidence from defect inner join finding on'
                         ' finding.id = defect.findingId inner join defectType'
                         ' on defect.type = defectType.id inner join '
                         'transactions on transactions.id = finding.responseId where defectType.description = "Invalid link"'
                         'order by defectType.type')
            self.cursor.execute(query)
            
            row = self.cursor.fetchone()
            while row is not None:
                row = links_page(doc, row)

    def links_page(self, doc, row):
        with doc.create(Tabular('|l|l|l|')) as table:
            table.add_hline()
            table.add_row(('Decription', 'On page', 'To page'))
            table.add_hline()
  
            count = 0
            max_on_line = 47
            while row is not None:
                table.add_row((pylatex.utils.escape_latex(row[0].decode('utf-8')), pylatex.utils.escape_latex(urllib.unquote(row[1]).decode('utf-8')), pylatex.utils.escape_latex(urllib.unquote(row[3]).decode('utf-8'))))
                table.add_hline()
                count += 1
                row = self.cursor.fetchone()
                if count == max_on_line: break;
        doc.append('\\newpage')
        return row

    def defects(self, doc):
        with doc.create(Section('Other defects')):
            query = ('select defectType.description, transactions.uri, '
                         'location, evidence from defect inner join finding on'
                         ' finding.id = defect.findingId inner join defectType'
                         ' on defect.type = defectType.id inner join '
                         'transactions on transactions.id = finding.responseId where defectType.description != "Invalid link"'
                         'order by defectType.type')
            self.cursor.execute(query)
            row = self.cursor.fetchone()
            while row is not None:
                row = defects_page(doc, row)

    def defects_page(selfi, doc, row):
        with doc.create(Tabular('|l|l|')) as table:
            table.add_hline()
            table.add_row(('Line', 'Description'))
            table.add_row((' ', 'On page'))
            table.add_hline()

            count = 0
            max_on_line = 23
            while row is not None:
                table.add_row((pylatex.utils.escape_latex(str(row[2])), pylatex.utils.escape_latex(row[0].decode('utf-8')) ))
                table.add_row(('', pylatex.utils.escape_latex(urllib.unquote(row[1]).decode('utf-8')) ))
                table.add_hline()
                count += 1
                row = self.cursor.fetchone()
                if count == max_on_line: break;
        doc.append('\\newpage')
        return row

def run():
    """ Entry point - load command line arguments and call printReport or show usage.
    """
    if len(sys.argv) == 3:
        reporter = TexReporter(sys.argv[1])
        reporter.printReport(sys.argv[2])
    else:
        print("Usage: "+sys.argv[0]+" <dbname> <outputfile>\nFor output file - .pdf is added automatically")

if __name__ == "__main__":
    run()
