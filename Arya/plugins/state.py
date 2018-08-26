from Arya.backends.base_module import BaseSaltModule
import os
from Arya.backends import tasks


class State(BaseSaltModule):

    def load_state_files(self,state_filename):
        from yaml import load, dump
        try:
            from yaml import CLoader as Loader, CDumper as Dumper
        except ImportError:
            from yaml import Loader, Dumper
        state_file = "%s/%s" %(self.settings.SALT_CONFIG_FILES_DIR,state_filename)
        if os.path.isfile(state_file):
            with open(state_file) as f:
                data = load(f.read(), Loader=Loader)
                return data
        else:
            exit("%s 不是一个合法的yaml文件" % state_filename)

    def apply(self):
        '''1. load yml文件  2. parse it 3.创建任务发送到MQ， 4.收集结果with task-callback id'''

        if '-f' in self.sys_argvs:
            yaml_file_index = self.sys_argvs.index('-f') + 1
            try:
                yaml_filename = self.sys_argvs[yaml_file_index]
                state_data = self.load_state_files(yaml_filename)
                # print('state data:', state_data)

                for os_type, os_type_data in self.config_data_dic.items():
                    # 按照不同的操作系统生成不同配置文件，操作系统相同，执行的命令也就相同
                    # print("\t系统类型",os_type)
                    for section_name, section_data in state_data.items():
                        # print('Section(部分名):', section_name)
                        #mod_name类似于user.present、group.present,下面的两个print可以不用
                        for mod_name, mod_data in section_data.items():
                            # print("模块名", mod_name)
                            # for state_item in mod_data:
                            #     print("\t", state_item)
                            base_mod_name = mod_name.split(".")[0]
                            #在这里根据字符串，拿到具体的模块,诸如user.User、group.Group的类
                            module_obj = self.get_module_instance(base_mod_name=base_mod_name,os_type=os_type)
                            module_parse_result = module_obj.syntax_parser(section_name, mod_name, mod_data, os_type) #用mod_data映射具体的uid、gid方法
                            self.config_data_dic[os_type].append(module_parse_result)
                # print("config_data_dic".center(60,'*'))
                print("config_data_dic是什么", self.config_data_dic)
                print("self是state.State()...",self)
                #这里把self实例传进去，是为了获得host_list信息，self在那个模块里，self就是谁
                new_task_obj = tasks.TaskHandle(self.db_models,self.config_data_dic,self.settings,self)
                new_task_obj.dispatch_task()
            except IndexError as e: #超出边界了
                exit("state file must be provided after -f")
        else:
            exit("statefile必须提供")