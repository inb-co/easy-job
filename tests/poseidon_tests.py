import copy
from django.test import TestCase
from unittest import mock
import logging

__author__ = 'Apollo'
EASY_JOB = {
    "logger": "",  # < choose a logger
    "workers": {
        "worker1": {
            "initializer": "sample.initializer",
            "count": 3,
            "logger": "worker_log",  # < choose a logger
            "result_backend": {
                "result_backend_class": "sample.backend",
                "options": {
                    "logger": "worker_log",  # < choose a logger
                    "log_level": logging.DEBUG
                }
            },
            "options": {
                'p1': 1,
                'p2': True,
                'p3': "me",
                'p4': (2, 3, 4, False),
                'p5': {
                    'p6': 5,
                    'p7': [
                        {},
                        {}
                    ]
                },
            }
        },
    }
}


class EasyJobTestCase(TestCase):
    @mock.patch("django.utils.module_loading.import_string")
    def test_easy_job_instantiate_initializers_correctly(self, import_string):
        assert isinstance(import_string, mock.MagicMock)
        # Arrange
        initializer = mock.MagicMock()
        import_string.return_value = initializer

        # Act
        import copy
        with self.settings(EASY_JOB=copy.deepcopy(EASY_JOB)):
            from easy_job import init
            init()

        # Assert
        _, args, kwargs = initializer.mock_calls[0]
        self.assertNotEqual(kwargs, EASY_JOB['workers']['worker1'])
        kwargs["initializer"] = EASY_JOB['workers']['worker1']['initializer']
        self.assertEqual(kwargs, EASY_JOB['workers']['worker1'])

    @mock.patch("logging.getLogger")
    @mock.patch("django.utils.module_loading.import_string")
    def test_poseidon_init_with_invalid_initializer(self, import_string, getLogger):
        assert isinstance(import_string, mock.MagicMock)
        assert isinstance(getLogger, mock.MagicMock)
        # Arrange
        import_string.side_effect = ValueError("import failed")
        logger_mock = getLogger.return_value = mock.MagicMock()
        # Act
        with self.settings(EASY_JOB=copy.deepcopy(EASY_JOB)):
            from easy_job import init
            init()

        # Assert
        import_string.assert_called_once_with(EASY_JOB['workers']['worker1']['initializer'])
        fatal_call = logger_mock.fatal.mock_calls[0]
        args = fatal_call[1]
        self.assertEqual(args[0], "invalid initializer specified for worker with name worker1")

        warning_call = logger_mock.warning.mock_calls[0]
        args = warning_call[1]
        self.assertEqual(args[0], "No worker is available")
