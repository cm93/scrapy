# -*- encoding:utf-8 -*-
from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request,FormRequest
from web2waza.items import Web2WazaItem
import re
from os.path import getsize
import os
import requests
import web2waza.settings
import sys
import web2waza.config
from scrapy.shell import inspect_response  
import string

wgetimg = web2waza.config.wgetimg
coverupload = web2waza.config.coverupload


if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


root =  web2waza.settings.root
imgs_path = web2waza.settings.imgs_path

class Dadas(Spider):
    name = 'dadas'
    #web = 'http://www.dadas.com.tw/'
    cate_dict = ({'6-7':['humor','1']},{'11-12':['knowledge','222']},{'31-33':['movies','841']},{'26-28':['game','225']},{'11-14':['travel','751']},{'11-13':['life','223']},{'6-8':['horror','224']})
    def start_requests(self):
        url = 'http://www.dadas.com.tw/wp-admin/admin-ajax.php'
        headers = {'content-type': 'application/json'}
        for dicts in self.cate_dict:
            for (k,v) in dicts.items():
                for i in range(1,2):
                    payload = {'action': 'ajax_cat_post', 'paged':str(i),'cat':v[1]}
                    yield FormRequest(url, headers=headers,formdata=payload,meta={'cid':k},callback = self.parse_getarticle)
    def parse_getarticle(self,response):
        sel = Selector(response)
        orurl_lists = sel.xpath('//*[@class="entry-header"]').extract()
        if not orurl_lists:
            return
        for list in orurl_lists:
            orurl =re.findall('<a href=\"([^\"]+)\" rel="bookmark">',list)
            oid =  re.findall('/(\d+)/$',orurl[0])
            check_api = requests.get('%s/crawapi/check/%d/%d/%d'%(root,int(oid[0]),18,1)).text
            print check_api
            check_dick = eval(check_api.encode('utf-8'))
            if check_dick['status']:
                print check_dick['data']['ourl'].replace('\\','')+'已经存在'
                print 'wazafee id：'+check_dick['data']['aid']
                continue
            imgurl = re.findall('<img[^>]+src=\"([^\"]+)\"[^>]+>',list)
            cover_ourl = imgurl[0]
            cover_opath = wgetimg(cover_ourl)
            cover_path = imgs_path + '/' + cover_opath
            if os.path.exists(cover_path):
                size = getsize(cover_path)
                if size < 35000:
                    os.remove(cover_path)
                    continue
            item = Web2WazaItem()
            item['cover_name'] = coverupload(cover_path)
            if item['cover_name'] == False:
                continue
            #item['image_urls'].pop(0)
            item['cover_info'] = {'url':cover_ourl,'path':cover_opath}
            item['typeid'] =  response.meta['cid']
            item['fromurl'] = orurl[0]
            item['artile_id_key'] = int(oid[0])
            item['keytype'] = 1
            item['ori_web'] = 18
            yield Request(orurl[0],meta = {'item':item},callback = self.parse)
    def parse(self,response):
        item = response.meta['item']
        sel = Selector(response)
        item['message'] = sel.xpath('//div[@class="entry-content"]').extract()[0]
        item['image_urls'] = re.findall('<img[^>]+pagespeed_lazy_src=\"([^\"]+)\"[^>]+>',item['message'])
        imge_check = ''.join(item['image_urls'])
        if imge_check.count('.gif'):
            return
        try:
            del_div = sel.xpath('//div[@class="entry-content"]/ul').extract()[0]
            item['message'] = item['message'].replace(del_div,'')
        except:
            pass
        start = item['message'].find('延伸')
        end = len(item['message'])
        if(start != -1):
            item['message'] = item['message'].replace(item['message'][start:end],'')
        #图片data=》src
        img = sel.xpath('//div[@class="entry-content"]/descendant::img').extract()
        if len(img):
            for img_item in img:
                new_img = re.sub(r'pagespeed_lazy_src=(\"[^\"]+\")([^>]+src=)(\"[^\"]+\")',r'pagespeed_lazy_src=\3\2\1',img_item)
                item['message'] = item['message'].replace(img_item,new_img)
        item['subject'] = sel.xpath('//div[@class="single-title"]/h1/text()').extract()[0]
        item['tags'] = ''
        item['desc'] = sel.xpath('//meta[@property="og:description"]/@content').extract()[0]
        item['iframe'] = sel.xpath('//div[@class="entry-content"]/descendant::iframe').extract()
        return item
