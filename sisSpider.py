#! python2
# -*- coding: utf-8 -*-
from __future__ import division
import sys
import requests
from requests.adapters import HTTPAdapter
import gevent
import gevent.monkey
from bs4 import BeautifulSoup as bs
import uuid
import os
import time
import re
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from progressbar import *
import jieba
import jieba.analyse
import uniout
import gzip, urllib2
from cStringIO import StringIO
import bencode
from multiprocessing import Process

gevent.monkey.patch_all()
reload(sys)
sys.setdefaultencoding('utf-8')

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = dict()
headers[
    "User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3078.0 Safari/537.36"
headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
headers["Accept-Encoding"] = "gzip, deflate"
headers["Accept-Language"] = "zh-TW,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-CN;q=0.2"
request_retry = HTTPAdapter(max_retries=3)
raw_cookies = "__utma=1.370745750.1492854006.1492982897.1493033367.10;__utmb=1.9.10.1493033367;__utmc=1;__utmt=1;__utmz=1.1492854006.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none);cdb3_auth=ktPyW1g94sPFPJa%2F%2BW3BDIzJj9%2FkryGbWybjPbEfjvVhPQabIfDeUhsvfAzjsMjOjr8;cdb3_cookietime=2592000;cdb3_fid421=1493031082;cdb3_oldtopics=D7100968D6803533D;cdb3_sid=klJAVc;cdb3_smile=1D1;"
post_data = {
    "formhash": "7c24af93",
    "referer": "http://www.sexinsex.net/bbs/index.php",
    "loginfield": "username",
    "username": "",
    "password": "",
    "questionid": "0",
    "answer": "",
    "cookietime": "2592000",
    "loginmode": "",
    "styleid": "",
    "loginsubmit": "true",
}

try:
    sis_forum_id = int((raw_input(unicode('请输入论坛ID：', 'utf-8').encode('gbk'))))
except:
    sis_forum_id = 64
sis_domin_base_url = "http://www.sexinsex.net/bbs/"
login_url = "http://www.sexinsex.net/bbs/logging.php?action=login"
sis_base_url = "http://www.sexinsex.net/bbs/forum-" + str(sis_forum_id)
forum_name = str("AsianArtGallery东方唯美图坊").decode("utf-8")
requests_proxies = {"http": "http://127.0.0.1:8087", "https": "http://127.0.0.1:8087", }
requests_none_proxies = {
    "http": None,
    "https": None,
}
sis_error_forum_allow = False
sleep_time = 0.5
sis_allow_up_post=False
sis_if_login=True
if str((raw_input(unicode('是否设置高级设定(y/n)：', 'utf-8').encode('gbk'))))=='y':
    if str((raw_input(unicode('是否不登录(y/n)：', 'utf-8').encode('gbk'))))=='y':
        sis_if_login=False
    if str((raw_input(unicode('是否爬取置顶帖(y/n)：', 'utf-8').encode('gbk'))))=='y':
        sis_allow_up_post=True



url_get = requests.session()
url_get.headers = headers

def login():
    url_get.headers = headers
    url_get.post(login_url, proxies=requests_proxies, verify=False, data=post_data)


def get_page_url(page):
    # url_get = requests.session()
    url_get.headers = headers
    response = url_get.get(sis_base_url + "-" + str(page) + ".html", proxies=requests_proxies,
                           verify=False)  # ,cookies=get_cookies())
    soup = bs(response.content, "lxml")
    global forum_name
    forum_name = str(bs(response.content, "lxml").title.text).decode("utf-8")
    # print response.content
    print str(forum_name).decode("utf-8")
    storage_file("")
    storage_file("","error_storage")
    storage_file("","proxylist")
    for raw_post in soup.select('table#forum_' + str(sis_forum_id) + ' tbody tr'):
        try:
            post = raw_post.select_one('td.folder a')
            # print post
            # print raw_post
            post_url = post.attrs["href"]
            post_id = post.attrs["href"].replace("thread-", "").replace(".html", "")
            post = raw_post.select_one('td.nums')
            relay_number = int(str(post.text).split("/")[0])
            if str(raw_post).count("置顶")> 0 and sis_allow_up_post==False:
                continue
        except Exception, e:
            print "获取主题信息错误：".decode("utf-8"), e
            continue

        # print relay_number
        try:
            if verify_pic_page(post_id) == False and verify_pic_page(post_id,"error_storage") == False:
                get_pic_page(sis_domin_base_url + post_url, post_id, relay_number)
                storage_file(post_id + "|")
            else:
                if verify_pic_page(post_id) == True:
                    print "该主题已下载：".decode("utf-8") + post_id
                else:
                    print "该主题图源或已死：".decode("utf-8") + post_id
        except Exception, e:
            try:
                print str(post_id)
            except:
                pass
            print "获取主题错误：".decode("utf-8"), e


def get_pic_page(posturl, postid, replay_number):
    # url_get = requests.session()
    url_get.headers = headers
    response = url_get.get(posturl, proxies=requests_proxies, verify=False)  # ,cookies=get_cookies())
    soup = bs(response.content, "lxml")
    thanks_number=get_thankyou_number(response)
    pic_title = str(bs(response.content, "lxml").title.text.replace(forum_name, "")).decode("utf-8")
    pic_title = '[感谢数 - '+ str(thanks_number)+']'+pic_title
    if pic_title.count("502 Urlfetch Error") > 0:
        time.sleep(3)
        raise Exception("抛出异常:502错误".decode("utf-8").encode('gbk'))
    print unicode("开始下载:" + pic_title.replace("-", "") + "(" + str(postid) + ")")
    page = 0
    error_number = 0
    if_error=False
    pbar = ProgressBar().start()
    get_comment(response, pic_title, replay_number)
    get_attachment(response,pic_title,replay_number)
    for post in soup.select(".postmessage img"):
        # print post.attrs["src"]
        time.sleep(sleep_time)
        pbar.update(int(page / len(soup.select(".postmessage img")) * 100))
        if str(post).count('http') > 0:
            try:

                if page==0:
                    print str(post.attrs["src"])
                    print get_proxy_info(post.attrs["src"])
                page += 1
                download_pic(post.attrs["src"], pic_title, page, replay_number)
                # print int(page/len(soup))
            except Exception, e:
                print "下载图片错误：".decode("utf-8"), e
                error_number += 1
                try:

                    if str(e).count("HTTPConnectionPool") > 0:
                        rstr = r".*host\=(.*)\port\=.*"  # '/\:*?"<>|'
                        http_get = re.findall(rstr, str(e))[0]
                        print http_get
                        storage_file(http_get+"|", filename="proxylist")
                except Exception, e:
                    print "提取错误信息错误：".decode("utf-8"), e
        if error_number > 3:
            if_error = True
            storage_file(postid+"|", filename="error_storage")
            print "错误次数过多;跳过".decode("utf-8")
            break
    if if_error == False:
        pbar.finish()

def get_comment(response,title,replay_number):
    txt_response=response
    soup = bs(response.content, "lxml")
    comment_content=''
    reforum_name = forum_name.replace("-  SexInSex! Board", "")
    reforum_name = validateTitle(reforum_name).replace(" ", "")
    if replay_number >= 35:
        title = "[热门]" + title
    title = validateTitle(title).replace(" ", "").replace("-", "")
    if txt_response.status_code == 200:
        if not os.path.exists("img/" + reforum_name + "/" + title):
            print str("img/" + reforum_name + "/" + title).decode("utf-8")
            os.makedirs("img/" + reforum_name + "/" + title)
        with open("img/" + reforum_name + "/" + title + "/" + "comment" + ".txt", 'w') as fs:
            for post in soup.select("div.postmessage div.t_msgfont"):
                    #print post.get_text()
                comment_content+=str(str(post.get_text(strip=True)))
                fs.write(str(post.get_text(strip=True))+'\r\n')
            print get_key_word(comment_content).decode('unicode-escape')

def get_thankyou_number(response):
    soup=bs(response.content,'lxml')
    post=soup.select_one('span.postratings div b')
    if post!=None:
        return  post.get_text()
    else:
        return '0'


def get_attachment(response,title,replay_number):
    txt_response=response
    soup = bs(response.content, "lxml")
    reforum_name = forum_name.replace("-  SexInSex! Board", "")
    reforum_name = validateTitle(reforum_name).replace(" ", "")
    if replay_number >= 35:
        title = "[热门]" + title
    title = validateTitle(title).replace(" ", "").replace("-", "")
    #print soup.select("dl.t_attachlist dt a")
    if txt_response.status_code == 200:
        if not os.path.exists("img/" + reforum_name + "/" + title):
            print str("img/" + reforum_name + "/" + title).decode("utf-8")
            os.makedirs("img/" + reforum_name + "/" + title)
        for attachment in soup.select("dl.t_attachlist dt a"):
            torrent_title=attachment.get_text()
            print torrent_title
            torrent_url=sis_domin_base_url+attachment.attrs['href']
            print torrent_url
            with open("img/" + reforum_name + "/" + title + "/" + torrent_title, 'wb') as fs:
                    response = url_get.get(torrent_url, proxies=requests_proxies,
                                           verify=False)  # ,cookies=get_cookies())
                    data = response.content
                    #print data
                    #gzipper = gzip.GzipFile(fileobj=StringIO(data))
                    #print gzipper
                    #plain = gzipper.read()
                    #data = plain
                    fs.write(data)


def download_pic(url, title, page, replay_number):
    new_url_get = requests.session()
    new_url_get.headers = headers
    pic_response = new_url_get.get(url, proxies=check_proxy(url), verify=False, timeout=20)
    reforum_name = forum_name.replace("-  SexInSex! Board", "")
    title = validateTitle(title).replace(" ", "").replace("-", "")
    if replay_number >= 35:
        title = "[热门]" + title
    reforum_name = validateTitle(reforum_name).replace(" ", "")
    if pic_response.status_code == 200:
        if not os.path.exists("img/" + reforum_name + "/" + title):
            print str("img/" + reforum_name + "/" + title).decode("utf-8")
            os.makedirs("img/" + reforum_name + "/" + title)
        with open("img/" + reforum_name + "/" + title + "/" + title + "_" + str(page) + ".jpg", 'wb') as fs:
            fs.write(pic_response.content)
    else:
        raise Exception(str("状态代码错误："+str(pic_response.status_code)).decode("utf-8").encode('gbk'))


def check_proxy(url):
    proxy_domin_list = ["showhaotu", ".club", ".net", ".cc", ".info", ".co", ".ru", "gonzb.com", "postimg.org",
                        "pixxxels.org", "vstanced.com", "showhaotu.club", "moepicx.cc", "sezuzu.info", "imgur.com",
                        "xoimg.co", "etwalls.com", "flickr.com", "niupic.com"]
    for domin in proxy_domin_list:
        if url.count(domin) > 0:
            return requests_proxies
    time.sleep(2)
    return requests_none_proxies

def get_proxy_info(url):
    proxy_domin_list = ["showhaotu", ".club", ".net", ".cc", ".info", ".co", ".ru", "gonzb.com", "postimg.org",
                        "pixxxels.org", "vstanced.com", "showhaotu.club", "moepicx.cc", "sezuzu.info", "imgur.com",
                        "xoimg.co", "etwalls.com", "flickr.com", "niupic.com"]
    for domin in proxy_domin_list:
        if url.count(domin) > 0:
            return '正在使用代理伺服器...'.decode('utf-8')
    return '正在使用本地连接...'.decode('utf-8')


def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/\:*?"<>|'
    new_title = re.sub(rstr, "", title)
    return new_title


def verify_pic_page(pageid,filename="storage"):
    if filename=="error_storage" and sis_error_forum_allow==True:
        return True
    reforum_name = forum_name.replace("-  SexInSex! Board", "")
    reforum_name = reforum_name.replace("|", "").replace(" ", "")
    pageid = str(pageid).split("-")
    pageid = pageid[0]
    print pageid
    with open("img/" + reforum_name + "/" + filename+".txt", "r") as fs:
        content = fs.readlines()
        if str(content).count(pageid) > 0:
            return True
        else:
            return False


def storage_file(content, filename="storage"):
    reforum_name = forum_name.replace("-  SexInSex! Board", "")
    reforum_name = validateTitle(reforum_name).replace(" ", "")
    # print reforum_name
    if not os.path.exists("img/" + reforum_name):
        os.makedirs("img/" + reforum_name)
    with open("img/" + reforum_name + "/" + filename + ".txt", "a") as fs:
        fs.write(content)


def get_cookies():
    new_cookies = {}
    try:
        for line in raw_cookies.split(';'):
            key = line.split("=", 1)[0]  # 1代表只分一次，得到两个数据
            value = line.split("=", 1)[1]
            new_cookies[key] = value
    except:
        pass
    # print new_cookies
    return new_cookies

def get_key_word(content):
    return str(jieba.analyse.extract_tags(content, topK=20, withWeight=False, allowPOS=()))


start_page = int((raw_input(unicode('请输入开始页：', 'utf-8').encode('gbk'))))
end_page = int((raw_input(unicode('请输入结束页：', 'utf-8').encode('gbk'))))
if sis_if_login==True:
    login()





for i in range(start_page, end_page + 1):
    get_page_url(i)
