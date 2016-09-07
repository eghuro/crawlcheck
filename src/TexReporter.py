import sqlite3 as mdb
from pylatex import Document, Section, Tabular, Package, NoEscape
import pylatex.utils
import sys
import urllib.parse

class TexReporter(object):
    """ Generate PDF report via LaTex.
        Generates LaTex document based on contents of the database and creates PDF out of it.
    """

    def __init__(self, dbname):
        print("Create reporter")
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
        
        max_on_page = 47
        with doc.create(Section('Invalid links')):
            query = ('select transactions.uri, defect.evidence, defectType.type from defect inner join defectType on defect.type = defectType.id inner join finding on finding.id = defect.findingId inner join transactions on transactions.id = finding.responseId where defectType.type = "badlink" or defectType.type = "timeout" order by defect.severity, transactions.uri')
            self.cursor.execute(query)
            row = self.cursor.fetchone()
            while row is not None:
                with doc.create(Tabular('|l|l|l|')) as table:
                    table.add_hline()
                    table.add_row(('On page', 'To page', 'Cause'))
                    table.add_hline()

                    count = 0
                    while row is not None:
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
                        count += 1

                        row = self.cursor.fetchone()
                        if count == max_on_page:
                            break #vyskoci z vnitrniho while
                #v kazdem pripade konec tabulky
                if row is not None: #doslo misto na strance
                    doc.append(NoEscape(r"\newpage"))
                continue

        with doc.create(Section('Other defects')):
            query = ('select transactions.uri, defect.evidence, defectType.description, defect.severity from defect inner join defectType on defect.type = defectType.id inner join finding on finding.id = defect.findingId inner join transactions on transactions.id = finding.responseId where defectType.type != "badlink" and defectType.type != "timeout" order by defect.severity desc, defectType.type, transactions.uri')
            self.cursor.execute(query)
            row = self.cursor.fetchone()
            while row is not None:
                with doc.create(Tabular('|l|l|l|l|')) as table:
                    table.add_hline()
                    table.add_row(('On page', 'Description', 'Evidence', 'Severity'))
                    table.add_hline()

                    count = 0
                    max_on_page = 47
                    while row is not None:
                        page = urllib.parse.unquote(row[0])
                        description = row[2]
                        evidence = row[1]
                        severity = row[3]
                        table.add_row((page, description, evidence, severity))
                        table.add_hline()
                        count += 1

                        row = self.cursor.fetchone()
                        if count == max_on_page:
                            break #vyskoci z vnitrniho while
                #v kazdem pripade konec tabulky
                if row is not None: #doslo misto na strance
                    doc.append(NoEscape(r"\newpage"))
                continue

        with doc.create(Section('Cookies')):
            query = ('select transactions.uri, cookies.name, cookies.value from cookies inner join finding on finding.id = cookies.findingId inner join transactions on finding.responseId = transaction.id')
            self.cursor.execute(query)
            row = self.cursor.fetchone()
            while row is not None:
                with doc.create(Tabular('|l|l|l|')) as table:
                    table.add_hline()
                    table.add_row(('On page', 'Name', 'Value'))
                    table.add_hline()

                    count = 0
                    max_on_page = 47
                    while row is not None:
                        page = urllib.parse.unquote(row[0])
                        name = row[1]
                        value = row[2]

                        table.add_row((page, name, value))
                        table.add_hline()
                        count += 1

                        row = self.cursor.fetchone()
                        if count == max_on_page:
                            break #vyskoci z vnitrniho while
                #v kazdem pripade konec tabulky
                if row is not None: #doslo misto na strance
                    doc.append(NoEscape(r"\newpage"))
                continue
        doc.generate_pdf(out)

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
