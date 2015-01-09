#! /usr/local/lib/python2.7
#! -*- encoding:utf-8 -*-
import re
import codecs
import json
import redis
import sys
import time
import os
import random
import requests
import web2waza.settings as settings
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


def encode_multipart_formdata(fields):
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields.items():
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    return body

#登录
def login():
    s = requests.session()
    um = ['Supersg','penguin9743','fukyouu','ac915617','songood','Zcio9112','Lacues082','finzaghhi','f22222s','arrrenw','cywgtw1990','koiopolo1','gdaiven','wuofjoa','qwertty183','ZERO3','colin112008','when970505','TFboys','SuperStar','seaya1991','ithill1','bbcbbdbili','dack0833','eight88088','mhnci','htppbbs','jasonn68979','nnnnn1nnnn','wwwwww','OMG321','picturecute','Rose2333','ssssexyON1','yesshi444','kkkkkkk','puhahah5','minico11','sayaka521','Naluto999']
    username = um[random.randint(0,33)]
    try:
        #hash_url ='http://dz.wazafee.com/member.php?mod=logging&action=login&goto=%s/'%root
        hash_url ='http://dz.gc.85pay.net/member.php?mod=logging&action=login&goto=%s/'%root
        r = s.get(hash_url)
        formhash = re.findall('<input type="hidden" name="formhash" value="([\w\d]+)" />',r.text)[0]
    except:
        return
    #formdata={'username': username,\
    #formdata={'username': 'KEN',\
    formdata={'username': 'merr',\
        'password': 'iloveallen',\
        'formhash': formhash,\
        'goto':root,\
        'refer':'forum.php',}
    #logurl = 'http://dz.wazafee.com/member.php?mod=logging&action=login&loginsubmit=yes&loginhash=LU70I&inajax=1'
    logurl = 'http://dz.gc.85pay.net/member.php?mod=logging&action=login&loginsubmit=yes&loginhash=LU70I&inajax=1'
    logr = s.post(logurl, data = formdata)
    dict_cookie =  dict(logr.cookies)
    #redirect_url = re.findall('http://user.wazafee.com/public/api/useruc.php[^\"\']+',logr.text)[0] 
    redirect_url = re.findall('http://jason.wazafee.com/public/api/uc.php[^\"\']+',logr.text)[0]
    iTiQ_r = s.get(redirect_url)
    return iTiQ_r.cookies


#发文
global root
root  = settings.root
rdis = redis.Redis(host='127.0.0.1', port=6379, db=1)
#rdis.delete('web2waza')
lenth = rdis.llen('web2waza')
print 'redis长度: %d'%lenth
if lenth == 0 :
    print '没有redis数据'
    os._exit(0)
for i in xrange(0, 3):
#for i in xrange(0, lenth):
    line = rdis.rpop('web2waza')
    data = json.loads(line)
    for k,v in data.items():
        num = 1
        if type(data[k]) != type(num):
            data[k] = v.encode('utf-8')
    if len(data['message'])<1200:
        continue
    if data['keytype'] == 1:
        check_api = requests.get('%s/crawapi/check/%d/%d/%d'%(root,int(data['artile_id_key']),int(data['ori_web']),1)).text
    else:
        check_api = requests.get('%s/crawapi/check/%s/%d/%d'%(root,data['artile_id_key'],int(data['ori_web']),2)).text
    check_dict = eval(check_api.encode('utf-8'))
    if check_dict['status']:
        print check_dict['data']['ourl'].replace('\\','')
        print '文章已经存在:' +root+'/dashboard/editArticle/'+ check_dict['data']['aid'].replace('\\','')+'\r\n'
        continue
    logr_cookies = login()
    formdata={'row[originalurl]':data['fromurl'],\
               'row[title]':data['subject'],\
               'row[summary]':data['desc'],\
               'row[cover]':data['cover'],\
               'row[content]':data['message'],\
               'row[cate]':data['typeid'],\
               'row[tags]':data['tags'],\
               'row[share_profit]':'0',\
               'row[is_adult]':'0',\
               'row[verify]':'1',\
               'row[aid]':'0'}
    #posturl_r = requests.post('http://user.wazafee.com/dashboard/postcreate',data = encode_multipart_formdata(formdata),headers = {'Content-Type':'multipart/form-data; boundary=----------ThIs_Is_tHe_bouNdaRY'},cookies=logr_cookies)
    posturl_r = requests.post('http://jason.wazafee.com/dashboard/postcreate',data = encode_multipart_formdata(formdata),headers = {'Content-Type':'multipart/form-data; boundary=----------ThIs_Is_tHe_bouNdaRY'},cookies=logr_cookies)
    print data['fromurl']
    aurl = re.findall('<meta property=\"og:url\" content=\"([^\"]+)\"',posturl_r.text)[0]
    aid = re.findall('/(\d+)',aurl)[-1]
    formdata={"row[siteid]" : data['ori_web'],\
              "row[keytype]" : int(data['keytype']),\
              "row[ourl]" : data['fromurl'],\
              "row[title]":data['subject'],\
              "row[aid]" : int(aid),\
    }
    if data['keytype'] == 1:
        formdata["row[oid]"] =  data['artile_id_key']
    else:
        formdata["row[okey]"] = data['artile_id_key']
    insert_api = requests.post('%s/crawapi/insert'%root,data = formdata).text
    insert_dict = eval(insert_api)
    inser_status = insert_dict['status']
    if inser_status:
        print '添加映射成功,文章:'+ aurl + '\r\n'
    else:
        print '添加映射失败,文章:'+ aurl +'\r\n'
    time.sleep(5)
