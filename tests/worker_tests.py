import json
import logging
import pickle
from unittest import mock
from unittest.case import TestCase
from easy_job.workers.mpqueue import MPQueueWorker, MPQueueInitializer
from easy_job.workers.rabbitmq import RabbitMQWorker, RabbitMQInitializer

__author__ = 'Apollo'


class RabbitMQWorkerTestCase(TestCase):
    @mock.patch("pika.BlockingConnection")
    def test_rabbitmq_worker_run_method(self, pika_connection):
        assert isinstance(pika_connection, mock.MagicMock)
        # Arrange
        queue_name = "queue_name"
        rabbitmq_configs = {}
        serialization_method = "json"
        result_backend = {
            "result_backend_class": "easy_job.result_backends.dummy.DummyBackend",
        }
        logger = "sample_logger"
        channel = mock.MagicMock()
        pika_connection.return_value = mock.MagicMock(__enter__=mock.MagicMock(return_value=channel))
        # Act
        RabbitMQWorker(queue_name=queue_name,
                       rabbitmq_configs=rabbitmq_configs,
                       serialization_method=serialization_method,
                       result_backend=result_backend,
                       logger=logger).run()
        # Assert
        channel.assert_has_calls([
            mock.call.channel(),
            mock.call.channel().queue_declare(durable=True, queue=queue_name),
            mock.call.channel().basic_qos(prefetch_count=1),
            mock.call.channel().basic_consume(mock.ANY, queue=queue_name),
            mock.call.channel().start_consuming()
        ])

    @mock.patch("django.utils.module_loading.import_string")
    def test_rabbitmq_worker_callback_method_with_json(self, import_string):
        assert isinstance(import_string, mock.MagicMock)
        # Arrange
        queue_name = "queue_name"
        rabbitmq_configs = {}
        serialization_method = "json"
        result_backend = {
            "result_backend_class": "easy_job.result_backends.dummy.DummyBackend"
        }
        logger = "sample_logger"
        m = import_string.return_value = mock.MagicMock()
        channel = mock.MagicMock()
        method = mock.MagicMock()
        body = {
            "function": "something.doesnt.matter",
            "parameters": {
                "args": (1, 2, 3),
                "kwargs": {'a': 4}
            }
        }
        # Act
        RabbitMQWorker(queue_name=queue_name,
                       rabbitmq_configs=rabbitmq_configs,
                       serialization_method=serialization_method,
                       result_backend=result_backend,
                       logger=logger).callback(channel, method, None, json.dumps(body).encode('utf8'))
        # Assert
        m.assert_called_once_with(1, 2, 3, a=4)
        channel.basic_ack.assert_called_once_with(delivery_tag=mock.ANY)

    @mock.patch("django.utils.module_loading.import_string")
    def test_rabbitmq_worker_callback_method_with_pickle(self, import_string):
        assert isinstance(import_string, mock.MagicMock)
        # Arrange
        queue_name = "queue_name"
        rabbitmq_configs = {}
        serialization_method = "pickle"
        result_backend = {
            "result_backend_class": "easy_job.result_backends.dummy.DummyBackend"
        }
        logger = "sample_logger"
        m = import_string.return_value = mock.MagicMock()
        channel = mock.MagicMock()
        method = mock.MagicMock()
        body = {
            "function": "something.doesnt.matter",
            "parameters": {
                "args": (1, 2, 3),
                "kwargs": {'a': 4}
            }
        }
        # Act
        RabbitMQWorker(queue_name=queue_name,
                       rabbitmq_configs=rabbitmq_configs,
                       serialization_method=serialization_method,
                       result_backend=result_backend,
                       logger=logger).callback(channel, method, None, pickle.dumps(body))
        # Assert
        m.assert_called_once_with(1, 2, 3, a=4)
        channel.basic_ack.assert_called_once_with(delivery_tag=mock.ANY)

    @mock.patch("django.utils.module_loading.import_string")
    @mock.patch("logging.getLogger")
    def test_rabbitmq_worker_callback_method_with_invalid_serialization_method(self, getLogger, import_string):
        assert isinstance(import_string, mock.MagicMock)
        # Arrange
        queue_name = "queue_name"
        rabbitmq_configs = {}
        serialization_method = "invalid"
        result_backend = {
            "result_backend_class": "easy_job.result_backends.dummy.DummyBackend",
        }
        logger = getLogger.return_value = mock.MagicMock()
        # Act
        rbt = RabbitMQWorker(queue_name=queue_name,
                             rabbitmq_configs=rabbitmq_configs,
                             serialization_method=serialization_method,
                             result_backend=result_backend,
                             logger="log")
        rbt.callback(mock.MagicMock(), mock.MagicMock(), None, "")

        # Assert

        logger.log.assert_called_once_with(logging.ERROR, mock.ANY)

    @mock.patch("logging.getLogger")
    @mock.patch("easy_job.workers.rabbitmq.call_with_retry")
    @mock.patch("django.utils.module_loading.import_string")
    @mock.patch("time.time")
    def test_normal_rabbitmq_worker_callback_with_retry(self, time, import_string, call_with_retry, getLogger):
        # Arrange
        dummy = mock.MagicMock()
        time.return_value = 0
        m = import_string.return_value = mock.MagicMock()
        logger = getLogger.return_value
        call_with_retry.return_value = "Some result"
        function_dot_path = "some.function"
        args = (1, 2, 3)
        retry_policy = {}
        kwargs = {
            "a": 1,
            "b": 2
        }
        body = {
            "function": function_dot_path,
            "parameters": {
                "args": args,
                "kwargs": kwargs,
                "retry_policy": retry_policy
            }
        }
        rmq = mock.MagicMock()
        rmq.deserialize = lambda x: x  # convert deserializer to identity function
        # Act

        RabbitMQWorker.callback(rmq, dummy, dummy, dummy, body)

        # Assert

        m.assert_not_called()
        call_with_retry.assert_called_once_with(m, args, kwargs, retry_policy)
        rmq.store_result.assert_called_once_with(function_dot_path, 'Some result')
        rmq.log.assert_called_once_with(logging.DEBUG, "{} finished in {} seconds ".format(function_dot_path, 0))

    @mock.patch("logging.getLogger")
    @mock.patch("django.utils.module_loading.import_string")
    @mock.patch("time.time")
    def test_rabbitmq_worker_with_callback_parameter(self, time, import_string, getLogger):
        # Arrange
        dummy = mock.MagicMock()
        time.return_value = 0
        main_function, callback_function = import_string.side_effect = mock.MagicMock(), mock.MagicMock()
        main_function.return_value = "Main function return value"
        callback_function.return_value = "Callback function return value"
        function_dot_path = "some.function"
        args = (1, 2, 3)
        kwargs = {
            "a": 1,
            "b": 2
        }
        body = {
            "function": function_dot_path,
            "parameters": {
                "args": args,
                "kwargs": kwargs,
                "callback": {
                    "function": "some.callback.function",
                    "args": (1,),
                    "kwargs": {
                        "test": True
                    }
                }
            }
        }
        rmq = mock.MagicMock()
        rmq.deserialize = lambda x: x  # convert deserializer to identity function
        # Act

        RabbitMQWorker.callback(rmq, dummy, dummy, dummy, body)

        # Assert
        main_function.assert_called_once_with(1, 2, 3, a=1, b=2)
        callback_function.assert_called_once_with(1, logger=mock.ANY, result='Main function return value', test=True)
        rmq.store_result.assert_called_once_with(function_dot_path, 'Callback function return value')
        rmq.log.assert_called_once_with(logging.DEBUG, "{} finished in {} seconds ".format(function_dot_path, 0))


