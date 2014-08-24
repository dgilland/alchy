"""
alchy
=====

The declarative companion to SQLAlchemy.

Project: https://github.com/dgilland/alchy

Documentation: http://alchy.readthedocs.org/
"""

from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


meta = {}
exec(read('alchy/__meta__.py'))


setup(
    name=meta['__title__'],
    version=meta['__version__'],
    url=meta['__url__'],
    license=meta['__license__'],
    author=meta['__author__'],
    author_email=meta['__email__'],
    description=meta['__summary__'],
    long_description=read('README.rst'),
    packages=['alchy'],
    install_requires=[
        'SQLAlchemy>=0.9.0'
    ],
    test_suite='tests',
    keywords='sqlalchemy databases',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ]
)
