from flask import Flask
from flask import jsonify
from flask import request

try:
    from urllib.parse import urlparse
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urlparse
from werkzeug.contrib.atom import AtomFeed
import datetime

from bs4 import BeautifulSoup

app = Flask(__name__)

# all news DB
allnews = []


def captureContent(tr):
    h1 = tr.findAll('h1')
    titles = [' '.join(x.span.get_text().split()) for x in h1]

    content_raw = tr.findAll('p')
    content = [' '.join(x.span.get_text().split()) for x in content_raw if ' '.join(x.span.get_text().split()) != '']

    link = tr.find('a')

    return titles, content, link


def captureText(tables):
    news11 = []
    news13 = []
    trs11 = tables[11].findAll('tr')
    trs13 = tables[13].findAll('tr')

    for tr in trs13:
        titles, content, link = captureContent(tr)
        if len(titles) != 0 and len(content) != 0:
            news13.append((titles[0], content, link.get('href')))

    for tr in trs11:
        titles, content, link = captureContent(tr)
        if len(titles) != 0 and len(content) != 0:
            news11.append((titles[0], content, link.get('href')))

    if len(news11) != 0:
        return news11
    else:
        return news13


def make_external(url):
    return urljoin(request.url_root, "http://google.com")


def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [alist[i * length // wanted_parts: (i + 1) * length // wanted_parts]
            for i in range(wanted_parts)]


def save_data(content):
    content = content.decode("utf-8")
    mystring = content.replace('\n', ' ').replace('\r', '').replace('\t', '')
    soup = BeautifulSoup(mystring, "lxml")

    tables = soup.find_all('table')
    news = [(t, '\n'.join(c[:-2]), c[len(c) - 2][8:], l) for t, c, l in captureText(tables)]
    allnews.extend(news)


@app.route('/update', methods=['POST'])
def update_feed():
    save_data(request.data)
    return jsonify({"done": "yes boss"})


@app.route('/')
def recent_feed():
    feed = AtomFeed('Recent Articles',
                    feed_url=request.url, url=request.url_root)

    # for each line in the table
    for i in allnews:
        # getting the identifier


        feed.add(i[0].encode('ascii', 'ignore').decode('ascii'), i[1].encode('ascii', 'ignore').decode('ascii'),
                 content_type='html',
                 author=i[2],
                 url=make_external(i[3]),
                 updated=datetime.datetime.today()
                 )

    return feed.get_response()
