#!/usr/bin/env python
# -*- coding:utf-8 -*-

from Arya.backends.base_module import BaseSaltModule
'''
  file.managed:
    - source: salt://apache/httpd.conf
    - user: root
    - group: root
    - mode: 644  把这些数据都装到一个列表中，交给客户端
'''


class File(BaseSaltModule):

    def source(self,*args,**kwargs):
        pass

    def user(self,*args,**kwargs):
        pass

    def group(self,*args,**kwargs):
        pass

    def mode(self,*args,**kwargs):
        pass

    def managed(self,*args,**kwargs): #最后调用managed
        print("in managed...", kwargs)
        # file_list = kwargs["mod_data"]
        # print("file_list", file_list)
        # 写这个的目的是让客户端调用对应的方法把下载好的文件放到指定位置
        kwargs['sub_action'] = 'managed'
        return kwargs

    def is_required(self, *args, **kwargs):
        file_path = args[0]
        cmd = "test -f %s ; echo $? " % file_path
        return cmd