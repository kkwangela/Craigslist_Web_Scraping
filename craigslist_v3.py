#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 14:53:18 2019

@author: kewang
"""

'''
This file is used to scrape Craigslist
'''

import requests
from bs4 import BeautifulSoup
import pandas as pd
from math import sin, cos, sqrt, atan2, radians

def getHTMLText(url):
    '''
    access url
    param: str
    return: text
    '''
    try:
        r = requests.get(url, timeout = 30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except:
        return 'Exception!'
    
def nextPage(soup):
    '''
    return: next_page url
    param: soup
    return: str
    '''    
    url = 'https://sandiego.craigslist.org'
    body = soup.body
    button = body.section.find('span', class_ = 'buttons')
    buttonnext = button.find('a', class_ = 'button next')

    url +=  buttonnext['href']

    return url

def caldistance(la2, lo2):
    
    '''
    calculate distance based on latitude and longitude
    param: float, float
    return: float
    
    '''
    R = 3956

    lat1 = radians(32.881294)
    lon1 = radians(-117.237706)
    lat2 = radians(float(la2))
    lon2 = radians(float(lo2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

    
def singlePost(url):
    
    '''
    scape information of each post, including attributes, distance, contactinfo and postID
    param: url
    return: condition[str], postID[str], contact[bool], distance[float]
    
    '''
    r = getHTMLText(url)
    soup = BeautifulSoup(r,'html.parser')
    section = soup.body.section.section.section
    attrs = section.find('p', class_ = 'attrgroup')

    condition = 'Unknown' #list of attributes
    try: 
        a = attrs.find('span')
        if not a:
            condition = 'Unknown'
        else:
            if 'condition' in a.get_text().split(': '):
                condition = a.get_text().split(': ')[1]
            else:
                condition = 'Unknown'
    except:
        pass
        
    
    contact = 'False'
    latitude = 0
    longitude = 0
    distance = 0
    
    if section.find('p', class_ = 'postinginfo'):
        
        postID = section.find('p', class_ = 'postinginfo').string
        postID = postID[9:]
        
        postingBody = section.section

        for c in postingBody.children:
            if 'Text' in c or 'text' in c or 'Call' in c or 'call' in c:
                contact = 'True'
            elif postingBody.a:
                contact = 'True'

    else:
        postID = 'None'
    if section.find('div', id = 'map'):
        s = section.find('div', class_ ="viewposting")
        latitude = s['data-latitude']
        longitude = s['data-longitude']
        distance = caldistance(latitude, longitude)
    
    return condition, postID, contact, distance


def fillItemList(text):
    '''
    generate the list for each item: name, price, postDate, image, attr, postID, contact, distance
    param: text
    return: soup, list[list]
    
    
    '''
    soup = BeautifulSoup(text,'html.parser')
    body = soup.body
    for child in body.section.children:
        if child.name == 'form':
            form = child
        
    ct = form.find('div', class_ = 'content')
    item_list = ct.ul
    item_info = []

    for item in item_list.find_all('li'):
    
        item_title = item.p.a.string
        
        meta = item.p.find('span', class_ = 'result-meta')
        item_price = meta.span.string
        post_date = item.p.find('time')
        item_date = post_date['datetime']
        item_url = item.a['href']
        
        attr, postID, contact, distance = singlePost(item_url) #attr = list[str], postID = str
        
        image = 'False' if len(item.a['class']) == 3 else 'True'
        name = item_title
        price = int(item_price.replace('$', ''))
        postDate = item_date
        
        item_info.append([name, price, postDate, image, attr, postID, contact, distance])
        
    return soup, item_info

def outputFile(d, path):
    '''
    generate csv file
    param: d[list], path[str]
    no return value 
    '''
    name, price, date, image, attr, postID, contact, distance = [],[],[],[],[],[],[], []
    for i in d:
        name.append(i[0])
        price.append(i[1])
        date.append(i[2])
        image.append(i[3])
        attr.append(i[4])
        postID.append(i[5])
        contact.append(i[6])
        distance.append(i[7])
    dataframe = pd.DataFrame({'Name': name, \
                              'Price': price, \
                              'postDate': date, \
                              'HasImage': image, \
                              'Attributes': attr, \
                              'postID': postID, \
                              'contactInfo': contact, \
                              'distance': distance})
    
    dataframe.to_csv(path, index = True) 

 
def start(url, out_path):
    '''
    start the scrapping process
    param: url[str], out_path[str]
    no return value
    '''
    r = getHTMLText(url)
    print('now processing page 1')
    s, d = fillItemList(r) #process first page

    for i in range(10):  
        try:           
            url = nextPage(s)
            r = getHTMLText(url)
            s_next, d_next = fillItemList(r)
            for i in d_next:
                d.append(i)
            s = s_next
            
            #print('now processing page {}'.format(i + 2))
        except:
            print('Running out of pages.')
            break
    outputFile(d, out_path)



if __name__ == '__main__':
    
    
    url_samsung_s9 = 'https://sandiego.craigslist.org/search/sss?query=samsung+s9&sort=rel'
    url_samsung_s8 = 'https://sandiego.craigslist.org/search/sss?query=samsung%20s8&sort=rel'
    url_samsung_s7 = 'https://sandiego.craigslist.org/search/sss?query=samsung+s7&sort=rel'
    
    url_iphone_x = 'https://sandiego.craigslist.org/search/sss?query=iphone%20x&sort=rel'
    url_iphone_7 = 'https://sandiego.craigslist.org/search/sss?query=iphone%207&sort=rel'
    url_iphone_6s = 'https://sandiego.craigslist.org/search/sss?query=iphone+6s&sort=rel'
    url_iphone_6 = 'https://sandiego.craigslist.org/search/moa?hints=static&mobile_os=2&query=%22iphone%206%22&sort=rel&srchType=T'
    
    url_pixel_4 = 'https://sandiego.craigslist.org/search/sss?query=google+pixel+4&sort=rel'
    url_pixel_3 = 'https://sandiego.craigslist.org/search/sss?query=google+pixel+3&sort=rel'
    url_pixel_2 = 'https://sandiego.craigslist.org/search/sss?query=google+pixel+2&sort=rel'
    
    url = [url_samsung_s9, url_samsung_s8, url_samsung_s7, url_iphone_x, url_iphone_7, url_iphone_6s,url_iphone_6, url_pixel_4, url_pixel_3, url_pixel_2]

    ymd = 1202
    
    s9 = '/Users/kewang/Desktop/ECE143/Craigslist_samsungs9-{}.csv'.format(ymd)
    s8 = '/Users/kewang/Desktop/ECE143/Craigslist_samsungs8-{}.csv'.format(ymd)
    s7 = '/Users/kewang/Desktop/ECE143/Craigslist_samsungs7-{}.csv'.format(ymd)
    
    ipx = '/Users/kewang/Desktop/ECE143/Craigslist_iphonex-{}.csv'.format(ymd)
    ip7 = '/Users/kewang/Desktop/ECE143/Craigslist_iphone7-{}.csv'.format(ymd)
    ip6s = '/Users/kewang/Desktop/ECE143/Craigslist_iphone6s-{}.csv'.format(ymd)
    ip6 = '/Users/kewang/Desktop/ECE143/Craigslist_iphone6-{}.csv'.format(ymd)
    
    gp4 = '/Users/kewang/Desktop/ECE143/Craigslist_pixel4-{}.csv'.format(ymd)
    gp3 = '/Users/kewang/Desktop/ECE143/Craigslist_pixel3-{}.csv'.format(ymd)
    gp2 = '/Users/kewang/Desktop/ECE143/Craigslist_pixel2-{}.csv'.format(ymd)
    
    out = [s9,s8,s7,ipx,ip7,ip6s,ip6,gp4,gp3,gp2]
   

    for u, n in zip(url, out):

        start(u,n)
    
        
    print('finish!')
    #time.sleep(120) # scrape after 120s
    #i = datetime.datetime.now()
        
    
    
    
   
