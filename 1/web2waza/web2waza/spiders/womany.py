#! -*- encoding:utf-8 -*-
from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from web2waza.items import Web2WazaItem
import re
import sys
import requests
import web2waza.settings
import os
from os.path import getsize
import web2waza.config

wgetimg = web2waza.config.wgetimg
coverupload = web2waza.config.coverupload

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


root =  web2waza.settings.root
imgs_path = web2waza.settings.imgs_path


class WomanySpider(Spider):
    name = 'womany'
    web = 'http://womany.net/read'
    cate_dict = {'41-45':'女人心事'}
    def start_requests(self):
        yield Request('http://womany.net/read.js?page=1',meta={'cid':'41-45'},callback = self.parse_getarticle)


    def parse_getarticle(self,response):
        oid_list = re.findall('data-href=\\\\\"http://womany.net/read/article/(\d+)\\\\\"',response._body)
        if not oid_list:
            return
        for oid in oid_list:
            check_api = requests.get('%s/crawapi/check/%d/%d/%d'%(root,int(oid),4,1)).text
            check_dick = eval(check_api.encode('utf-8'))
            if check_dick['status']:
                print check_dick['data']['ourl'].replace('\\','')+'已经存在'
                print 'wazafee id：'+check_dick['data']['aid']+'\r\n\r\n'
                continue
            fromurl = 'http://womany.net/read/article/%d'%int(oid)
            item = Web2WazaItem()
            item['typeid'] =  response.meta['cid']
            item['fromurl'] = fromurl
            item['artile_id_key'] = int(oid)
            item['keytype'] = 1
            item['ori_web'] = 4
            yield Request(fromurl,meta = {'item':item},callback = self.parse)
        

    def parse(self,response):
        item = response.meta['item']
        sel = Selector(response)
        #图集        
        item['message'] = sel.xpath('//section[@class="article-body"]').extract()[0]
        item['image_urls'] = re.findall('<img[^>]+src=\"([^\"]+)\"[^>]*>',item['message'])
        if not item['image_urls']:
            return
        imge_check = ''.join(item['image_urls'])
        if imge_check.count('.gif'):
            return
        try:
            cover_ourl = item['image_urls'][0]
        except:
            return
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
        item['subject'] = sel.xpath('//section[@class="article-header"]/a/h1/text()').extract()[0]
        item['tags'] = sel.xpath('//meta[@name="keywords"]/@content').extract()[0]
        item['desc'] = sel.xpath('//meta[@name="description"]/@content').extract()[0]
        item['desc'] = item['desc'].replace(u'womany 編按：','')
        item['desc'] = item['desc'].strip()
        item['iframe'] = sel.xpath('//section[@class="article-body"]/descendant::iframe').extract()
         
        delp_list = sel.xpath('//section[@class="article-body"]/p').extract()
        for delp in delp_list:
            if delp.count(u'請勿任意轉載') !=0 or delp.count(u'延伸閱讀') !=0:
                item['message'] = item['message'].replace(delp,'')
        item['message']  = item['message'] .replace(u'womany 編按：','')
        item['message']  = item['message'] .replace(u'womany編按：','')
        item['message']  = item['message'] .replace(u'Womany編按：','')
        item['message']  = item['message'] .replace(u'Womany 編按：','')
        item['message'] = item['message'].strip()
        try:
            relate_del = sel.xpath('//section[@class="article-body"]/descendant::div[@class="related-articles"]').extract()[0]
            item['message'] = item['message'].replace(relate_del,'')
        except:
            pass
        return item
