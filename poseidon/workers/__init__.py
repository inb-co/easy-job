import logging

__author__ = 'Apollo'


class BaseInitializer(object):
    def __init__(self, count, logger, options, result_backend=None, *args, **kwargs):
        self.count = count
        self.result_backend = result_backend
        self.logger = logger
        self.options = options

    def start(self, no_runner=False):
        """
        start workers and return a runner instance

        :return: a runner instance ro run
        :rtype: BaseRunner
        """
        raise NotImplementedError()

    def log_error(self, message, exception=None, include_traceback=True):
        import traceback
        logging.getLogger(self.logger).error(
            "{} : {}\n{}".format(
                message,
                exception or "",
                traceback.format_exc() if include_traceback else ""
            )
        )


class BaseRunner(object):
    def run(self, function, args, kwargs):
        pass
