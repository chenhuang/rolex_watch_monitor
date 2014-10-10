#! /usr/bin/python
# This script monitor the vintage rolex website and returns any information that has been updated. 
# This is the website URL to monitor: http://www.hqmilton.com/vintage-watches/rolex

import sys
import re
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP_SSL as SMTP
import httplib
import json
import os.path
import datetime
from bs4 import BeautifulSoup
import codecs

#working_directory = "/Users/chhuang/Dropbox/Car/"
class Monitor:
    def __init__(self, dire):
        self.directory = dire

    # SMTP Email Sending Function
    # Outlook.com works really great on this one
    def send_email(self,subject, content):
        me = "robot@gmail.com"
        you = "youremail@gmail.com"

        SMTP_server = "smtp.gmail.com"
        user_name = me
        pwd = "password"
        SMTP_port = 587

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = me
        msg['To'] = you

        msg.attach(MIMEText(content,'html'))

        conn = smtplib.SMTP(SMTP_server,SMTP_port)
        conn.starttls()
        conn.login(user_name,pwd)
        conn.sendmail(me, you, msg.as_string())
        conn.close()

    # Fetch data from MBPreowned, with the given zipcode and distance
    def fetch_data(self):
        url = "www.hqmilton.com"
        query = "/vintage-watches/rolex"

        conn = httplib.HTTPConnection(url)
        conn.request("GET",query)
        rl = conn.getresponse()
        if rl.status != 200 or rl.reason != "OK":
            send_email("mypreownedmercedes web error",rl.status+": "+rl.reason)
            sys.exit(0)
        data = rl.read()

        return data

    # Parse html of rolex watches
    def parse(self,data):
        soup = BeautifulSoup(data)
        divs = soup.find_all('div',attrs={'class':'span4 product-overview clearfix'})
        watch_data = []
        for div in divs:
            watch = {}
            url = div.a['href']
            img = div.find('img',attrs={'class':'img-border'})['src']
            detail = div.find('div',attrs={'class':'product-overview-details'})
            serial = detail.h2.string
            name = detail.p.em.string.encode('ascii', 'ignore')
            price = detail.p.contents[1]
            id = serial+name
            watch['url'] = url
            watch['img'] = img
            watch['serial'] = serial
            watch['name'] = name
            watch['price'] = price
            watch['id'] = url
            watch_data.append(watch)

        return watch_data

    # Update local database and send the new watch information to my email box
    # I keep two files on record:
    # 1. Current watch list, the list that keeps the most updated watch information
    # 2. Archived watch list, the list that keeps cars that have been on shelf.

    def update(self, watch_data):
        on_market_file_name = self.directory+"/rolex.json"
        data = ""
        existing_watch = {}
        watchid_set = set()
        if os.path.isfile(on_market_file_name) == True:
            fin = open(on_market_file_name, "r")
            data = fin.read()
            fin.close()
            watchs = json.loads(data)
            for watch in watchs:
                existing_watch[watch['id']] = watch
                watchid_set.add(watch['id'])


        # Compare fetched data with current watch on file
        new_count = 0
        email_subject = ""
        email_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rolex</title>
        <style type="text/css">
            body {
                font-family:"Segoe UI", "Liberation Sans", "Nimbus Sans L", Helvetica, Arial, serif;
                font-size:14px;
            }

            dl {
                margin-bottom:0px;
            }
         
            dl dt {
                color:#000;
                font-weight: bold;
                float:left; 
                margin-right:0px; 
                padding:0px;  
                width: 75px;
            }
             
            dl dd {
                margin:0px; 
                padding:0px;
            }
            ol,ul {
                margin:0px;
                margin-bottom: 0px;
            }
        </style>
    </head>

    <body>
    <ol>
    """

        changed_count = 0
        email_content_changed_vehicle = """
    </ol>
    <h3>Watch Information Changed:</h3>
    <ol>
        """
        for watch in watch_data:
            # If the vehicle informaion is on record, update the information
            watch_id = watch['id']
            if watch_id in watchid_set:
                is_changed = False
                watchid_set.remove(watch_id)
                for key in watch.keys():
                    if key == 'img':
                        continue
                    if existing_watch[watch_id][key] != watch[key]:
                        print watch_id, existing_watch[watch_id][key], watch[key]
                        is_changed = True
                    existing_watch[watch_id][key] = watch[key]
                watch["record_date"] = existing_watch[watch_id]["record_date"]
                if is_changed == True:
                    changed_count += 1
                    email_content_changed_vehicle += self.generate_email_content(watch)
            # If not in, new car, set email and archive it
            else:	
                new_count += 1
                watch["record_date"] = str(datetime.datetime.now()) 
                email_content += self.generate_email_content(watch)

        if changed_count > 0:
            email_content += email_content_changed_vehicle

        email_content += """
        </ol>
        
        </body>
        </html>
        """
        # Send an email to me for new watchs:
        if new_count > 0 or changed_count > 0:
            if changed_count > 0:
                email_subject = str(changed_count) + " rolex info changed"  + email_subject
            if new_count > 0:
                email_subject = str(new_count) + " new "+ "rolex " + email_subject
            self.send_email(email_subject,email_content)

        # Update current car JSON file
        fout = open(self.directory+'/rolex.json','w')
        fout.write(json.dumps(watch_data))
        fout.close()

    def generate_email_content(self, watch):
        url = watch['url']
        img = watch['img']
        serial = watch['serial']
        name = watch['name']
        price = watch['price']
        id = watch['id']

        content = 	"""
        <li>
            <dl>
                <dt>Serial: </dt><dd>
        """
        content += str(serial)
        content += """
                </dd>
                <dt>Name: </dt><dd>
        """
        content += str(name)
        content += """
                </dd>
                <dt>Price: </dt><dd>
        """
        content += str(price)
        content += """
                </dd>
        """
        content += '<dd>\n'
        content += '<img src="'+img+'" height="100", width="145"><a href="'+url+'">URL</a>'
        content += """
                </dd>
            </dl>
        </li>
        """

        return content

if __name__ == "__main__":
    m = Monitor('absolution path to the folder where you store the watch data')
    watch_data = m.parse(m.fetch_data())
    m.update(watch_data)



