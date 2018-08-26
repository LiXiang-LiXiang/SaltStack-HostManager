#_*_coding:utf-8_*_

import pika,json

class TaskHandle(object):
    '''
    generate task
    '''
    def __init__(self,db_model,task_data,settings,module_obj):
        self.db_model = db_model
        self.task_data = task_data
        self.settings = settings
        self.module_obj = module_obj
        self.make_connection()

    def make_connection(self):

        self.mq_conn = pika.BlockingConnection(pika.ConnectionParameters(
                       self.settings.MQ_CONN['host']))
        self.mq_channel = self.mq_conn.channel()


    def apply_new_task(self):
        '''
        create a task record in db and return the task id
        :return:
        '''

        new_task_obj = self.db_model.Task()
        new_task_obj.save()
        self.task_id = new_task_obj.id
        return True
    def dispatch_task(self):
        '''
        format the task data and make it ready to sent
        :return:
        '''
        if self.apply_new_task():
            #在服务器端将任务发送给客户端监听的队列时，也马上去监听callback_queue
            print('send task to :',self.module_obj.host_list)
            #这个队列有两个作用：1.服务端从这取消息；2.客户端执行结果发到这
            self.callback_queue_name = "TASK_CALLBACK_%s" % self.task_id
            data = {
                'data':self.task_data,
                'id': self.task_id,
                'callback_queue': self.callback_queue_name,
                'token':None
            }

            for host in self.module_obj.host_list:
                self.publish(data, host)  #发布任务，发送数据到队列，将主机id作为队列名

            #开始等待任务结果,由生产者转换为消费者
            self.wait_callback()

    def publish(self,task_data,host):
        print('\033[41;1m-----going to publish msg ------\033[0m;\n')

        #声明服务器将消息发向的队列
        queue_name = 'TASK_Q_%s' % host.id
        self.mq_channel.queue_declare(queue=queue_name)

        print("task_data是什么",json.dumps(task_data).encode())

        #n RabbitMQ a message can never be sent directly to the queue, it always needs to go through an exchange.
        self.mq_channel.basic_publish(exchange='',
                              routing_key=queue_name,
                              body= json.dumps(task_data))
        print(" Server Sent task to queue [%s] 'Hello World!'" % queue_name)

    def close_connection(self):
        self.mq_conn.close()

    def task_callback(self,ch, method, properties, body):
        print("有新消息了就打印", body)

    def wait_callback(self):
        '''
        get task callback
        :return:
        '''
        #print('------waiting for callback from :' ,self.callback_queue_name)

        self.mq_channel.queue_declare(queue=self.callback_queue_name)
        #服务器端在这里消费返回的信息，no_ack=True意思是不用告诉客户端，我是否收到消息了
        self.mq_channel.basic_consume(self.task_callback,
                              queue=self.callback_queue_name,
                              no_ack=True)

        print('\033[42;1m[%s] Waiting for callback. To exit press CTRL+C\033[0m' % self.callback_queue_name)
        self.mq_channel.start_consuming()