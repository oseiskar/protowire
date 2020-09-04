from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

def read(fname):
    return open(path.join(here, fname)).read()

setup(
    name='protowire',
    version='1.2.0',
    description='Write protobuf messages & GRPC calls from the command line without the proto files',
    long_description=read('DESCRIPTION.rst'),
    url='https://github.com/oseiskar/protowire',
    author='Otto Seiskari',

    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',

        # MIT license
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='grpc protobuf commandline cli',
    packages=find_packages(exclude=['contrib', 'doc', 'tests']),

    entry_points = {
        'console_scripts': [
            'pw=protowire.commandline:pw',
            'pw-grpc-frame=protowire.commandline:grpc_frame',
            'pw-grpc-client=protowire.commandline:grpc_client',
        ],
    },

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['nose', 'pylint', 'check-manifest'],
        'grpc': ['grcpio'],
    }
)
