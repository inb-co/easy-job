"""
Result backend for Easy-Job which use python logging
available options to use
    * log_level: level of logging could be logging.DEBUG logging.ERROR or any other log level defined in logging module
        default: logging.DEBUG
    * logger: name of the logger to use, be cautious , the logger must already defined
        default: no default value available, you must specify either logger or logger_instance
    * logger_instance: for testing purposes you can provide the logger object itself
        default: None
    message_template: string template to log function and result , you can use {task_id} and {result} in your template
        default: "{task_id} -> {result}"
"""
from . import BaseResultBackend
import logging

__author__ = 'Apollo'


class LogResultBackend(BaseResultBackend):
    def __init__(self, log_level=logging.DEBUG, logger=None, logger_instance=None, message_template=None):
        if logger_instance is not None:
            self.logger = logger_instance
        elif logger is not None:
            self.logger = logging.getLogger(logger)
        else:
            raise ValueError("No logger or logger_instance specified")
        self.log_level = log_level
        self.message_template = message_template or "{task_id} -> {result}"

    def store(self, task_id, result, *args, **kwargs):
        self.logger.log(
            level=self.log_level,
            msg=self.message_template.format(
                task_id=task_id,
                result=result
            )
        )


