from __future__ import print_function
import httplib2
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException        
import unittest, time, re
import numpy as np
import string

import requests
import bs4
from bs4 import BeautifulSoup
import math
from datetime import date, datetime, timedelta
import re
import pandas
import calendar

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient import errors
import base64
import email
import imaplib 
import email
import quopri
import HTMLParser
from bs4 import BeautifulSoup
import urllib2
import pandas as pd
from datetime import datetime
datetime.now().strftime('%Y-%m-%d %H:%M:%S')
import nltk
from text_stemmer import ScoreText
from string import letters
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None
# Use key words to score the relavance of the job    
good_words = {'python':5, 'matlab':10, 'R':5, 'Python':5, 'Matlab':10, 'data':2, 'analysis':5, 'model':5,'Analyze':5, 'modeling':5, 'economics':10,'Economics':10, 'Master':5, 'master':5, 'PhD':10, 'scientist':10,'Scientist':10, 'machine':10}
bad_words = {'clinical':-5, 'chemistry':-5, 'biology':-5,'biostatistics':-5,'senior':-10,'hadoop':-5,'Senior':-10,'software':-2,'Software':-2, 'MBA':-20}


def retrieve_text(soup,current_url):
    t = None
    title = None
    if current_url.startswith('https://www.glassdoor.com'):
        if current_url.startswith('https://www.glassdoor.com/job-listing'):
            try:
                dd = soup.find(id="JobDescContainer")
                df = soup.find("h2", {"class" : "noMargTop margBotXs strong"})
                title = driver.find_element_by_css_selector("h2.noMargTop").text
            except:
                print('Unable to retrieve for glassdoor.\n')
        else:
            try:
                dd = soup.find(id="JobDescriptionContainer")
                t = dd.text.encode('utf8')
                title = driver.find_element_by_css_selector("h1.noMargTop").text
            except:
                print('Unable to retrieve for glassdoor.\n')
    else:
        if current_url.startswith('https://www.indeed.com'):
            try:
                dd = soup.find(id="job_summary")
                t = dd.text.encode('utf8')
                df = soup.findAll("b", { "class" : "jobtitle" })
                title = re.sub("<.*?>", "", str(df)).replace('[','').replace(']','')
            except:
                print('Unable to retrieve for indeed.\n')
        else:
            try:
                t = soup.text.encode('utf8')
            except:
                print('Unable to retrieve for other websites.\n')
    return (t, title)

def get_credentials():
    home_dir = os.getcwd()
    credential_dir = os.path.join(home_dir, 'credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)  
    credential_path = os.path.join(credential_dir,'gmail-python-quickstart.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def ListMessagesWithLabels(service, user_id, label_ids=[], query=[]):
    try:
        response = service.users().messages().list(userId=user_id,labelIds=label_ids, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id,labelIds=label_ids, q=query, pageToken=page_token).execute()
            messages.extend(response['messages'])
        return messages
    except errors.HttpError, error:
        print('An error occurred: %s' % error)   


def GetMessage(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        print('Message snippet: %s' % message['snippet'])
        return message
    except errors.HttpError, error:
        print('An error occurred: %s' % error)

def GetMimeMessage(service, user_id, msg_id):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id,format='raw').execute()
        print('Message snippet: %s' % message['snippet'])
        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
        mime_msg = email.message_from_string(msg_str)
        return mime_msg
    except errors.HttpError, error:
        print('An error occurred: %s' % error)

def RetriveEmailList(service):
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    if not labels:
        print('No labels found.')
    else:
      #print('Labels:')
      for label in labels:
        #print(label['name']+ " "+label['id'])
        if label['name'].lower().startswith('job'):
            email_id_list = ListMessagesWithLabels(service, user_id='me', label_ids=[label['id']], query = "in:unread")
            print('There are %d unread emails of label %s.\n' %(len(email_id_list), label['name']))
    return email_id_list
def check_and_make_dir(dir):
   if not os.path.exists(dir):
        os.makedirs(dir)  

# Initialize word list and parameters
words_list = good_words.copy()
words_list.update(bad_words)
porter = nltk.PorterStemmer()
text_stemmer = ScoreText(porter, words_list)

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
CLIENT_SECRET_FILE = 'client_secret2.json'
APPLICATION_NAME = 'Gmail API Email Screening'

# Start to get the emails        
credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('gmail', 'v1', http=http)

email_id_list = RetriveEmailList(service)
error_urls = []
title_list = []
gp = []
bp = []
ap = []
gw_list = []
bw_list = []
url_list = []
counter = 0 
for j in range(0,10):
    # Get urls from email
    email_id = email_id_list[j]['id']
    email_content = GetMimeMessage(service, 'me', email_id)
    msg = email_content.get_payload()
    links = []
    for i in range(0,len(msg)):
        content = quopri.decodestring(str(msg[i]))
        soup = BeautifulSoup(content, 'html.parser')
        for link in soup.find_all('a'):
            links.append(link.get('href'))
    print('There are %d links to retrieve.\n' % (len(links)-7))
    # Use firefox to text from urls in emails
    fp = webdriver.FirefoxProfile()
    fp.set_preference("browser.download.folderList",2)
    fp.set_preference("browser.download.manager.showWhenStarting",False)

    driver = webdriver.Firefox(firefox_profile=fp)
    last_url = ''
    for k in range(1,int(len(links))-6):       
        url = links[k]
        if url == last_url:
            print('Link %d is a repetitive link.\n' % k)
            last_url = url
            continue
        last_url = url
        print('Start processing link %d.\n' % k)
        if url.startswith('https://www.glassdoor.com/job-alert') or url.startswith('https://www.glassdoor.com/profile'):
            continue
        driver.get(url)
        time.sleep(4)
        page_source = driver.page_source
        page_source_clean = page_source.encode('utf-8')
        soup = BeautifulSoup(page_source_clean,"lxml")
        current_url = driver.current_url
        (t, title) = retrieve_text(soup,current_url)
        if t:
            if title:
                title_list.append(title)
            else:
                title_list.append('NA')
            # Read the text and record "good" and "bad" words
            tokens = nltk.word_tokenize(t.decode('utf-8'))
            (gw_in,bw_in,total_count_a,total_count_p,total_count_n) = text_stemmer._score(tokens)
            gp.append(total_count_p)
            bp.append(total_count_n)
            ap.append(total_count_a)
            url_list.append(current_url)
            gw_list.append(gw_in)
            bw_list.append(bw_in)
        else:
            error_urls.append(current_url)
        time.sleep(1)
    counter += 1
    print('Finish %d of %d emails.\n' % (counter, len(email_id_list)))
    driver.close()
    # Mark as read
    service.users().messages().modify(userId='me', id=email_id,body={ 'removeLabelIds': ['UNREAD']}).execute()
    df = pd.DataFrame({'Title':title_list, 'GoodPoint': gp, 'BadPoint': bp, 'TotalPoint': ap, 'Url': url_list, 'GoodWords': gw_list, 'BadWords': bw_list})
    df2 = pd.DataFrame({'bad_url': error_urls})
    datetime_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    home_dir = os.getcwd()
    job_csv_dir = os.path.join(home_dir, 'jobs')
    error_csv_dir = os.path.join(home_dir, 'errors')
    check_and_make_dir(job_csv_dir)
    check_and_make_dir(error_csv_dir) 
    df.to_csv(os.path.join(job_csv_dir,'jobs' +datetime_now+'.csv'))
    df2.to_csv(os.path.join(error_csv_dir, 'url_errors'+ datetime_now + '.csv'))
#email_csv = pd.DataFrame({'email id': email_id_list})
#email_csv.to_csv('email id list.csv')