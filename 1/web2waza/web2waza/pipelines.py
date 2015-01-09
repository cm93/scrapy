#! /usr/local/lib/python2.7
#! -*- encoding:utf-8 -*-
import redis
import re
import json
import os
import requests
import hashlib
import Image
from os.path import getsize
import sys
import web2waza.settings
from scrapy.selector import Selector
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


root =  web2waza.settings.root
imgs_path = web2waza.settings.imgs_path
wget_path = web2waza.settings.wget_path
local_img_url = web2waza.settings.local_img_url


class Web2WazaPipeline(object):
    def process_item(self, item, spider):
        #iframe过滤和替换
        if  item['iframe']:
            for iframe in item['iframe']:
                if iframe.count('youtube.com/embed/'):
                    try:
                        youtube_key = re.findall('www.youtube.com/embed/([^\"]+)\"',iframe)[0]
                    except:
                        pass
                    new_iframe = '<embed type="application/x-shockwave-flash" class="edui-faked-video" pluginspage="http://www.macromedia.com/go/getflashplayer" src="https://www.youtube.com/v/'+youtube_key+ '" ' +'width="100%" wmode="transparent" play="true" loop="false" menu="false" allowscriptaccess="never" allowfullscreen="true">'
                    item['message'] = item['message'].replace(iframe,new_iframe)
                else:
                    if  iframe.count('embed.gettyimages.com'):
                        iframe_src = re.findall('src=\"([^\"]+)\"',iframe)[0]
                        src_text = requests.get('http:'+iframe_src).text
                        src_sel = Selector(text=src_text)
                        new_iframe = src_sel.xpath('//figure/a/img').extract()[0]
                        src_img_url = src_sel.xpath('//figure/a/img/@src').extract()[0]
                        rep_src_img = src_img_url
                        if not src_img_url.count('http'):
                             src_img_url ='http:'+src_img_url
                        src_img_path = self.wgetimg(src_img_url)
                        src_img_now_url =  local_img_url + '/' + src_img_path
                        new_iframe = new_iframe.replace('&amp;','&')
                        new_iframe = new_iframe.replace(rep_src_img,src_img_now_url)
                        item['message'] = item['message'].replace(iframe,new_iframe)


        #图片送入imgcc
        if len(item['images']) != len(item['image_urls']) :
            for pic in item['images']:
                item['image_urls'].remove(pic['url'])
            for index2,picurl2 in enumerate(item['image_urls']):
                item['images'].append({'url':picurl2,'path':self.wgetimg(picurl2)})
        if(item['ori_web'] != 18):
            item['images'].append(item['cover_info'])

        for index,picurl in enumerate(item['images']):
            try:
                item['images'][index]['nowurl'] =  local_img_url + '/' +item['images'][index]['path']
            except (IOError):
                item['images'][index]['path'] = self.wgetimg(item['images'][index]['url'])
                item['images'][index]['nowurl'] =  local_img_url + '/' +item['images'][index]['path']
            #imgcc图替换原文图 
            if item['ori_web'] == 16:
                item['images'][index]['url'] = '/'+item['images'][index]['url'].split('/',3)[-1]
            item['message'] = item['message'].replace(item['images'][index]['url'],item['images'][index]['nowurl'])
        item['message'] = re.sub(r'<a[^>]+>([^<]*[^a]*[^>]*)</a>',r'\1',item['message'])
        item['message'] = re.sub('<img[^>]+src=\"([^\"]+)\"[^>]*>',r'<img src="\1" class="center-block">',item['message'])
        item['message'] = item['message'].replace('style=\"\"','')
        item['message'] = re.sub('<div[^>]*>','<div>',item['message'])

        #放入redis
        redisdata = {'message':item['message'],\
                     'tags':item['tags'],\
                     'subject':item['subject'],\
                     'desc':item['desc'],\
                     'cover':item['cover_name'],\
                     'fromurl':item['fromurl'],\
                     'artile_id_key':item['artile_id_key'],\
                     'keytype':item['keytype'],\
                     'ori_web':item['ori_web'],\
                     'typeid':item['typeid'],}
        data = json.dumps(redisdata)
        print '新增:'+redisdata['fromurl'] + '\r\n\r\n\r\n'
        r = redis.Redis(host='127.0.0.1', port=6379, db=1)
        r.lpush('web2waza',data)


    #图片管道下载失败进入wget下载
    def wgetimg(self,imgurl):
        if imgurl.count('png'):
            suffix ='png'
        else:
            suffix = 'jpg'
        key = hashlib.sha1(imgurl).hexdigest()
        key = key + '.'+suffix
        imgpath = '%s/full/%s'%(imgs_path,key)
        os.system("/usr/bin/wget -t 2 -T 30 '%s' -O %s -o %s"%(imgurl,imgpath,wget_path))
        imgpath = 'full/%s'%key
        return imgpath
