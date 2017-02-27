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
        self.queue = queue
        super(MTQueueWorker, self).__init__(*args, **options)

    def callback(self, body):
        from django.utils.module_loading import import_string
        try:
            function_dot_path, parameters = body['function'], body['parameters']
            args, kwargs = parameters['args'], parameters['kwargs']
            retry_policy = parameters.get('retry_policy', None)
            function = import_string(function_dot_path)
            if callable(function):
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
                raise ValueError("{} is not callable".format(function_dot_path))
            self.log(logging.DEBUG, "{} finished in {} seconds ".format(function_dot_path, time_to_complete))
        except Exception as exp:
            self.log(logging.ERROR, body, exception=exp, include_traceback=True)

    def run(self):
        self.log(logging.DEBUG, "Running the MTQueue worker: {}".format(os.getpid()))
        while True:
            try:
                self.callback(self.queue.get(timeout=2))
            except Empty:
                pass


class MTQueueInitializer(BaseInitializer):
    def start(self, no_runner=False):
        from threading import Thread
        from queue import Queue
        queue = Queue()
        logging.getLogger(self.logger).log(logging.DEBUG, "Starting {} MTQueue workers...".format(self.count))
        if not no_runner:
            for process_index in range(self.count):
                worker_instance = MTQueueWorker(
                    result_backend=self.result_backend,
                    queue=queue,
                    logger=self.logger,
                    **self.options
                )
                t = Thread(
                    target=lambda x: x.run(),
                    args=(worker_instance,)
                )
                t.daemon = True
                t.start()
        return MTQueueRunner(queue=queue, logger=self.logger)


class MTQueueRunner(LoggerMixin, BaseRunner):
    def __init__(self, queue, *args, **kwargs):
        self.queue = queue
        self.log(logging.DEBUG, "MTQueue Runner is ready...")
        super(MTQueueRunner, self).__init__(*args, **kwargs)

    def run(self, function, args=None, kwargs=None, retry_policy=None, callback=None):
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
