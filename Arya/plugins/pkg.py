#!/usr/bin/env python
# -*- coding:utf-8 -*-

from Arya.backends.base_module import BaseSaltModule


class Pkg(BaseSaltModule):

    def is_required(self, *args, **kwargs):
        cmd = "rpm - qa | grep %s ; echo $?" %args[0]
        return cmd
