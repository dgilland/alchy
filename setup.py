"""
alchy
-----

The SQLAlchemy enhancement library.

Documentation: https://github.com/dgilland/alchy
"""

from setuptools import setup

setup(
    name = 'alchy',
    version = '0.4.0',
    url = 'https://github.com/dgilland/alchy',
    license = 'MIT',
    author = 'Derrick Gilland',
    author_email = 'dgilland@gmail.com',
    description = 'SQLAlchemy enhancement library',
    long_description = __doc__,
    packages = ['alchy'],
    install_requires = [
        'SQLAlchemy>=0.9.0'
    ],
    test_suite = 'tests',
    keywords = 'sqlalchemy databases',
    classifiers = [
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Topic :: Database :: Front-Ends',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ]
)
