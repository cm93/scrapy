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
import web2waza.config

wgetimg = web2waza.config.wgetimg
coverupload = web2waza.config.coverupload

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


root =  web2waza.settings.root
imgs_path = web2waza.settings.imgs_path


class ZhaizhaiSpider(Spider):
    name = 'zhaizhai'
    web = 'http://news.gamme.com.tw/category'

    cate_dict = ({'6-7':['Kuso搞笑','kuso']},{'6-9':['邪恶漫画','anime']},{'6-10':['奇闻异事','myst']},{'26-28':['游戏电玩','gaming']},{'31-32':['娱乐八卦','entertainment']},{'31-35':['电影世界','pets']},{'46-48':['男人品味','hotguy']})

    def start_requests(self):
        for dicts in self.cate_dict:
            for (k,v) in dicts.items():
                yield Request('%s/%s'%(self.web,v[1]),meta={'cid':k},callback = self.parse_getarticle)


    def parse_getarticle(self,response):
        sel = Selector(response)
        orurl_lists = sel.xpath('//div[@class="List-4"]/a/@href|//div[@class="adwrpt"]/a/@href').extract()
        if not orurl_lists:
            return
        #i = 1
        for orurl in orurl_lists:
            #if i>1:
                #continue
            #i = i+1
            akey =  orurl.split('/')[-1]
            aid = re.findall('(\d+)',akey)[0]
            check_api = requests.get('%s/crawapi/check/%d/%d/%d'%(root,int(aid),2,1)).text
            check_dick = eval(check_api.encode('utf-8'))
            if check_dick['status']:
                print check_dick['data']['ourl'].replace('\\','')+'已经存在'
                print 'wazafee id：'+check_dick['data']['aid']+'\r\n\r\n'
                continue
            item = Web2WazaItem()
            item['typeid'] =  response.meta['cid']
            item['fromurl'] = orurl
            item['artile_id_key'] = aid
            item['keytype'] = 1
            item['ori_web'] = 2
            yield Request(orurl,meta = {'item':item},callback = self.parse)
        

    def parse(self,response):
        item = response.meta['item']
        sel = Selector(response)
        #图集        
        image_urls_list = sel.xpath('//div[@class="entry"]/descendant::img/@src|//div[@class="post"]/descendant::img/@data-original').extract()
        if not image_urls_list:
            return
        item['image_urls']=[]
        for img_url in image_urls_list :
            if  img_url.count(u'http://images.gamme.com.tw/news'):
                item['image_urls'].append(img_url)
        imge_check = ''.join(img_url)
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
        item['subject'] = sel.xpath('//div[@class="post"]/h1[@class="title"]/text()').extract()[0]
        item['tags'] = sel.xpath('//meta[@name="keywords"]/@content').extract()[0]
        item['desc'] = sel.xpath('//meta[@name="description"]/@content').extract()[0]
        item['message'] = sel.xpath('//div[@class="entry"]').extract()[0]
        item['iframe'] = sel.xpath('//div[@class="entry"]/descendant::iframe').extract()
        #图片data=》src
        img = sel.xpath('//div[@class="entry"]/descendant::img').extract()                                                                     
        for img_index,img_item in enumerate(img):
            new_img = re.sub(r'src=(\"/images/grey.gif\")([^>]+data-original=)(\"[^\"]+\")',r'src=\3\2\1',img_item)
            item['message'] = item['message'].replace(img_item,new_img)
        #过滤
        photovia = sel.xpath('//div[@class="entry"]/descendant::em[@class="photovia"]').extract()[0]        
        discuss = sel.xpath('//div[@class="entry"]/descendant::div[@class="discuss"]').extract()[0]
        script = sel.xpath('//div[@class="post"]/descendant::script').extract()[0]
        pre_list = sel.xpath('//div[@class="entry"]/descendant::pre').extract()
        item['message'] = item['message'].replace(photovia,'')
        item['message'] = item['message'].replace(discuss,'')
        item['message'] = item['message'].replace(script,'')
        item['message'] = item['message'].replace(u'<p><strong></strong></p>','')
        item['message'] = item['message'].replace(u'<p></p>','')
        for pre in pre_list:
            item['message'] = item['message'].replace(pre,'')
        return item
