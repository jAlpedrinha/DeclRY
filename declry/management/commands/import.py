from django.core.management.base import BaseCommand, CommandError
import pyodbc
import sqlite3
import decimal
from datetime import datetime, date
__author__ = 'AlexandreRua'


class Command(BaseCommand):
    args = '<poll_id poll_id ...>'
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        con = pyodbc.connect('DRIVER={SQL Server};SERVER=srv-sql;DATABASE=ina;UID=sa;PWD=jfk')
        c=con.cursor()

        con2=sqlite3.connect('c:/wamp/apps/wsgi/school-manager/db.db')
        c2=con2.cursor()

        tables=['common_profissao']#'common_banktransferline']#,'com_seccao','form_formacao','form_formacaoformador','form_formacaoformando'] #,'com_seccaoempregado']
        #tables=['pedagogic_course','pedagogic_subject']
        # tables.extend(['pessoal_universidade','pessoal_cursosuperior','pessoal_empregado','pessoal_empregadohabilitacao','pessoal_empregadoproteccaosocial'])
        # tables.extend(['formacao_formacao','formacao_formacaoformador','formacao_formacaoformando'])

        for t in tables:
            
            self.stdout.write( '{:.<35}.'.format(t))
            c2.execute('delete from {}'.format(t))
            n=0
            #print "select %s from %s" % (','.join(sourcefields),sourcetable)
            for r in c.execute("sp_wwwexport '{}'".format(t)):
                newr=[]
                n+=1
                for f in r:
                    if type(f)==str:
                        newr.append(f.decode('latin1').strip())
                    elif type(f)==decimal.Decimal:
                        newr.append(str(f))
                    elif type(f)==datetime:
                        if f.hour==0 and f.minute==0:
                            newr.append(date(f.year,f.month,f.day))
                        else:
                            newr.append(f)
                    else:
                        newr.append(f)
        #        print newr
                try:
                    c2.execute('insert into {} values({})'.format(t,','.join('?'*len(newr))),tuple(newr))
                except:
                    self.stdout.write( newr)
                    raise
            self.stdout.write('{} records'.format(n))

        con2.commit()

        con2.close()
        con.close()