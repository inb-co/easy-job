from retrying import Retrying

__author__ = "Apollo"


def call_with_retry(function, args: tuple, kwargs: dict, retry_policy: dict):
    return Retrying(**retry_policy).call(function, *args, **kwargs)


def empty_callback(result, logger, *args, **kwargs):
    return result