class RabbitMQInitializerTestCase(TestCase):
    @mock.patch("logging.getLogger")
    @mock.patch("multiprocessing.Process")
    @mock.patch("easy_job.workers.rabbitmq.RabbitMQRunner")
    def test_normal_start(self, runner, process, getLogger):
        assert isinstance(process, mock.MagicMock)
        # Arrange
        process_count = 4
        logger = getLogger.return_value = mock.MagicMock()
        expected_result = runner.return_value = "SOME_RETURN_VALUE"
        result_backend = {
            'result_backend_class': 'easy_job.result_backends.dummy.DummyBackend'
        }
        # Act
        initializer = RabbitMQInitializer(count=process_count, logger="logger", result_backend=result_backend,
                                          options={'serialization_method': 'json', 'queue_name': 'queue',
                                                   'rabbitmq_configs': {}})
        result = initializer.start()
        # Assert
        logger.log.assert_called_once_with(10, "Starting {} RabbitMQ workers...".format(process_count))

        process.assert_has_calls([mock.call(args=(mock.ANY,), target=mock.ANY), mock.call().start()] * process_count)
        self.assertEqual(result, expected_result)
        _, args, kwargs = process.mock_calls[0]
        worker_object = kwargs['args'][0]
        self.assertIsInstance(worker_object, RabbitMQWorker)


