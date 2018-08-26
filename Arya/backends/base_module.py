import os


class BaseSaltModule(object):

    def __init__(self, sys_argvs, db_models, settings):
        self.sys_argvs = sys_argvs
        self.db_models = db_models
        self.settings = settings

    def argu_valid_check(self,argument, value, data_type):
        if type(value) is not data_type:
            exit("Error:[%s]'s data_type is not valid" % argument)

    def process(self):  #作用：继承BaseSaltModule的类，不主动调用，就不执行process，也就是不返回主机等信息
        self.host_list = self.fetch_hosts()
        self.config_data_dic = self.get_selected_os_types()

    def get_selected_os_types(self): #获取主机操作系统类型
        data = {}
        for host in self.host_list:
            data[host.os_type] = []
        print('--->主机操作系统类型及执行命令列表', data)
        return data



    def fetch_hosts(self): #获取主机或主机组详细信息
        # print("self.sys_argvs", self.sys_argvs)
        if '-h' in self.sys_argvs or '-g' in self.sys_argvs:
            host_list = []
            if '-h' in self.sys_argvs:
                host_str_index = self.sys_argvs.index('-h') + 1
                if len(self.sys_argvs) <= host_str_index:
                    exit("host argument must be provided after -h")
                else:  # get the host str
                    host_str = self.sys_argvs[host_str_index]
                    host_str_list = host_str.split(',')
                    host_list += self.db_models.Host.objects.filter(hostname__in=host_str_list)
            if '-g' in self.sys_argvs:
                group_str_index = self.sys_argvs.index('-g') + 1
                if len(self.sys_argvs) <= group_str_index:
                    exit("group argument must be provided after -g")
                else:  # get the group str
                    group_str = self.sys_argvs[group_str_index]
                    group_str_list = group_str.split(',')
                    group_list = self.db_models.HostGroup.objects.filter(name__in=group_str_list)
                    for group in group_list:
                        host_list += group.hosts.select_related()
            self.host_list = set(host_list)
            print('----主机列表:', self.host_list)
            return self.host_list
        else:
            exit("主机 [-h] 或 主机组 [-g] 参数必须提供")

    def get_module_instance(self, *args, **kwargs):
        # 根据字符串从plugins目录导入对应的文件
        base_mod_name = kwargs.get("base_mod_name")
        os_type = kwargs.get("os_type")
        plugin_file = "%s/%s.py" % (self.settings.SALT_PLUGINS_DIR, base_mod_name)
        if os.path.isfile(plugin_file):
            # 对不是redhat系统的主机做特殊处理
            special_os_module_name = "%s%s" % (os_type.capitalize(), base_mod_name.capitalize())
            # 根据字符串从plugins目录导入对应的文件
            module_plugin = __import__('plugins.%s' % base_mod_name)
            module_file = getattr(module_plugin, base_mod_name)  # 真正导入模块 相当于import plugins.user

            if hasattr(module_file, special_os_module_name):  # 根据操作系统的类型进行特殊解析的类，
                module_instance = getattr(module_file, special_os_module_name)
            else:
                module_instance = getattr(module_file, base_mod_name.capitalize())  # 执行默认是诸如user.User、group.Group的类
            # print("具体执行哪个模块去处理uid、gid之类：", module_instance)
            # print("base_mod_name", base_mod_name, "module_file", module_file)

            module_obj = module_instance(self.sys_argvs, self.db_models, self.settings)
            return module_obj
            # module_obj.syntax_parser(section_name, mod_name, mod_data)

            # syntax_parser()可以新建一个文件,将用到的mod_data传过去即可，但我就不用
        else:
            exit("module [%s] is not exist" % base_mod_name)

    def is_required(self,*args,**kwargs):
        exit("Error: is_required()方法必须出现在模块[%s]中 " %args[0])

    def require(self,*args,**kwargs):
        # print("in require:", args, type(args),kwargs, type(kwargs))
        os_type = kwargs.get("os_type")
        self.require_list = []
        #args类似于 ([{'group': 'apache'}, {'file': '/etc/httpd/conf/httpd.conf'}],)
        #取元组第一个值，第一个item是{'group': 'apache'}，第二个是{'file': '/etc/httpd/conf/httpd.conf'}
        for item in args[0]:
            # print("item是什么",item)
            for mod_name, mod_val in item.items():
                #诸如group.Group、file.File
                module_obj = self.get_module_instance(base_mod_name=mod_name, os_type=os_type)
                require_condition = module_obj.is_required(mod_val)  #如果没有is_required()就调用上面的方法，退出
                self.require_list.append(require_condition)
        print("require_list",self.require_list)
                # print("检测依赖条件的模块module_obj", module_obj)
                # print("require_list长什么样",self.require_list)

    def syntax_parser(self, section_name, mod_name, mod_data, os_type):   #apache、user.present、具体内容
        print("---%s正在解析%s的%s参数:" %(self.__class__.__name__,section_name, mod_name))
        self.raw_cmds = []
        self.single_line_cmds = []

        for Argu_To_Cmd in mod_data:
            # print("\t", Argu_To_Cmd) {'uid': 87}、{'home': '/var/www/html'}
            for key, val in Argu_To_Cmd.items():
                #self在这里是处理uid、gid参数的类,如user.User、user.UbuntuUser
                if hasattr(self, key):
                    state_func = getattr(self, key)
                    state_func(val, section=section_name, os_type=os_type)  #第一个执行require，然后执行uid、gid等拼接字符串函数
                else:
                    exit("Error:module [%s] has no [%s] method" % (mod_name, key))
        else:
        #执行完上面的for循环之后，执行这个else
        # 判断user.present在具体的类中有没有present方法
            if '.' in mod_name:
                base_mod_name,mod_action = mod_name.split('.')
                if hasattr(self, mod_action):
                    cmd_func = getattr(self, mod_action)
                    cmd_list = cmd_func(section=section_name,mod_data=mod_data)   # 如：User.present() 此函数是用来整合命令的、参数是用来获取username的
                    data = {
                        "cmd_list": cmd_list,
                        "require_list": self.require_list,
                    }
                    if type(cmd_list) is dict:
                        data['file_module'] = True
                        data['sub_action'] = cmd_list.get('sub_action')
                    #section中的一个模块已经解析完毕
                    # print("data是什么", data)
                    return data
                else:
                    exit("Error:module [%s] has no [%s] method" % (mod_name, mod_action))
            else:
                exit("Error:模块[%s]后必须提供动作" % mod_name )
















