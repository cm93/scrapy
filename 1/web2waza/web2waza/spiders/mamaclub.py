#! -*- encoding:utf-8 -*-
from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from web2waza.items import Web2WazaItem
import re
import sys
import web2waza.settings
import requests
import os
from os.path import getsize
import urllib
import web2waza.config

wgetimg = web2waza.config.wgetimg
coverupload = web2waza.config.coverupload

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


root =  web2waza.settings.root
imgs_path = web2waza.settings.imgs_path


class MamaclubSpider(Spider):
    name = 'mamaclub'
    web = 'http://mamaclub.com/learn/category/'
    cate_dict = ({'41-42':['美妆保养','fashion/']},{'41-43':['亲子妇幼','parenting/']},{'41-44':['居家布置','food/']},{'41-44':['居家布置','mamasmart/moneymoney/']},{'41-45':['女人心事','familyrelationship/']})

    def start_requests(self):
        for dicts in self.cate_dict:
            for (k,v) in dicts.items():
                yield Request('%s/%s'%(self.web,v[1]),meta={'cid':k},callback = self.parse_getarticle)


    def parse_getarticle(self,response):
        sel = Selector(response)
        orurl_lists = sel.xpath('//div[@class="fullarticle"]/div/div[@class="fullcontent "]/h2/a/@href').extract()
        if not orurl_lists:
            return
        #i = 1
        for orurl in orurl_lists:
            #if i>1:
                #continue
            #i = i+1
            orurl = urllib.unquote(orurl.encode('utf-8'))
            akey =  orurl.split('/')[-2].encode('utf-8')
            check_api = requests.get('%s/crawapi/check/%s/%d/%d'%(root,akey,17,2)).text
            check_dick = eval(check_api.encode('utf-8'))
            if check_dick['status']:
                print check_dick['data']['ourl'].replace('\\','')+'已经存在'
                print 'wazafee id：'+check_dick['data']['aid']+'\r\n\r\n'
                continue
            item = Web2WazaItem()
            item['typeid'] =  response.meta['cid']
            item['fromurl'] = orurl
            item['artile_id_key'] = akey
            item['keytype'] = 2
            item['ori_web'] = 17
            yield Request(orurl,meta = {'item':item},callback = self.parse)
        

    def parse(self,response):
        item = response.meta['item']
        sel = Selector(response)
        #图集        
        item['image_urls'] = sel.xpath('//div[@class="blogcontent"]/p/descendant::img/@src').extract()
        if not item['image_urls']:
            return
        imge_check = ''.join(item['image_urls'])
        if imge_check.count('.gif'):
            return
        del_frstimg = sel.xpath('//div[@class="blogcontent"]/p/descendant::img').extract()[0]
        try:
            cover_ourl = item['image_urls'][1]
        except:
            return
        cover_opath = wgetimg(cover_ourl)
        cover_path = imgs_path + '/' + cover_opath
        if os.path.exists(cover_path):
            size = getsize(cover_path)
            if size < 35000:
                os.remove(cover_path)
                return
        item['cover_name'] = coverupload(cover_path)
        if item['cover_name'] == False:
            return
        item['image_urls'].pop(0)
        item['cover_info'] = {'url':cover_ourl,'path':cover_opath}
        item['subject'] = sel.xpath('//h1[@class="blogtitle entry-title"]/span/text()').extract()[0]
        item['subject'] = item['subject'].strip()
        item['tags'] = sel.xpath('//meta[@name="keywords"]/@content').extract()[0]
        item['desc'] = sel.xpath('//meta[@name="description"]/@content').extract()[0]
        message = sel.xpath('//div[@class="blogcontent"]/p').extract()
        item['iframe'] = sel.xpath('//div[@class="blogcontent"]/p/iframe').extract()
        item['message'] = ''
        for itm in message:
            if itm.count(u'延伸閱讀') != 0 or itm.count(u'id=\"newsTopicWrapper\"') != 0:
                continue
            item['message'] = item['message']+itm
        item['message'] = re.sub('([^>\s]+)<img',r'\1<br><img',item['message'])
        item['message']  = item['message'] .replace(del_frstimg,'')
        return item
