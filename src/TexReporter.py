import MySQLdb as mdb
from pylatex import Document, Section, Tabular, Package
import pylatex.utils

class TexReporter(object):

    def __init__(self, uri, user, password, dbname):
        self.con = mdb.connect(uri, user, password, dbname)
        self.cursor = self.con.cursor()

    def __del__(self):
        if self.con:
            self.con.close()


    def printReport(self):
        doc = Document()
        doc.packages.append(Package('geometry', options = ['top=1in', 'bottom=1.25in', 'left=0.25in', 'right=1.25in']))
        with doc.create(Section('Invalid links')):
            query = ('select defectType.description, transaction.uri, '
                         'location, evidence from defect inner join finding on'
                         ' finding.id = defect.findingId inner join defectType'
                         ' on defect.type = defectType.id inner join '
                         'transaction on transaction.id = finding.responseId where defectType.description = "Invalid link"'
                         'order by defectType.type')
            self.cursor.execute(query)
            row = self.cursor.fetchone()
            while row is not None:
                with doc.create(Tabular('|l|l|l|')) as table:
                    table.add_hline()
                    table.add_row(('Decription', 'On page', 'To page'))
                    table.add_hline()
  
                    count = 0
                    max_on_line = 47
                    while row is not None:
                        table.add_row((pylatex.utils.escape_latex(row[0].decode('utf-8')), pylatex.utils.escape_latex(row[1].decode('utf-8')), pylatex.utils.escape_latex(row[3].decode('utf-8'))))
                        table.add_hline()
                        count+=1
                        row = self.cursor.fetchone()
                        if count == max_on_line: break;
                doc.append('\\newpage')
 
        with doc.create(Section('Other defects')):
            query = ('select defectType.description, transaction.uri, '
                         'location, evidence from defect inner join finding on'
                         ' finding.id = defect.findingId inner join defectType'
                         ' on defect.type = defectType.id inner join '
                         'transaction on transaction.id = finding.responseId where defectType.description != "Invalid link"'
                         'order by defectType.type')
            self.cursor.execute(query)
            row = self.cursor.fetchone()
            while row is not None:
               with doc.create(Tabular('|l|l|')) as table:
                   table.add_hline()
                   table.add_row(('Line', 'Description'))
                   table.add_row((' ', 'On page'))
                   table.add_hline()

                   count = 0
                   max_on_line = 23
                   while row is not None:
                       table.add_row((pylatex.utils.escape_latex(str(row[2])), pylatex.utils.escape_latex(row[0].decode('utf-8')) ))
                       table.add_row(('', pylatex.utils.escape_latex(row[1].decode('utf-8')) ))
                       table.add_hline()
                       count+=1
                       row = self.cursor.fetchone()
                       if count == max_on_line: break;
               doc.append('\\newpage')

        doc.generate_pdf('report')

def run():
    reporter = TexReporter("localhost", "test", "", "crawlcheck")
    reporter.printReport()

if __name__ == "__main__":
    run()
