#!/usr/bin/env python
# -*- coding:utf-8 -*-

from Arya.backends.base_module import BaseSaltModule


class User(BaseSaltModule):

    def uid(self,*args,**kwargs):
        cmd = '-u %s ' %args[0]
        self.raw_cmds.append(cmd)

    # def gid(self,*args,**kwargs):
    #     cmd = '-g %s ' %args[0]
    #     self.raw_cmds.append(cmd)


    def shell(self,*args,**kwargs):
        cmd = '-s %s ' %args[0]
        self.raw_cmds.append(cmd)


    def home(self,*args,**kwargs):
        cmd = '-d %s ' % args[0]
        self.raw_cmds.append(cmd)

    def password(self,*args,**kwargs):
        username = kwargs.get('section')
        password = args[0]
        cmd = '''echo "%s:%s" | chpasswd ''' % (username, password)
        self.single_line_cmds.append(cmd)

    def is_required(self, *args, **kwargs):
        pass

    def present(self, *args,**kwargs):
        cmd_list = []
        username = kwargs.get('section')
        self.raw_cmds.insert(0, "useradd %s " %username)
        cmd_list.append(''.join(self.raw_cmds))
        cmd_list.extend(self.single_line_cmds)
        print("cmd_list",cmd_list)
        return  cmd_list
        # print("raw_cmds", self.raw_cmds)
        # print("single_line_cmds", self.single_line_cmds)

class UbuntuUser(User):
    def uid(self, *args, **kwargs):
        print("系统类型为ubuntu:", *args)

    def gid(self, *args, **kwargs):
        print("系统类型为ubuntu:", *args)

    def shell(self, *args, **kwargs):
        print("系统类型为ubuntu:", *args)

    def home(self, *args, **kwargs):
        print("系统类型为ubuntu:", *args)

    # def require(self, *args, **kwargs):
    #     print("系统类型为ubuntu:", *args)

