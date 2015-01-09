#! /usr/local/lib/python2.7
#! -*- encoding:utf-8 -*-
import redis

rdis = redis.Redis(host='127.0.0.1', port=6379, db=1)
#rdis.delete('web2waza')
lenth = rdis.llen('web2waza')
print 'redis长度: %d'%lenth
