from lxml import etree
from lxml import html
import feedgenerator
import requests
import os
from flask import Flask

from flask import request
from urlparse import urljoin
from werkzeug.contrib.atom import AtomFeed
import datetime
from bs4 import BeautifulSoup

app = Flask(__name__)

def make_external(url):

    # if "#aTodosTitulos" == url:
    return urljoin(request.url_root, "http://google.com")
    # return urljoin(request.url_root, url)
def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts]
             for i in range(wanted_parts) ]

@app.route('/')
def recent_feed():
    feed = AtomFeed('Recent Articles',
                    feed_url=request.url, url=request.url_root)



    with open("email2.htm") as fp:
        mystring = fp.read().replace('\n', ' ').replace('\r', '').replace('\t', '')
        soup = BeautifulSoup(mystring, "lxml")


    # print(soup)
    tables = soup.find_all('table')
    # print(len(tables))



    news = []

    trs = tables[13].findAll('tr')
    for tr in trs:
        h1 = tr.findAll('h1')
        titles = [' '.join(x.span.get_text().split()) for x in h1]


        content_raw = tr.findAll('p')
        content = [' '.join(x.span.get_text().split()) for x in content_raw if ' '.join(x.span.get_text().split()) != '']

        link = tr.find('a')


        if len(titles) != 0 and len(content) != 0:
            news.append((titles[0], content, link.get('href')))

    news = [(t, '\n'.join(c[:-2]), c[len(c)-2][8:],l) for t, c,l in news]

    # for i, n in enumerate(news):
    #     print('============= {} ================'.format(i))
    #     print('title: {}'.format(n[0].encode('utf-8')))
    #     print('content: {}'.format(n[1].encode('utf-8')))
    #     print('from: {}'.format(n[2].encode('utf-8')))
    #     print('link: {}'.format(n[3].encode('utf-8')))
    #
    # print('there are {} news'.format(len(news)))


    # print(tables[1])

    # for each line in the table
    for i in news:
        # getting the identifier


        feed.add(i[0].encode('ascii', 'ignore').decode('ascii'), i[1].encode('ascii', 'ignore').decode('ascii'),
                 content_type='html',
                 author=i[2],
                 url=make_external(i[3]),
                 updated=datetime.datetime.today()
                 )

    return feed.get_response()



