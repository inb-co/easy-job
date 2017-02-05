"""
Easy-Job worker based on python multiprocessing Queue
available options to use
    * process_name_template: a template to create process names , you can use {index} in naming processes
        default: MPQueueProcess_{index}

"""
from easy_job.workers.common import call_with_retry
from . import BaseInitializer, BaseRunner
import logging
from queue import Empty
import os
import time
from easy_job.workers.mixins import LoggerMixin, StoreResultMixin

__author__ = 'Apollo'


def worker(worker_instance):
    worker_instance.run()


class MPQueueWorker(StoreResultMixin):
    def __init__(self, queue, *args, **options):
        self.queue = queue
        super(MPQueueWorker, self).__init__(*args, **options)

    def callback(self, body):
        from django.utils.module_loading import import_string
        try:
            function_dot_path, parameters = body['function'], body['parameters']
            args, kwargs = parameters['args'], parameters['kwargs']
            retry_policy = parameters.get('retry_policy', None)
            callback = parameters.get('callback', None)
            function = import_string(function_dot_path)
            if callable(function):
                before = time.time()
                if retry_policy is not None:
                    result = call_with_retry(function, args, kwargs, retry_policy)
                else:
                    result = function(*args, **kwargs)
                time_to_complete = time.time() - before
                if callback is None:
                    self.store_result(function_dot_path, result)
                else:
                    callback_function = import_string(callback['function'])
                    callback_args = callback.get('args', tuple())
                    callback_kwargs = callback.get('kwargs', {})
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
            self.log(logging.ERROR, body, exp, include_traceback=True)

    def run(self):
        self.log(logging.DEBUG, "Running the MPQueue worker: {}".format(os.getpid()))
        while True:
            try:
                self.callback(self.queue.get(timeout=2))
            except Empty:
                pass


class MPQueueInitializer(BaseInitializer):
    def start(self, no_runner=False):
        from multiprocessing import Process, Queue
        queue = Queue()
        logging.getLogger(self.logger).log(logging.DEBUG, "Starting {} MPQueue workers...".format(self.count))
        if not no_runner:
            for process_index in range(self.count):
                process_name = self.options.pop('process_name_template',
                                                "MPQueueProcess_{index}").format(index=process_index)
                worker_instance = MPQueueWorker(
                    result_backend=self.result_backend,
                    queue=queue,
                    logger=self.logger,
                    **self.options
                )
                p = Process(
                    name=process_name,
                    target=worker,
                    args=(worker_instance,)
                )
                p.daemon = True
                p.start()
        return MPQueueRunner(queue=queue, logger=self.logger)


class MPQueueRunner(LoggerMixin, BaseRunner):
    def __init__(self, queue, *args, **kwargs):
        self.queue = queue
        self.log(logging.DEBUG, "MPQueue Runner is ready...")
        super(MPQueueRunner, self).__init__(*args, **kwargs)

    def run(self, function, args=None, kwargs=None, retry_policy=None, callback=None):
        self.queue.put({
            "function": function,
            "parameters": {
                "args": args or tuple(),
                "kwargs": kwargs or {},
                "retry_policy": retry_policy,
                "callback": callback,
            }
        })
        self.log(logging.DEBUG, "Task received : {} , Queue size : {}".format(function, self.queue.qsize()))
