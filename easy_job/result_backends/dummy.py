"""
Result backend for Easy-Job which do nothing
there is no available option
"""
from . import BaseResultBackend
import logging

__author__ = 'Apollo'


class DummyBackend(BaseResultBackend):
    def store(self, task_id, result, *args, **kwargs):
        pass
