Easy-Job
========
Easy-Job is asynchronous task runner for django , it means you can run a function without waiting for the function to finish .

*Notice : current design of easy-job depends on django framework but in the near future we intend to break this dependency*


***How to setup Easy-Job in a django project***

three simple steps are required to make setup easy-job in your django project :
****1. first open your settings file and add the following:****

        EASY_JOB = {
            "easy_job_logger": "easy_job",  # the logger name which easy_job itself will be using
            "workers": {}
        }
    the inside workers you need to define your workers.
        .. code-block:: python

        # inside workers dictionary
        EASY_JOB = {
                    "easy_job_logger": "easy_job",  # the logger name which easy_job itself will be using
                    "workers": {
                        "worker1": {
                                "initializer": "easy_job.workers.rabbitmq.RabbitMQInitializer",
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
                    }
        }

let me explain what these configurations are from top  :
* worker1: worker name
    worker name is a custom name which you specify for the worker , later you will use this name to send
    tasks to this particular worker.
* initializer: worker initializer class path
    the dot.path to worker initializer class, you can use one of :
    `easy_job.workers.rabbitmq.RabbitMQInitializer` or `easy_job.workers.mpqueue.MPQueueInitializer`
    or you can create your own initializer
* count :
    how many worker of this type you need
* logger: name of logger for this worker
    name of the logger which workers will send their logs to it (it's different than result log)
* result_backend:
if you like to store the result of each task you can set result backend but generally result backend is optional.
to configure your result backend you need to provide
    * result_backend_class :
            type of result backend ,
                you can use `poseidon_async.result_backends.log.LogResultBackend` or create your
            own result backend .
    * options:
            options for the selected result backend , for example a Log result backend needs log_level and logger_name
            but later another result backend may need other options
* options:
depending on the type of worker you chose ,it may have special options and configurations you can provide them in
this dictionary.
in this particular example which we are using RabbitMQ the following options are available:
    * queue_name : name of rabbitMQ queue to use for transferring messages between main process and workers
    * serialization_method : method of serialization , could be :code:`json` or *pickle*
    * rabbitmq_configs : configurations related to rabbitmq , following is an example configuration:
    ```
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
    ```
****2. call init() in wsgi.py****
open your wsgi.py file and add the following:
```
import easy_job as easy_job
easy_job.init()
```
this little code will initialize easy-job and create all your workers .

****3.run your tasks****
somewhere in your project you can run your tasks:

```
import easy_job
runner = easy_job.getRunner("my_worker") # the worker name you want to send your tasks
runner.run(
        "path.to.your.function",
        args=('unnamed','parameters','here'),
        kwargs={'named':'parameters'}
)
```

that's it

Some more options :Easy-Job
========
Easy-Job is asynchronous task runner for django , it means you can run a function without waiting for the function to finish .

*Notice : current design of easy-job depends on django framework but in the near future we intend to break this dependency*


***How to setup Easy-Job in a django project***

three simple steps are required to make setup easy-job in your django project :
****1. first open your settings file and add the following:****

        EASY_JOB = {
            "easy_job_logger": "easy_job",  # the logger name which easy_job itself will be using
            "workers": {}
        }
    the inside workers you need to define your workers.
        .. code-block:: python

        # inside workers dictionary
        EASY_JOB = {
                    "easy_job_logger": "easy_job",  # the logger name which easy_job itself will be using
                    "workers": {
                        "worker1": {
                                "initializer": "easy_job.workers.rabbitmq.RabbitMQInitializer",
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
                    }
        }

let me explain what these configurations are from top  :
* worker1: worker name
    worker name is a custom name which you specify for the worker , later you will use this name to send
    tasks to this particular worker.
* initializer: worker initializer class path
    the dot.path to worker initializer class, you can use one of :
    `easy_job.workers.rabbitmq.RabbitMQInitializer` or `easy_job.workers.mpqueue.MPQueueInitializer`
    or you can create your own initializer
* count :
    how many worker of this type you need
* logger: name of logger for this worker
    name of the logger which workers will send their logs to it (it's different than result log)
* result_backend:
if you like to store the result of each task you can set result backend but generally result backend is optional.
to configure your result backend you need to provide
    * result_backend_class :
            type of result backend ,
                you can use `poseidon_async.result_backends.log.LogResultBackend` or create your
            own result backend .
    * options:
            options for the selected result backend , for example a Log result backend needs log_level and logger_name
            but later another result backend may need other options
* options:
depending on the type of worker you chose ,it may have special options and configurations you can provide them in
this dictionary.
in this particular example which we are using RabbitMQ the following options are available:
    * queue_name : name of rabbitMQ queue to use for transferring messages between main process and workers
    * serialization_method : method of serialization , could be :code:`json` or *pickle*
    * rabbitmq_configs : configurations related to rabbitmq , following is an example configuration:
```
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
```
****2. call init() in wsgi.py****
open your wsgi.py file and add the following:
```
import easy_job as easy_job
easy_job.init()
```
this little code will initialize easy-job and create all your workers .

****3.run your tasks****
somewhere in your project you can run your tasks:

```
import easy_job
runner = easy_job.getRunner("my_worker") # the worker name you want to send your tasks
runner.run(
        "path.to.your.function",
        args=('unnamed','parameters','here'),
        kwargs={'named':'parameters'}
)
```

that's it

***Some more options :***

****Specifying retry policy when running tasks :****
easy-job used retrying package to perform retrying on failure , if you intend to use this feature you should call `run()`
function with `retry_policy` parameter , like this :
```
runner.run(
                "path.to.your.function",
                args=('unnamed','parameters','here'),
                kwargs={'named':'parameters'},
                retry_policy={
                    "stop_max_attempt_number": 7,
                    "wait_random_min": 1000,
                    "wait_random_max": 2000,

                }
        )

```
please read [retrying documentation](https://pypi.python.org/pypi/retrying) for all available options.
*warning: do not use an empty `retry_policy` dictionary , if you don't need retrying just don't send this parameter otherwise an empty dictionary means try forever*


****Specifying callback function for tasks :****
you can also specify a callback function if you wish , you just need to provide callback parameter like this:
```
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
```
a few thing you need to remember when using callbacks:
1. parameter name conflict
do not name your parameters `result` or `logger` , the worker will use these names for:
    * result: the result of the main function
    * logger: some logger object
so watch out for parameters with the same name because they will be overwritten by these values
2. task failure means no callback invocation
failure of your task will result on ignoring callback invocation
if you don't have `**kwargs` in your callback function or you dont have these parameters defined , calling your
callback will raise exception.
a good callback function :
```
def i_am_callback(*args, **kwargs):
    result = kwargs['result']
    # do some stuff with the result
    return result
```

3. Result
if you specify callback , for your task the return value of the callback will be sent to the result backend instead of your primary function


