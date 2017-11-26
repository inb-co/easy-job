import sys
from distutils.core import setup

import setuptools
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='easy_job',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    version='0.2.4',
    description='A lightweight background task runner',
    author='Mahdi Zareie',
    install_requires=["retrying",
                      "pika",
                      "pika_pool"],
    author_email='mahdi.elf@gmail.com',
    url='https://github.com/inb-co/easy-job',
    keywords=['worker', 'task runner', 'lightweight job runner'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
