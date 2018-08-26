#_*_coding:utf-8_*_

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SALT_MASTER = '192.168.10.10'

#文件下载方式
FILE_SERVER = {
    'http':'%s:8000' %SALT_MASTER.strip(),
    'salt':SALT_MASTER
}
#文件在服务器上的位置
FILE_SREVER_BASE_PATH = '/salt/file_center'

FILE_STORE_PATH = "%s/var/downloads/" % BASE_DIR

#客户端监听的队列的id
NEEDLE_CLIENT_ID =  1

MQ_CONN = {
    'host':'192.168.10.10',
    'port': 5672,
	'username': '',
    'password': '',
}