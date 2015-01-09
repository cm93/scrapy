#! -*- encoding:utf-8 -*-
from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request
from web2waza.items import Web2WazaItem
import re
from os.path import getsize
import os
import requests
import web2waza.settings
import sys
import web2waza.config

wgetimg = web2waza.config.wgetimg
coverupload = web2waza.config.coverupload


if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


root =  web2waza.settings.root
imgs_path = web2waza.settings.imgs_path


class LifeSpider(Spider):
    name = 'life'
    web = 'http://www.life.com.tw'
    cate_dict = ({'1-3':'44'},{'1-4':'54'},{'6-7':'13'},{'11-12':'19'},{'11-13':'63'},{'11-14':'11'},{'11-15':'57'},{'11-15':'10'},{'16-17':'8'},{'16-18':'36'},{'16-19':'38'},{'16-20':''},{'21-22':'15'},{'21-23':'22'},{'21-24':'61'},{'21-25':'29'},{'26-27':'5'},{'26-28':'25'},{'26-29':'47'},{'26-30':''},{'31-32':'45'},{'31-33':'27'},{'31-34':'30'},{'31-35':'1'},{'36-37':''},{'41-43':'16'},{'41-44':'24'},{'41-45':'12'},{'46-48':'35'},{'46-50':'17'},{'36-39':'23'})


    def start_requests(self):
        for dicts in self.cate_dict:
            for (k,v) in dicts.items():
                yield Request('%s/?app=category&act=categorylist&no=%s'%(self.web,v),meta={'cid':k},callback = self.parse_getarticle)


    def parse_getarticle(self,response):
        sel = Selector(response)
        orurl_lists = sel.xpath('//*[@class="shadow radius5"]/dl/dt/a/@href').extract()
        if not orurl_lists:
            return
        #i = 1
        for orurl in orurl_lists:
            #if i>1:
                #continue
            #i = i+1
            oid =  re.findall('no=(\d+)',orurl)[0]
            check_api = requests.get('%s/crawapi/check/%d/%d/%d'%(root,int(oid),1,1)).text
            check_dick = eval(check_api.encode('utf-8'))
            if check_dick['status']:
                print check_dick['data']['ourl'].replace('\\','')+'已经存在'
                print 'wazafee id：'+check_dick['data']['aid']
                continue
            item = Web2WazaItem()
            item['typeid'] =  response.meta['cid']
            item['fromurl'] = self.web + orurl
            item['artile_id_key'] = int(oid)
            item['keytype'] = 1
            item['ori_web'] = 1
            yield Request(self.web + orurl,meta = {'item':item},callback = self.parse)
        

    def parse(self,response):
        item = response.meta['item']
        sel = Selector(response)
        #图      
        item['message'] = sel.xpath('//div[@id="mainContent"]').extract()[0]
        item['image_urls'] = re.findall('<img[^>]+src=\"([^\"]+)\"[^>]+>',item['message'])
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
        item['cover_name'] = coverupload(cover_path)
        if item['cover_name'] == False:
            return
        item['image_urls'].pop(0)
        item['cover_info'] = {'url':cover_ourl,'path':cover_opath}
        item['subject'] = sel.xpath('//h1/text()').extract()[0]
        item['tags'] = ''
        item['desc'] = sel.xpath('//meta[@property="og:description"]/@content').extract()[0]
        item['iframe'] = sel.xpath('//div[@id="mainContent"]/descendant::iframe').extract()
        message = sel.xpath('//div[@id="mainContent"]/p|//div[@id="mainContent"]/div|//div[@id="mainContent"]/div[@class="article_body"]/p|//div[@id="mainContent"]/div[@class="article_body"]/div|//div[@id="mainContent"]/table').extract()
        try:
            del_div = sel.xpath('//div[@id="mainContent"]/div[@class="article_body"]').extract()[0]
            message.remove(del_div)
        except:
            pass
        
        div_exist = 0
        for index,itm in enumerate(message):
            if itm.count(u'更多精彩') != 0 or itm.count('class="writer"') or itm.count(u'文章來源') != 0 or itm.count(u'來源</a>') != 0 or itm.count(u'未經授權，請勿轉載') != 0 or itm.count(u'粉絲團') or itm.count(u'圖、文') or itm.count(u'相關連結') or itm.count(u'最短時間進行撤除') or itm.count(u'via <a rel')  or itm.count(u'via <a href')or itm.count(u'圖片來源</a') or itm.count(u'團</span') or itm.count(u'圖文來源') or itm.count(u'<video'):
                split_tags = itm
                div_exist = 1
                break
        try:
            item['message'] = item['message'].split(split_tags,1)[0]
        except:
            pass
            
        item['message'] = item['message'].encode('utf-8')
        item['message'] = re.sub(r'(<img[^>]+>)([^<])',r"\1<br>\2",item['message'])
        item['message'] = re.sub(r'(<img[^>]+>)<img',r"\1<br><img",item['message'])
        item['message'] =re.sub(r'<p>\s*(\xc2\xa0)*(<strong>[\s-]*</strong>)*(\xc2\xa0)*</p>','',item['message'])
        item['message'] = item['message'].replace('<p> </p>','')
        start = item['message'].find('延伸')
        end = len(item['message'])
        if(start != -1):
            item['message'] = item['message'].replace(item['message'][start:end],'')

        #补全标签
        if item['message'].count('<div class="article_body">'):
            item['message'] = item['message']+'</div>'
        if div_exist==1:
           item['message'] = item['message']+'</div>'
        return item