class MPQueueWorkerTestCase(TestCase):
    @mock.patch("django.utils.module_loading.import_string")
    @mock.patch("time.time")
    def test_normal_mpqueue_worker_callback(self, time, import_string):
        # Arrange
        time.return_value = 0
        m = import_string.return_value = mock.MagicMock()
        m.return_value = "Some result"
        function_dot_path = "some.function"
        body = {
            "function": function_dot_path,
            "parameters": {
                "args": (1, 2, 3),
                "kwargs": {
                    "a": 1,
                    "b": 2
                }
            }
        }
        mpq = mock.MagicMock()
        # Act

        MPQueueWorker.callback(mpq, body)

        # Assert
        m.assert_called_once_with(1, 2, 3, a=1, b=2)
        mpq.store_result.assert_called_once_with(function_dot_path, 'Some result')
        mpq.log.assert_called_once_with(logging.DEBUG, "{} finished in {} seconds ".format(function_dot_path, 0))

    @mock.patch("logging.getLogger")
    @mock.patch("easy_job.workers.mpqueue.call_with_retry")
    @mock.patch("django.utils.module_loading.import_string")
    @mock.patch("time.time")
    def test_normal_mpqueue_worker_callback_with_retry(self, time, import_string, call_with_retry, getLogger):
        # Arrange
        time.return_value = 0
        m = import_string.return_value = mock.MagicMock()
        logger = getLogger.return_value
        call_with_retry.return_value = "Some result"
        function_dot_path = "some.function"
        args = (1, 2, 3)
        retry_policy = {}
        kwargs = {
            "a": 1,
            "b": 2
        }
        body = {
            "function": function_dot_path,
            "parameters": {
                "args": args,
                "kwargs": kwargs,
                "retry_policy": retry_policy
            }
        }
        mpq = mock.MagicMock()
        # Act

        MPQueueWorker.callback(mpq, body)

        # Assert
        m.assert_not_called()
        call_with_retry.assert_called_once_with(m, args, kwargs, retry_policy)
        mpq.store_result.assert_called_once_with(function_dot_path, 'Some result')
        mpq.log.assert_called_once_with(logging.DEBUG, "{} finished in {} seconds ".format(function_dot_path, 0))

    @mock.patch("logging.getLogger")
    @mock.patch("django.utils.module_loading.import_string")
    @mock.patch("time.time")
    def test_mpqueue_worker_with_callback_parameter(self, time, import_string, getLogger):
        # Arrange
        time.return_value = 0
        main_function, callback_function = import_string.side_effect = mock.MagicMock(), mock.MagicMock()
        main_function.return_value = "Main function return value"
        callback_function.return_value = "Callback function return value"
        function_dot_path = "some.function"
        args = (1, 2, 3)
        kwargs = {
            "a": 1,
            "b": 2
        }
        body = {
            "function": function_dot_path,
            "parameters": {
                "args": args,
                "kwargs": kwargs,
                "callback": {
                    "function": "some.callback.function",
                    "args": (1,),
                    "kwargs": {
                        "test": True
                    }
                }
            }
        }
        rmq = mock.MagicMock()
        rmq.deserialize = lambda x: x  # convert deserializer to identity function
        # Act

        MPQueueWorker.callback(rmq, body)

        # Assert
        main_function.assert_called_once_with(1, 2, 3, a=1, b=2)
        callback_function.assert_called_once_with(1, logger=mock.ANY, result='Main function return value', test=True)
        rmq.store_result.assert_called_once_with(function_dot_path, 'Callback function return value')
        rmq.log.assert_called_once_with(logging.DEBUG, "{} finished in {} seconds ".format(function_dot_path, 0))


