#!venv/bin/python
import requests
import json
from bs4 import BeautifulSoup as soup
import re
from flask import Flask, jsonify, make_response


app = Flask(__name__,static_url_path='')

root_url = 'http://www1.skysports.com/'
transfer_url = "https://data.livefyre.com/bs3/v3.1/bskyb.fyre.co/363166/MTAwMDk1MTI=/init"
sports = ["football", "cricket", "golf", "rugby-league", "boxing", "tennis", "f1", "darts", "snooker", "cycling", "american-football", "motor-racing", "ice-hockey", "baseball"]


def get_news(index_url):
    response = requests.get(index_url)
    latest = []
    item = {}
    bs = soup(response.text)
    allnews = bs.findAll("div", {"class":"news-list__item news-list__item--show-thumb-bp30"})
    for news in allnews:
        #latest.append(news.noscript.img.attrs.get('src'))
        #latest.append(news.find("div",{"class":"news-list__body"}).p.get_text())
        itemdetail = news.find("div",{"class":"news-list__body"})
        #latest.append(itemdetail.p.get_text())
        #latest.append(re.sub('\s+',' ',itemdetail.h4.get_text()))
        #latest.append(itemdetail.h4.a.attrs.get('href'))
        item = {"imgsrc":news.noscript.img.attrs.get('src'),"title":re.sub('\s+',' ',itemdetail.h4.get_text()),"shortdesc":itemdetail.p.get_text(),"link":itemdetail.h4.a.attrs.get('href')}
        latest.append(item)
    return latest


def get_text(html):
    return str(soup(html).text).replace("\n", "")  # remove all new lines


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/sky/getlatest/v1.0/', methods=['GET'])
def get_latest():
    index_url = root_url + "latest-news" + "/"
    response = requests.get(index_url)
    latest = {}
    bs = soup(response.text)
    for sport in sports:
        info = []
        for a in bs.select("div.site-wrapper a[href^=https://www.skysports.com/" + sport + "/]"):
            info.append({"link": a.attrs.get('href'), "text": a.get_text()})
        latest[sport] = info
    return json.dumps(latest)


@app.route('/sky/getnews/<string:name_of_sport>/v1.0/', methods=['GET'])
def get_sportsnews(name_of_sport):
    index_url = root_url+ name_of_sport +"/news/"
    latest = []
    latest = get_news(index_url)
    return json.dumps(latest)


@app.route('/sky/<string:sport>/getteamnews/<string:team>/v1.0/', methods=['GET'])
def get_teamsnews(sport,team):
    index_url=root_url+ sport+"/teams/"+team+"/news/"
    latest = []
    latest = get_news(index_url)
    return json.dumps(latest)


@app.route('/sky/transfer/news/v1.0/')
def transfer():
    r = requests.get(transfer_url)
    content = json.loads(r.text)
    item = []
    articles = content['headDocument']['content']
    for article in articles:
        news = {}
        content = article['content']
        if 'bodyHtml' in content.keys():
            bs = soup(content['bodyHtml'])
            title = str(bs.select("p:first-child strong")[0])
            body = content['bodyHtml'].replace(title, "", 1)  # remove the title from body
            news['title'] = get_text(title)
            news['body'] = get_text(body)
        news['time'] = content['createdAt']  # timestamp
        if 'attachments' in content.keys():
            attachments = []
            for attachment in content['attachments']:
                attachment_content = {}
                if 'thumbnail_url' in attachment.keys():
                    attachment_content['thumbnail_url'] = attachment['thumbnail_url']
                if 'html' in attachment.keys():
                    attachment_content['html'] = attachment['html']
                if 'type' in attachment.keys():
                    attachment_content['type'] = attachment['type']
                attachments.append(attachment_content)
            news['attachments'] = attachments
        item.append(news)
    res = make_response(json.dumps(item))
    res.headers = {
        'Content-Type': 'application/json',
        'Cache-control': 'no-cache'
    }
    return res


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    app.run(debug=True)



