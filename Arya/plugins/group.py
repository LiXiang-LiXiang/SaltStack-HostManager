#!/usr/bin/env python
# -*- coding:utf-8 -*-

from Arya.backends.base_module import BaseSaltModule


class Group(BaseSaltModule):

    def gid(self,*args,**kwargs):
        cmd = '-g %s ' % args[0]
        self.raw_cmds.append(cmd)

    def is_required(self, *args, **kwargs):
        name = args[0]
        cmd = '''cat /etc/group | awk -F':' '{print $1}' | grep -w %s -q ; echo &? ''' % name
        return cmd

    def present(self, *args,**kwargs):
        cmd_list = []
        grouprname = kwargs.get('section')
        self.raw_cmds.insert(0, "groupadd %s " % grouprname)
        cmd_list.append(''.join(self.raw_cmds))
        cmd_list.extend(self.single_line_cmds)
        print("cmd_list",cmd_list)
        return  cmd_list

class UbuntuGroup(Group):

    def gid(self,*args,**kwargs):
        print("系统类型为ubuntu:", *args)
