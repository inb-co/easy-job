import logging
from unittest import mock
from unittest.case import TestCase
from easy_job.result_backends.log import LogResultBackend

__author__ = 'Apollo'


class ResultBackendLogTestCase(TestCase):
    @mock.patch("logging.getLogger")
    def test_normal_logging_function(self, logger):
        assert isinstance(logger, mock.MagicMock)
        # Arrange
        logger_instance = logger.return_value = mock.MagicMock()
        # Act
        log_backend = LogResultBackend(logger="foo")
        log_backend.store(
            "sample task",
            "sample result"
        )
        # Assert
        _, args, kwargs = logger.mock_calls[0]  # logging.getLogger call
        self.assertEqual(args[0], "foo")

        _, args, kwargs = logger_instance.mock_calls[0]  # logger.log call
        self.assertEqual(kwargs, {
            'level': logging.DEBUG,
            'msg': 'sample task -> sample result'
        })

    def test_normal_logging_function_using_logger_instance(self):
        # Arrange
        logger_instance = mock.MagicMock()

        # Act
        log_backend = LogResultBackend(logger_instance=logger_instance)
        log_backend.store(
            "sample task",
            "sample result"
        )
        # Assert
        _, args, kwargs = logger_instance.mock_calls[0]  # logger.log call
        self.assertEqual(kwargs, {
            'level': logging.DEBUG,
            'msg': 'sample task -> sample result'
        })
