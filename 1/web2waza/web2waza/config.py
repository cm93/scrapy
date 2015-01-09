#! -*- encoding:utf-8 -*-
import sys
import hashlib
import web2waza.settings
import os
import requests
import re
import Image


root =  web2waza.settings.root
imgs_path = web2waza.settings.imgs_path
wget_path = web2waza.settings.wget_path
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')




def wgetimg(imgurl):
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

def coverupload(imgpath):
    suffix =  imgpath.split('.')[-1].encode('utf-8')
    url = '%s/ajax/uploadimg'%root
    files = {'upfile': (imgpath, open(imgpath, 'rb'),'image/%s'%suffix)}
    formdata={'row[type]': 'article'}
    r = requests.post(url,files=files,data = formdata)
    content  = r.text
    try:
        status = content.count('\"status\":1')
        if status != 1:
            os.remove(cover_path)
            return False
    except:
        return False
    img_pre = re.findall('\"path":\"([^\'\"]+)',content)[0]
    img_pre = img_pre.replace('\\','')
    image = Image.open(imgpath)
    ow = image.size[0]
    oh = image.size[1]
    canshu = 300.0/171.0
    if ow>oh:
        sx=0.5*ow-0.5*oh
        sy=0
        sw=oh
        sh=oh
    else:
        sx=0
        sy=0.5*oh-0.5*ow
        sw=ow
        sh=ow
    if ow > canshu*oh:
        x=0.5*ow -0.5*canshu*oh
        y=0
        w=canshu*oh
        h=oh
    else:
        x=0
        y=0.5*oh - 0.5*(1.0/canshu)*ow
        w=ow
        h=(1.0/canshu)*ow
    formdata = {'type':'article',\
                'cover':img_pre,\
                'x':sx,\
                'y':sy,\
                'w':sw,\
                'h':sh,\
                'sx':x,\
                'sy':y,\
                'sw':w,\
                'sh':h}
    img_urls_r = requests.post('%s/ajax/cropimg'%root,data = formdata)
    img_urls = img_urls_r.text
    status = re.findall('\"status\":(\d)',img_urls)[0]
    if status != '1':
        return  False
    cover_name = re.findall('\"covername\":\"([^\'\"]+)',img_urls)[0]
    return cover_name
