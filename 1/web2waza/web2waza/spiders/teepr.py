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


class TeeprSpider(Spider):
    name = 'teepr'
    web = 'http://www.teepr.com'
    cate_dict = ({'1-3':['社会新闻','新聞/']},{'6-7':['Kuso搞笑','爆笑/']},{'6-7':['Kuso搞笑','藝術/建築/']},{'6-7':['Kuso搞笑','藝術/設計/']},{'6-7':['Kuso搞笑','藝術/攝影/']},{'6-7':['Kuso搞笑','女性專區/']},{'6-10':['奇闻异事','驚奇/地球/']},{'6-10':['奇闻异事','驚奇/社會/']},{'6-10':['奇闻异事','驚奇/歷史/']},{'11-13':['励志感人','感動/']},{'11-14':['旅游指南','旅遊/']},{'11-15':['美食料理','生活/食物/']},{'16-17':['保健养生','生活/健康/']},{'16-18':['减肥塑身','生活/時尚/']},{'31-32':['娱乐八卦','娛樂/']},{'31-34':['音乐情报','表演/音樂/']},{'31-34':['音乐情报','表演/跳舞/']},{'31-35':['电影世界','動物/']},{'36-38':['心里测验','生活/心理/']},{'46-50':['两性关系','生活/愛情/']})
    def start_requests(self):
        for dicts in self.cate_dict:
            for (k,v) in dicts.items():
                yield Request(self.web+'/category/'+v[1],meta={'cid':k},callback = self.parse_getarticle)


    def parse_getarticle(self,response):
        sel = Selector(response)
        orurl_lists = sel.xpath('//article[@class="latestPost excerpt  "]/a/@href').extract() 
        if not orurl_lists:
            return
        #i = 1
        for orurl in orurl_lists:
            #if i>1:
                #break
            #i=i+1
            oid =  re.findall('/(\d+)/',orurl)[0]
            check_api = requests.get('%s/crawapi/check/%d/%d/%d'%(root,int(oid),15,1)).text
            check_dict = eval(check_api.encode('utf-8'))
            if check_dict['status']:
                print '源文章：'+ check_dict['data']['ourl'].replace('\\','')
                print 'waza文章:' +root+'/dashboard/editArticle/'+ check_dict['data']['aid'].replace('\\','')+'\r\n'
                continue
            item = Web2WazaItem()
            item['typeid'] =  response.meta['cid']
            item['fromurl'] = self.web+'/'+oid+'/'
            item['artile_id_key'] = int(oid)
            item['keytype'] = 1
            item['ori_web'] = 15
            yield Request(item['fromurl'],meta = {'item':item},callback = self.parse)
            

    def parse(self,response):
        item = response.meta['item']
        body = response.body
        body = body.replace('<article class=\"article \">','<div class=\"article \">')
        body = body.replace('</article>','</div>')
        body = body.replace('<div class=single_post>','<div class=\"single_post\">')
        sel = Selector(text=body)
        #图集        
        item['message'] = sel.xpath('//div[@class="post-single-content box mark-links"]').extract()[0]
        item['image_urls'] = re.findall('<img[^>]+src=\"([^\"]+)\"[^>]*>',item['message'])
        imge_check = ''.join(item['image_urls'])
        if imge_check.count('.gif'):
            return
        if not item['image_urls']:
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
        item['subject'] = sel.xpath('//div[@class="single_post"]/header/h1/text()').extract()[0]
        item['tags'] = ''
        item['desc'] = ''
        item['iframe'] = sel.xpath('//div[@class="post-single-content box mark-links"]/descendant::iframe').extract()
        #图片data=》src
        img = sel.xpath('//div[@class="post-single-content box mark-links"]/descendant::img').extract()
        for img_index,img_item in enumerate(img):
            new_img = re.sub(r'pagespeed_lazy_src=(\"[^\"]+\")([^>]+src=)(\"[^\"]+\")',r'pagespeed_lazy_src=\3\2\1',img_item)
            item['message'] = item['message'].replace(img_item,new_img)
        #过滤
        post_page_number = sel.xpath('//div[@class="post-page-number"]').extract()[0]
        item['message'] = item['message'].replace(post_page_number,'')
        
        mid_post_ad_list = sel.xpath('//div[@class="mid-post-ad"]').extract()
        for mid_post_ad in mid_post_ad_list:
            item['message'] = item['message'].replace(mid_post_ad,'')
        script_list = sel.xpath('//div[@class="post-single-content box mark-links"]/descendant::script').extract()
        for script in script_list:
            item['message'] = item['message'].replace(script,'')

        item['message'] = re.sub(u'<p[^<]+來源：[^<]+</p>','',item['message'])
        item['message'] = re.sub(u'<div[^<]+來源：[^<]+</div>','',item['message'])
        item['message'] = re.sub(u'<div[^<]+來源：[^<]+<a[^<]+</a>[^<]+</div>','',item['message'])
        return item
