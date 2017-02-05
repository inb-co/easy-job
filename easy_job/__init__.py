"""
    Easy-Job is asynchronous task runner for django , it means you can run
    a function without waiting for the function to finish .
    Three step to start working with poseidon :
    - >  Step 1: define your workers
        first open your settings file and add the following:
        EASY_JOB = {
            "easy_job_logger": "easy_job",  # the logger name which easy_job itself will be using
            "workers": {}
        }
        the inside workers you need to define your workers.
        a sample worker configuration:
            "WORKER_NAME": {
            "type": "RabbitMQ",
            "count": 3,
            "logger_name": "sample_worker",
            "result_backend": {
                "type": "Log",
                "options": {
                    "logger_name": "sample_worker",
                    "log_level": logging.DEBUG
                }
            },
            "options": {
                'queue_name': 'sample_works2',
                "serialization_method": "pickle",
                "rabbitmq_configs": {
                    "connection_pool_configs": {
                        "max_size": 10,
                        "max_overflow": 10,
                        "timeout": 10,
                        "recycle": 3600,
                        "stale": 45
                    },
                    "connection_parameters": {
                        "host": "127.0.0.1"
                    }
                }
            }
        },
        let me explain what these configurations are from top  :
        WORKER_NAME :
            worker name is a custom name which you specify for the worker , later you will use this name to send
            tasks to the worker , for example if you name your worker my_worker then later in your code you can :
            import easy_job as easy_job
            runner = easy_job.getRunner("my_worker")
            runner.run("path.to.your.function", args=('unnamed','parameters','here'), kwargs={'named':'parameters'} )
        type :
            type of the worker you want , you can choose RabbitMQ or MPQueue for now
        count :
            how many worker of this type you need
        logger_name:
            name of the logger which workers will send their logs to it (it's different than result log)
        result_backend:
            if you like to store the result of each task you can set result backend but generally result backend is optional.
            to configure your result backend you need to provide :
                type :
                    type of result backend , which there is only one result backend available at the moment which just log the
                    result of tasks .
                options:
                    options for the selected result backend , for example a Log result backend needs log_level and logger_name
                    but later another result backend may need other options
        options:
            depending on the type of worker you choose ,it may have special options and configurations you can provide them in
            this dictionary.
            for example type of your worker is RabbitMQ then the following options are available:
                queue_name : name of rabbitMQ queue to use for transferring messages between main process and workers
                serialization_method : method of serialization , could be json or pickle
                rabbitmq_configs : configurations related to rabbitmq , following is an example configuration:
                        {
                            "connection_pool_configs": {
                                "max_size": 10,
                                "max_overflow": 10,
                                "timeout": 10,
                                "recycle": 3600,
                                "stale": 45
                            },
                            "connection_parameters": {
                                "host": "127.0.0.1"
                            }
                        }






    - >  Step 2: call init() in wsgi.py

        open your wsgi.py file and add the following:
            import easy_job as easy_job
            easy_job.init()

    - > Step 3: run your tasks asynchronously anywhere in your django project
        import easy_job as easy_job
        runner = easy_job.getRunner("my_worker") # the worker name you want to send your tasks
        runner.run(
                "path.to.your.function",
                args=('unnamed','parameters','here'),
                kwargs={'named':'parameters'}
        )
        you can also specify retry policy using retrying library parameters like this:
        runner.run(
                "path.to.your.function",
                args=('unnamed','parameters','here'),
                kwargs={'named':'parameters'},
                retry_policy={
                    # a dictionary of retrying library options
                    # for more details check https://pypi.python.org/pypi/retrying
                    # careful about empty retry_policy dictionary , an empty retry_policy dictionary means
                    # running the task using retying library without any condition which leads to try for ever !!!
                    #for example:
                    "stop_max_attempt_number": 7,
                    "wait_random_min": 1000,
                    "wait_random_max": 2000,

                }
        )
        you can also specify a callback function if you wish , you just need to provide callback parameter like this:
        runner.run(
                "path.to.your.function",
                args=('unnamed','parameters','here'),
                kwargs={'named':'parameters'},
                callback={
                    "function": "path.to.callback.function",
                    args=('unnamed','parameters','here'),
                    kwargs={'named':'parameters'}
                }
        )
        remember , some other keyword parameters will be pass to callback like these:
            -> result: the result of the main function
            -> logger: some logger object
        so watch out for parameters with the same name because they will be overwritten by these values
        if you don't have **kwargs in your callback function or you dont have these parameters defined , calling your
        callback will raise exception.
        also remember , if you specify callback parameter , the result of you callback will be sent to ResultBackend
        instead of your function return value.
        a good callback function :
        def i_am_callback(*args, **kwargs):
            result = kwargs['result']
            # do some stuff with the result
            return result
"""
import logging

from django.conf import settings

__author__ = 'Apollo'

_runners = None


def init(run_woker=True):
    from django.utils.module_loading import import_string
    global _runners
    configs = getattr(settings, "EASY_JOB", {})
    logger = logging.getLogger(configs.get('logger', None))
    runners = {}
    for worker_name, worker_options in configs['workers'].items():
        # noinspection PyPep8Naming
        try:
            if 'result_backend' not in worker_options or worker_options['result_backend'] is None:
                worker_options['result_backend'] = "easy_job.result_backends.dummy.DummyBackend"
            WorkerInitializerClass = import_string(worker_options.pop('initializer'))
            worker = WorkerInitializerClass(**worker_options)
            runners[worker_name] = worker.start(not run_woker)
        except (AttributeError, ValueError):
            logger.fatal("invalid initializer specified for worker with name {}".format(worker_name))
    if len(runners) == 0:
        logger.warning("No worker is available")
    _runners = runners


def get_runner(worker_name):
    """

    :param worker_name:
    :return:
    :rtype: BaseRunner
    """
    if _runners is None:
        raise RuntimeError("Easy-Job didn't initialized correctly")
    if worker_name in _runners:
        return _runners[worker_name]
    raise KeyError("no runner found match with your worker name")
