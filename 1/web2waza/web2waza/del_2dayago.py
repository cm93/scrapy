#! -*- encoding:utf-8 -*-
import os
import web2waza.settings
import sys
from datetime import timedelta, date


root_path = web2waza.settings.root_path
if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

dayago = date.today()-timedelta(2)
year = dayago.year
month = dayago.month
day = dayago.day
dayago_path = root_path+'/crawler_waza/web2waza/imgs/'+str(year)+str(month)+str(day)


if  os.path.exists(dayago_path):
    os.rmdir(dayago_path)
    print '成功删除'+dayago_path+'\r\n\r\n'
else:
    print dayago_path,'不存在','\r\n\r\n'