# noinspection PyCallByClass
class MPQueueInitializerTestCase(TestCase):
    @mock.patch("multiprocessing.Queue")
    @mock.patch("multiprocessing.Process")
    @mock.patch("logging.getLogger")
    @mock.patch("easy_job.workers.mpqueue.MPQueueWorker")
    @mock.patch("easy_job.workers.mpqueue.MPQueueRunner")
    def test_initializer_start_method(self, mpqr: mock.MagicMock,
                                      mpqw: mock.MagicMock,
                                      getLogger: mock.MagicMock,
                                      Process: mock.MagicMock,
                                      Queue: mock.MagicMock):
        # Arrange
        logger = getLogger.return_value = mock.MagicMock()
        queue = Queue.return_value = mock.MagicMock()
        proc_count = 4
        this = mock.MagicMock(count=proc_count)
        mpqr.return_value = "Expect this"
        # Act
        result = MPQueueInitializer.start(this)

        # Assert
        self.assertEqual(result, mpqr.return_value)
        Queue.assert_called_once_with()
        logger.log.assert_called_once_with(logging.DEBUG, "Starting {} MPQueue workers...".format(proc_count))
        mpqw.assert_has_calls([mock.call(logger=mock.ANY, queue=mock.ANY, result_backend=mock.ANY)] * proc_count)
        from easy_job.workers.mpqueue import worker
        Process.assert_has_calls(
            [
                mock.call(args=mock.ANY, name=mock.ANY, target=worker),
                mock.call().start()
            ] * proc_count
        )
        mpqr.assert_called_once_with(queue=queue, logger=mock.ANY)


class CommonTestCase(TestCase):
    @mock.patch("easy_job.workers.common.Retrying")
    def test_call_a_function_with_some_retry_parameters(self, Retrying):
        # Arrange
        func = mock.MagicMock()
        from easy_job.workers.common import call_with_retry as target
        retrying_params = {
            "wait_random_min": 100,
            "wait_random_max": 500,
            "stop_max_attempt_number": 5
        }
        # Act
        result = target(func, (1, 2, 3), {"p": "arameter"}, retry_policy=retrying_params)
        # Assert
        Retrying.assert_called_once_with(**retrying_params)

    # @mock.patch("")
    def test_actually_calling_retrying_library_to_see_if_everything_is_cool(self, ):
        # Arrange
        function_side_effects = [Exception(), Exception(), "finally worked"]
        func = mock.MagicMock(side_effect=function_side_effects)
        from easy_job.workers.common import call_with_retry as target
        retrying_params = {
            "stop_max_attempt_number": 5
        }
        # Act
        result = target(func, (1, 2, 3), {"p": "arameter"}, retry_policy=retrying_params)

        # Assert
        func.assert_has_calls([mock.call(1, 2, 3, p='arameter'),
                               mock.call(1, 2, 3, p='arameter'),
                               mock.call(1, 2, 3, p='arameter')]
                              )
        self.assertEqual(result, "finally worked")

    # @mock.patch("")
    def test_actually_calling_retrying_library_in_a_failing_condition(self, ):
        # Arrange
        function_side_effects = [IndentationError(), SyntaxError(), OSError()]
        func = mock.MagicMock(side_effect=function_side_effects)
        from easy_job.workers.common import call_with_retry as target
        retrying_params = {
            "stop_max_attempt_number": 3
        }
        args = (1, 2, 3)
        kwargs = {"p": "arameter"}
        # Act
        with self.assertRaises(OSError):
            target(func, args, kwargs, retry_policy=retrying_params)

        # Assert
        func.assert_has_calls([mock.call(*args, **kwargs),
                               mock.call(*args, **kwargs),
                               mock.call(*args, **kwargs)]
                              )
