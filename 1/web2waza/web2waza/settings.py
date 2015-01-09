import os
from time import strftime, localtime
year = strftime("%Y",localtime())
mon  = strftime("%m",localtime())
day  = strftime("%d",localtime())



root = 'http://www.wazafee.com'
root_path = '/home/ray/html'
img_web_url = 'http://ci.wazafeecdn.com/'
xiangdui_path = '/crawler_waza/web2waza/imgs/' + year+mon+day
imgs_path = root_path + xiangdui_path
imgs_path_full = imgs_path + '/full'
if not os.path.exists(imgs_path_full):
    os.mkdir(imgs_path)
    os.mkdir(imgs_path_full)
local_img_url = img_web_url + year+mon+day

wget_path = root_path + '/crawler_waza/web2waza/wget.log'

BOT_NAME = 'web2waza'

SPIDER_MODULES = ['web2waza.spiders']
NEWSPIDER_MODULE = 'web2waza.spiders'

ITEM_PIPELINES = {
    'web2waza.pipelines.Web2WazaPipeline':300,\
    'scrapy.contrib.pipeline.images.ImagesPipeline':1,\
}
IMAGES_STORE =imgs_path


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'life2wazafee (+http://www.yourdomain.com)'
