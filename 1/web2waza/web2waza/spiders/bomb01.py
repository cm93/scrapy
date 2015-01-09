#! -*- encoding:utf-8 -*-
from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from web2waza.items import Web2WazaItem
import re
import sys
import requests
import web2waza.settings
import web2waza.config
import os
from os.path import getsize

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


root =  web2waza.settings.root
imgs_path = web2waza.settings.imgs_path
wgetimg = web2waza.config.wgetimg
coverupload = web2waza.config.coverupload



class Bomb01Spider(Spider):
    name = 'bomb01'
    web = 'http://www.bomb01.com/'
    cate_dict = {'6-7':'Kuso搞笑'}
    def start_requests(self):
        yield Request('http://www.bomb01.com',meta={'cid':'6-7'},callback = self.parse_getarticle)


    def parse_getarticle(self,response):
        sel = Selector(response)
        href_list = sel.xpath('//div[@id="content"]/div/div/a/@href').extract()
        if not href_list:
            return
        for href in href_list:
            oid =  href.split('/')[-2]
            check_api = requests.get('%s/crawapi/check/%d/%d/%d'%(root,int(oid),16,1)).text
            check_dick = eval(check_api.encode('utf-8'))
            if check_dick['status']:
                print check_dick['data']['ourl'].replace('\\','')+'已经存在'
                print 'wazafee id：'+check_dick['data']['aid']+'\r\n\r\n'
                continue
            fromurl = 'http://www.bomb01.com'+href
            item = Web2WazaItem()
            item['typeid'] =  response.meta['cid']
            item['fromurl'] = fromurl
            item['artile_id_key'] = int(oid)
            item['keytype'] = 1
            item['ori_web'] = 16
            yield Request(fromurl,meta = {'item':item},callback = self.parse)
        

    def parse(self,response):
        item = response.meta['item']
        sel = Selector(response)
        #图集        
        image_urls = sel.xpath('//div[@id="content"]/descendant::img/@src').extract()
        if not image_urls:
            return
        item['image_urls'] = []
        for imgurl in image_urls:
            item['image_urls'].append('http://www.bomb01.com'+imgurl)
        if not item['image_urls']:
            return
        imge_check = ''.join(item['image_urls'])
        if imge_check.count('.gif'):
            return
        cover_ourl = item['image_urls'][0]
        cover_opath = wgetimg(cover_ourl)
        cover_path = imgs_path + '/' + cover_opath
        if os.path.exists(cover_path):
            size = getsize(cover_path)
            if size < 35000:
                os.remove(cover_path)
                return
        else:
            return 
        item['cover_name'] = coverupload(cover_path)
        if item['cover_name'] == False:
            return
        item['image_urls'].pop(0)
        item['cover_info'] = {'url':cover_ourl,'path':cover_opath}
        item['subject'] = sel.xpath('//h1[@class="title"]/text()').extract()[0]
        item['tags'] =''
        item['desc'] = sel.xpath('//meta[@property="og:description"]/@content').extract()[0]
        item['message'] = sel.xpath('//div[@id="content"]').extract()[0]
        item['iframe'] = sel.xpath('//div[@id="content"]/descendant::iframe').extract()
        return item
