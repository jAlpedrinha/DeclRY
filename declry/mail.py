# _*_  encoding: utf-8 _*_

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from threading import local

class Mailer(local):

    def login(self):
        self.server = smtplib.SMTP('smtp.gmail.com:587')
        self.server.ehlo()
        self.server.starttls()
        self.server.login('secretaria@institutonunalvres.pt', 'mkkwulat')
    
    def addheader(self, message, headername, headervalue):
        if self.containsnonasciicharacters(headervalue):
            h = Header(headervalue, 'utf-8')
            message[headername] = h
        else:
            message[headername] = headervalue    
        return message

    def containsnonasciicharacters(self, str):
        return not all(ord(c) < 128 for c in str)   



    def send(self, email_txt, subject, to):
        self.login()

        msg = MIMEMultipart('alternative')
        msg = self.addheader(msg, 'Subject', subject)
        msg['From'] = 'secretaria@institutonunalvres.pt'
        msg['To'] = to

        if(self.containsnonasciicharacters(email_txt)):
            plaintext = MIMEText(email_txt.encode('utf-8'),'plain','utf-8') 
        else:
            plaintext = MIMEText(email_txt,'plain')
        msg.attach(plaintext)

        self.server.sendmail('helpdesk@scholr.net', [to], msg.as_string())
        self.quit()

    def quit(self):
        self.server.quit()

mailer = Mailer()