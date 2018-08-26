#_*_coding:utf-8_*_

from ..conf import configs,registered_modules
import pika
import platform
import subprocess
import json,threading
from ..modules import files


class CommandManagement(object):
    def __init__(self,argvs):
        self.argvs = argvs[1:]
        self.argv_handler()

    def argv_handler(self):
        if len(self.argvs) == 0:
            exit("argument: start\stop")
        if hasattr(self,self.argvs[0]):
            func = getattr(self,self.argvs[0])
            func()
        else:
            exit("invalid argument.")

    def start(self):
        client_obj = Needle()
        client_obj.listen()

    def stop(self):
        pass


class TaskHandle(object):
    def __init__(self, main_obj, task_body):
        self.main_obj = main_obj
        self.task_body = json.loads(task_body.decode())

    def processing(self):
        '''
        process task
        :return:
        '''
        check_res = self.check_data_validation()
        if check_res:
            self.current_os_type, data = check_res
            self.parse_task_data(self.current_os_type, data)

    def check_data_validation(self):
        '''
        确保服务器发来的任务是在本客户端上可以执行的
        :return:
        '''

        print('----parse task ----')
        os_version = platform.version().lower()
        # print(self.task_body['data'])
        for os_type, data in self.task_body['data'].items():
            print(os_version, os_type)
            if os_type in os_version:  # should be in , only for test
                print(os_type, data)
                return os_type, data
                # break
        else:
            print("\033[31;1msalt is not supported on this os \033[0m", os_version)

    def parse_task_data(self, os_type, data):
        '''
        解析任务数据并执行
        :param os_type:
        :param data:
        :return:
        '''

        applied_list = []  # 所有已经执行了的子任务(section)都放在这个列表里
        applied_result = []  # 把所有应用的section的执行结果放这里面
        last_loop_section_set_len = len(applied_list)
        while True:
            for section in data:
                if section.get('called_flag'):  # 代表已执行过了
                    print('------------------------------called already ')
                    # break
                else:
                    apply_status, result = self.apply_section(section)
                    if apply_status == True:  # 代表执行成功
                        applied_list.append(section)
                        applied_result += result

            if len(applied_list) == last_loop_section_set_len:
                # 这两个变量相等,代表2种可能, 要么是都执行完了,要么是依赖关系形成了死锁
                print('done'.center(60, '*'), len(applied_list), last_loop_section_set_len)
                print(applied_list)
                print(applied_result)
                break
            last_loop_section_set_len = len(applied_list)

        # 接下来把执行结果返回给服务器
        print('\033[42;1msend task result to task callback queue:\033[0m', self.task_body['callback_queue'])
        self.task_callback(self.task_body['callback_queue'], applied_result)

    def apply_section(self, section_data):
        '''
        执行指定的task section
        :return:
        '''

        print("\033[32;1mapplying section\033[0m".center(50, '-'))
        if section_data['require_list'] != None:
            # 检测requsite条件是否满足
            if self.check_pre_requisites(section_data['require_list']) == 0:  # 依赖满足
                if section_data.get('file_module') == True:  # 文件section需要单独处理
                    res = self.file_handle(section_data)
                else:
                    res = self.run_cmds(section_data['cmd_list'])
                section_data['called_flag'] = True
                return [True, res]
            else:
                print("\033[33;1m依赖不满足\033[0m")
                return [False, None]  # 依赖不满足
        else:  # 没依赖要求,直接执行
            if section_data.get('file_module') == True:  # 文件section需要单独处理
                res = self.file_handle(section_data)
            else:
                res = self.run_cmds(section_data['cmd_list'])

            section_data['called_flag'] = True
            return [True, res]

    def check_pre_requisites(self, conditions):
        '''
        检测依赖条件是否成立
        :return:
        '''

        print('----check pre requisites:')
        condition_results = []
        for condition in conditions:
            print(condition)

            cmd_res = subprocess.run(condition, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            condition_results.append(int(cmd_res.stdout.read().decode().strip()))

        print('\033[41;1mcmd res:\033[0m', condition_results)
        return sum(condition_results)  # 所有命令如果执行成功,返回是0

    def task_callback(self, callback_queue, callback_data):
        '''
        把任务执行结果返回给服务器
        :param callback_queue:
        :param callback_data:
        :return:
        '''

        data = {
            'client_id': self.main_obj.client_id,
            'data': callback_data
        }

        # 声明queue
        self.main_obj.mq_channel.queue_declare(queue=callback_queue)
        # n RabbitMQ a message can never be sent directly to the queue, it always needs to go through an exchange.
        self.main_obj.mq_channel.basic_publish(exchange='',
                                               routing_key=callback_queue,
                                               body=json.dumps(data))
        print(" [x] Sent task callback to [%s]" % callback_queue)

    def run_cmds(self, cmd_list):
        '''
        运行命令,返回结果
        :param cmd_list:
        :return:
        '''
        cmd_results = []
        for cmd in cmd_list:
            print(cmd)
            # run方法是python3.5才有的
            cmd_res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd_results.append([cmd_res.returncode, cmd_res.stderr.read().decode()])

        print('\033[41;1mcmd res:\033[0m', cmd_results)
        return cmd_results  # 所有命令如果执行成功,返回是0

    def file_handle(self, section_data):
        '''
        对文件进行操作
        :param section_data:
        :return:
        '''

        file_module_obj = files.FileModule(self)
        file_module_obj.process(section_data)
        return []


class Needle(object):
    def __init__(self):
        self.configs = configs
        self.make_connection()
        self.client_id = self.get_needle_id()
        self.task_queue_name = "TASK_Q_%s" % self.client_id

    def get_needle_id(self):
        '''
        去服务器端取自己的id
        :return:
        '''
        return configs.NEEDLE_CLIENT_ID

    def listen(self):
        '''
        开始监听服务器的call
        :return:
        '''
        self.msg_consume()

    def make_connection(self):
        credentials = pika.PlainCredentials('guset', 'guest')
        self.mq_conn = pika.BlockingConnection(pika.ConnectionParameters(
            configs.MQ_CONN['host'],
            configs.MQ_CONN['port'],
            '/',
            credentials))
        self.mq_channel = self.mq_conn.channel()

    def publish(self, data):
        print('\033[41;1m-----going to publish msg ------\033[0m', data)

        # 声明queue
        self.mq_channel.queue_declare(queue='hello')
        # n RabbitMQ a message can never be sent directly to the queue, it always needs to go through an exchange.
        self.mq_channel.basic_publish(exchange='',
                                      routing_key='hello',
                                      body='Hello World!')
        print(" [x] Sent 'Hello World!'")
        self.mq_conn.close()

    def msg_callback(self, ch, method, properties, body):
        print(" [x] Received a task msg 每一个任务都起一个单独的线程", body)
        thread = threading.Thread(target=self.start_thread, args=(body,))
        thread.start()

    def start_thread(self, task_body):
        print('\033[31;1m start a thread to process task\033[0m')
        task = TaskHandle(self, task_body)
        task.processing()

    def msg_consume(self):
        self.mq_channel.queue_declare(queue=self.task_queue_name)

        # def callback(ch, method, properties, body):
        #    print(" [x] Received %r" % body)

        # 回调函数 self.msg_callback，来了新消息，就调用
        self.mq_channel.basic_consume(self.msg_callback,
                                      queue=self.task_queue_name,
                                      no_ack=True)

        print(' [%s] Waiting for messages. To exit press CTRL+C' % self.task_queue_name)
        self.mq_channel.start_consuming()