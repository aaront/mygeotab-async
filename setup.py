# -*- coding: utf-8 -*-
import re
import ast

from setuptools import setup, find_packages


_version_re = re.compile(r'__version__\s+=\s+(.*)')
with open('mygeotab_async.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='mygeotab-async',
    author='Aaron Toth',
    version=version,
    url='https://github.com/aaront/mygeotab-async',
    description='An experimental asynchronous Python interface for the MyGeotab API, powered by asyncio',
    long_description=open('README.rst').read(),
    install_requires=[
        'mygeotab>=0.2',
        'aiohttp>=0.15'
    ],
    test_suite="tests",
    py_modules=[
        'mygeotab_async'
    ],
    package_data={'': ['LICENSE']},
    license='Apache 2.0',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries'
    ),
)