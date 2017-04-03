"""
Easy-Job worker based on python multithreading and Queue
This backend doesn't have any configuration option

"""
from easy_job.workers.common import call_with_retry, empty_callback
from . import BaseInitializer, BaseRunner
import logging
from queue import Empty
import os
import time
from easy_job.workers.mixins import LoggerMixin, StoreResultMixin

__author__ = 'Apollo'


class MTQueueWorker(StoreResultMixin):
    def __init__(self, queue, *args, **options):
        self.log(logging.DEBUG, "MTQueueWorker.__init__")
        self.queue = queue
        self.log(logging.DEBUG, "MTQueueWorker.__init__ , queue is {}->{}".format(queue, type(queue)))
        self.log(logging.DEBUG, "MTQueueWorker.__init__ , args is {}->{}".format(args, type(args)))
        self.log(logging.DEBUG, "MTQueueWorker.__init__ , options is {}->{}".format(options, type(options)))

        super(MTQueueWorker, self).__init__(*args, **options)

    def callback(self, body):
        self.log(logging.DEBUG, "MTQueueWorker.callback")
        self.log(logging.DEBUG, "MTQueueWorker.callback , the body parameter is {}->{}".format(body, type(body)))
        from django.utils.module_loading import import_string
        try:
            function_dot_path, parameters = body['function'], body['parameters']
            args, kwargs = parameters['args'], parameters['kwargs']
            retry_policy = parameters.get('retry_policy', None)
            function = import_string(function_dot_path)
            self.log(logging.DEBUG, "MTQueueWorker.callback , function to run {}->{}".format(function, type(function)))
            if callable(function):
                self.log(logging.DEBUG, "MTQueueWorker.callback , {} is callable let's run it".format(function))
                before = time.time()
                if retry_policy is not None:
                    result = call_with_retry(function, args, kwargs, retry_policy)
                else:
                    result = function(*args, **kwargs)
                time_to_complete = time.time() - before
                callback_descriptor = parameters.get('callback', {})
                try:
                    callback_function = import_string(callback_descriptor['function'])
                except:
                    callback_function = empty_callback
                callback_args = callback_descriptor.get('args', tuple())
                callback_kwargs = callback_descriptor.get('kwargs', {})
                callback_kwargs.update(
                    {
                        'result': result,
                        'logger': self._logger
                    }
                )
                self.store_result(function_dot_path, callback_function(*callback_args, **callback_kwargs))
            else:
                self.log(logging.DEBUG, "MTQueueWorker.callback , {} isn't callable ".format(function))
                raise ValueError("{} is not callable".format(function_dot_path))
            self.log(logging.DEBUG, "{} finished in {} seconds ".format(function_dot_path, time_to_complete))
        except Exception as exp:
            self.log(logging.DEBUG, "MTQueueWorker.callback: Some error happened: {}".format(str(exp)))
            self.log(logging.ERROR, body, exception=exp, include_traceback=True)

    def run(self):
        self.log(logging.DEBUG, "we are inside the created thread : {}".format(os.getpid()))
        self.log(logging.DEBUG, "Running the MTQueue worker: {}".format(os.getpid()))
        self.log(logging.DEBUG, "getting into a Loop")
        while True:
            try:
                task = self.queue.get(timeout=2)
                self.log(logging.DEBUG, "MTQueueWorker.run() -> TASK REACH THE WORKER")
                self.log(logging.DEBUG, "MTQueueWorker.run() -> task is {}, {}".format(task, type(task)))
                self.callback(task)
            except Empty:
                self.log(logging.DEBUG, "MTQueueWorker.run() -> in task in last 2 sec")
                pass


class MTQueueInitializer(BaseInitializer):
    def start(self, no_runner=False):
        from threading import Thread
        from queue import Queue
        logging.getLogger(self.logger).log(logging.DEBUG, "MTQueueInitializer.start, lets initialize")
        queue = Queue()
        logging.getLogger(self.logger).log(logging.DEBUG,
                                           "queue object has been created : {} -> {}".format(queue, type(queue)))
        logging.getLogger(self.logger).log(logging.DEBUG, "Starting {} MTQueue workers...".format(self.count))
        if not no_runner:
            logging.getLogger(self.logger).log(logging.DEBUG, "MTQueueInitializer.start()::creating workers ...")
            for process_index in range(self.count):
                worker_instance = MTQueueWorker(
                    result_backend=self.result_backend,
                    queue=queue,
                    logger=self.logger,
                    **self.options
                )
                logging.getLogger(self.logger).log(logging.DEBUG, "worker instance has been created : {} - > {}".format(
                    worker_instance, type(worker_instance)))
                logging.getLogger(self.logger).log(logging.DEBUG,
                                                   """worker params are :
                                                    result_backend={} -> {}
                                                    queue={} -> {}
                                                    logger={} -> {}
                                                    other options :
                                                    {}
                                                   """.format(
                                                       self.result_backend, type(self.result_backend, ),
                                                       queue, type(queue),
                                                       self.logger, type(self.logger),
                                                       self.options
                                                   ))
                logging.getLogger(self.logger).log(logging.DEBUG, "creating thread")
                t = Thread(
                    target=lambda x: x.run(),
                    args=(worker_instance,)
                )
                logging.getLogger(self.logger).log(logging.DEBUG, "thread created : {} -> {}".format(t, type(t)))
                t.daemon = True
                t.start()
        else:
            logging.getLogger(self.logger).log(logging.DEBUG, "No runner is available !!!")
        return MTQueueRunner(queue=queue, logger=self.logger)


class MTQueueRunner(LoggerMixin, BaseRunner):
    def __init__(self, queue, *args, **kwargs):
        self.log(logging.DEBUG, "MTQueueRunner Initializer")
        self.log(logging.DEBUG, "MTQueueRunner Initializer args : {}".format(args))
        self.log(logging.DEBUG, "MTQueueRunner Initializer kwargs: {}".format(kwargs))
        self.log(logging.DEBUG, "MTQueueRunner Initializer Queue Parameter is : {}".format(queue))
        self.log(logging.DEBUG, "MTQueueRunner Initializer Queue Parameter is [type]: {}".format(type(queue)))

        self.queue = queue
        self.log(logging.DEBUG, "MTQueue Runner is ready...")
        super(MTQueueRunner, self).__init__(*args, **kwargs)

    def run(self, function, args=None, kwargs=None, retry_policy=None, callback=None):
        self.log(logging.DEBUG, "MTQueueRunner run() function has been called with :")
        self.log(logging.DEBUG, "MTQueueRunner run() -> function is {}".format(function))
        self.log(logging.DEBUG, "MTQueueRunner run() -> args is {}".format(args))
        self.log(logging.DEBUG, "MTQueueRunner run() -> kwargs is {}".format(kwargs))
        self.log(logging.DEBUG, "MTQueueRunner run() -> retry_policy is {}".format(retry_policy))
        self.log(logging.DEBUG, "MTQueueRunner run() -> callback is {}".format(callback))

        self.queue.put({
            "function": function,
            "parameters": {
                "args": args or tuple(),
                "kwargs": kwargs or {},
                "retry_policy": retry_policy,
                "callback": callback or {},
            }
        })
        self.log(logging.DEBUG, "Task received : {} , Queue size : {}".format(function, self.queue.qsize()))
