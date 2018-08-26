from Arya.action_list import actions
import django
django.setup()

from Stark import settings
from Arya import models

class ArgvManagement(object):
    '''
    接收用户指令并分配到相应模块
    '''

    def __init__(self, argvs):
        self.argvs = argvs
        self.argv_parse()

    def help_msg(self):
        print("Available modules:")
        for module in actions:
            print("  %s" % module)
        exit()

    def argv_parse(self):
        # print(self.argvs)
        if len(self.argvs) < 2:
            self.help_msg()
        module_name = self.argvs[1]
        if '.' in module_name:  #state.apply
            mod_name, mod_method = module_name.split('.')
            module_instance = actions.get(mod_name)
            if module_instance:
                module_obj = module_instance(self.argvs, models, settings)  #把参数交给了相应的模块，这里执行state.State()
                module_obj.process()  # State继承的基类，负责提取主机信息和操作系统类型,返回一个self.host_list、data(系统信息)
                if hasattr(module_obj, mod_method):
                    module_method_obj = getattr(module_obj, mod_method)
                    module_method_obj() #例如执行State.apply()
                else:
                    exit("module [%s] doesn't have [%s] method" % (mod_name, mod_method))
            else:
                exit("没有此模块")
        else:
            exit("模块名错误")
