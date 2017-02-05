from distutils.core import setup
from setuptools.command.test import test as TestCommand
import sys


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
    packages=['easy_job'],
    version='0.1.1',
    description='A lightweight background task runner',
    author='Mahdi Zareie',
    author_email='mahdi.elf@gmail.com',
    url='https://github.com/inb-co/easy-job',
    keywords=['worker', 'task runner', 'lightweight job runner'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
