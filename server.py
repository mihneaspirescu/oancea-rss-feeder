import pickle
from flask import Flask
from flask import jsonify
from flask import request
import hashlib
import os
from rfeed import *
import uuid


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
allnews = {}
latest_pubdate = datetime.datetime.today()

# save and reload data
pickle_file = "rssdata.pickle"
if os.path.exists(pickle_file) is not True:
    open(pickle_file, 'a').close()
elif os.path.getsize(pickle_file) != 0:
    with open(pickle_file, 'rb') as pickle_off:
        allnews = pickle.load(pickle_off)
        print("#######################################")
        print("Preloaded {} posts".format(len(allnews)))
        print("#######################################")



def pickle_data(state):
    print("Saving data...")
    pickling_on = open(pickle_file, "wb")
    pickle.dump(state, pickling_on)
    pickling_on.close()
    print("Saved!")





def merge_two_dicts(x, y):
    z = x.copy()  # start with x's keys and values
    z.update(y)  # modifies z with y's keys and values & returns None
    return z


def captureContent(tr):
    h1 = tr.findAll('h1')
    titles = [' '.join(x.span.get_text().split()) for x in h1]

    content_raw = tr.findAll('p')
    content = [' '.join(x.span.get_text().split()) for x in content_raw if ' '.join(x.span.get_text().split()) != '']

    link = tr.find('a')

    return titles, content, link


def captureText(tables):
    news11 = {}
    news13 = {}
    trs11 = tables[11].findAll('tr')
    trs13 = tables[13].findAll('tr')

    for tr in trs13:
        titles, content, link = captureContent(tr)
        if len(titles) != 0 and len(content) != 0:
            hash_object = hashlib.md5((str(titles[0]) + str(content) + str(link.get('href'))).encode())
            news13[hash_object.hexdigest()] = (titles[0], content, link.get('href'))

    for tr in trs11:
        titles, content, link = captureContent(tr)
        if len(titles) != 0 and len(content) != 0:
            hash_object = hashlib.md5((str(titles[0]) + str(content) + str(link.get('href'))).encode())
            print(hash_object.hexdigest())

            news11[hash_object.hexdigest()] = (titles[0], content, link.get('href'))

    if len(news11) != 0:
        return news11
    else:
        return news13


def make_external(url):
    return urljoin(request.url_root, "http://google.com/{}".format(uuid.uuid4().hex))


def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [alist[i * length // wanted_parts: (i + 1) * length // wanted_parts]
            for i in range(wanted_parts)]


def save_data(content):
    count = 0
    count_added = 0

    content = content.decode("utf-8")
    mystring = content.replace('\n', ' ').replace('\r', '').replace('\t', '')
    soup = BeautifulSoup(mystring, "lxml")

    tables = soup.find_all('table')

    for id, data in captureText(tables).items():
        if id not in allnews:
            global latest_pubdate
            string_date = datetime.datetime.today()
            allnews[id] = (
                data[0], '\n'.join(data[1][:-2]), data[1][len(data[1]) - 2][8:], data[2], string_date)
            count_added += 1
            latest_pubdate = string_date
        else:
            count += 1

    pickle_data(allnews)

    return count, count_added


def make_email_addr(name):
    return "{0}@email.com ({1})".format(name.replace(" ", "").encode('ascii', 'ignore').decode('ascii'),
                                        name.encode('ascii', 'ignore').decode('ascii'))


@app.route('/update', methods=['POST'])
def update_feed():
    count, count_added = save_data(request.data)
    return jsonify({"success": True, "added": count_added, "duplicates": count})


def sort_dict(feed):
    return sorted(feed.items(), key=lambda elem: elem[1][4], reverse=True)


@app.route('/reset')
def reset_db():
    global allnews
    allnews = {}
    pickle_data(allnews)

    return jsonify({"success": True, "message": "Emptied the db"})


@app.route('/rss.xml')
def recent_feed():
    arr = []
    # for each line in the table
    for id, i in sort_dict(allnews):
        # getting the identifier
        arr.append(Item(
            title=i[0].encode('ascii', 'ignore').decode('ascii'),
            link=make_external(i[3]),
            description=i[1].encode('ascii', 'ignore').decode('ascii'),
            author=make_email_addr(i[2]),
            guid=Guid(id, isPermaLink=False),
            pubDate=i[4]))

    feed = Feed(
        title="RSS Feed",
        link="http://ec2-35-177-192-241.eu-west-2.compute.amazonaws.com/rss.xml",
        description="Feed for parsing emails...",
        language="en-US",
        lastBuildDate=latest_pubdate,
        items=arr)

    return feed.rss(), 200, {'Content-Type': 'application/rss+xml'}
