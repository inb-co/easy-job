"""
Easy-Job worker based on RabbitMQ
available options to use
    * queue_name: name of the underlying rabbitmq queue
        default: no default value available you have to specify queue name or ValueError will be raise
    * use_threads: a boolean value indicating whether workers should be thread or process
        default: the default value is False means workers will be process
    * serialization_method: method of serializing messages before putting them in the queue , can be json or pickle
        default: json
    * rabbitmq_configs: a dictionary of rabbitmq related configurations consist of :
        * connection_pool_configs : which is another nested dictionary consist of :
            * max_size: Maximum number of connections to keep queued , default is 10
            * max_overflow: Maximum number of connections to create above `max_size`, default is 10
            * timeout: Default number of seconds to wait for a connections to available, default is 30
            * recycle: Lifetime of a connection (since creation) in seconds or None for no
                       recycling. Expired connections are closed on acquire , default is None
            * stale: Threshold at which inactive (since release) connections are
                     considered stale in seconds or None for no staleness. Stale
                     connections are closed on acquire , default is None
        * connection_parameters: which is another nested dictionary consist of parameters to send
                                to pika.ConnectionParameters

"""
from . import BaseInitializer, BaseRunner
import logging
import os
from django.utils.functional import SimpleLazyObject
import pika
import pika_pool
import time
from easy_job.workers.mixins import StoreResultMixin, LoggerMixin
from .common import call_with_retry
__author__ = 'Apollo'


def worker(worker_instance):
    worker_instance.run()


# noinspection PyDefaultArgument
class RabbitMQWorker(StoreResultMixin):
    def __init__(self, queue_name, rabbitmq_configs={}, serialization_method='json', *args, **kwargs):
        self.connection_params = rabbitmq_configs.get('connection_parameters', {})
        self.serialization_method = serialization_method
        self.queue_name = queue_name
        super(RabbitMQWorker, self).__init__(*args, **kwargs)

    def deserialize(self, body):
        if self.serialization_method == "json":
            import json
            return json.loads(body.decode('utf8'))
        elif self.serialization_method == "pickle":
            import pickle
            return pickle.loads(body)
        else:
            raise ValueError("unknown serialization_method")

    def callback(self, ch, method, properties, body):
        from django.utils.module_loading import import_string
        try:
            body = self.deserialize(body)
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
            self.log(logging.ERROR, body, exception=exp, include_traceback=True)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def run(self):
        while True:
            try:
                self.log(logging.DEBUG, "Running the RabbitMQ worker: {}".format(os.getpid()))
                with pika.BlockingConnection(pika.ConnectionParameters(**self.connection_params)) as connection:
                    channel = connection.channel()
                    channel.queue_declare(queue=self.queue_name, durable=True)
                    channel.basic_qos(prefetch_count=1)
                    channel.basic_consume(self.callback, queue=self.queue_name)
                    channel.start_consuming()
            except Exception as exp:
                self.log(
                    logging.ERROR,
                    "Worker have issues while receiving: {}".format(type(exp)),
                    exception=exp,
                    include_traceback=True
                )


class RabbitMQInitializer(BaseInitializer):
    def start(self, no_runner=False):
        if self.options.pop('use_threads', False):
            from threading import Thread as WorkerType
        else:
            from multiprocessing import Process as WorkerType

        serialization_method = self.options.get('serialization_method', 'json')
        if serialization_method == "json":
            import json as serialization_method
        elif serialization_method == "pickle":
            import pickle as serialization_method
        else:
            raise ValueError("unknown serialization method")
        logging.getLogger(self.logger).log(logging.DEBUG, "Starting {} RabbitMQ workers...".format(self.count))

        if not no_runner:

            for process_index in range(self.count):
                # here the multiprocessing logic
                # create a rabbitmq worker to send for worker function
                if 'queue_name' not in self.options or self.options['queue_name'] == "":
                    raise ValueError("you must provide queue_name in worker options")
                worker_instance = RabbitMQWorker(
                    result_backend=self.result_backend,
                    logger=self.logger,
                    **self.options
                )

                p = WorkerType(target=worker, args=(worker_instance,))
                p.daemon = True
                p.start()
        return RabbitMQRunner(queue_name=self.options['queue_name'],
                              serializer=serialization_method.dumps,
                              rabbitmq_configs=self.options.pop("rabbitmq_configs", {}),
                              logger=self.logger)


class RabbitMQRunner(LoggerMixin, BaseRunner):
    def __init__(self, queue_name, serializer, rabbitmq_configs, *args, **kwargs):
        self.queue_name = queue_name
        self.serialize = serializer
        super(RabbitMQRunner, self).__init__(*args, **kwargs)
        self.log(logging.DEBUG, "RabbitMQ Runner is ready...")

        def _create_pool():
            connection_pool_configs = rabbitmq_configs.get('connection_pool_configs', {})

            def create_connection():
                self.log(logging.DEBUG, "Creating new rabbitmq connection")
                con_params = pika.ConnectionParameters(**rabbitmq_configs.get('connection_parameters', {}))
                return pika.BlockingConnection(con_params)

            return pika_pool.QueuedPool(
                create=create_connection,
                **connection_pool_configs
            )

        self._pool = SimpleLazyObject(_create_pool)

    def run(self, function, args=None, kwargs=None, retry_policy=None, callback=None):
        with self._pool.acquire() as cxn:
            cxn.channel.basic_publish(
                body=self.serialize(
                    {
                        "function": function,
                        "parameters": {
                            "args": args or tuple(),
                            "kwargs": kwargs or {},
                            "retry_policy": retry_policy,
                            "callback": callback
                        }
                    }
                ),
                exchange='',
                routing_key=self.queue_name,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            self.log(logging.DEBUG, "Task received : {}".format(function))
