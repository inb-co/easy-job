import logging
from django.utils.module_loading import import_string

__author__ = 'Apollo'


class LoggerMixin(object):
    _logger = None

    def __init__(self, logger, ):
        self.logger = logger
        self._logger = logging.getLogger(logger)

    def log(self, level, message, **kwargs):
        if hasattr(self, 'logger'):
            import traceback
            if self._logger is None:
                self._logger = logging.getLogger(self.logger)
            self._logger.log(
                level,
                "{} : {}\n{}".format(
                    message,
                    kwargs.get("exception") or "",
                    traceback.format_exc() if kwargs.get('include_traceback', False) else ""
                )
            )


class StoreResultMixin(LoggerMixin):
    def __init__(self, result_backend=None, *args, **options):
        try:
            if result_backend is None:
                raise ValueError("if you don't want a result_backend use dummy result backend")
                # noinspection PyPep8Naming
            ResultBackend = import_string(result_backend['result_backend_class'])
            self.result_backend = ResultBackend(**result_backend.get('options', {}))
        except KeyError:
            raise KeyError("You have to provide result_backend_class for result backend")
        super(StoreResultMixin, self).__init__(*args, **options)

    def store_result(self, task_id, result):
        try:
            self.result_backend.store(task_id, result)
        except Exception as exp:
            self.log(logging.ERROR, "problem while logging result", exp, include_traceback=True)
