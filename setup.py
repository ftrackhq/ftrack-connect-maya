# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import re
import glob
import shutil

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from setuptools import setup, find_packages, Command
from pip._internal import main as pip_main

import fileinput


ROOT_PATH = os.path.dirname(
    os.path.realpath(__file__)
)

RESOURCE_PATH = os.path.join(
    ROOT_PATH, 'resource'
)

SOURCE_PATH = os.path.join(
    ROOT_PATH, 'source'
)

README_PATH = os.path.join(ROOT_PATH, 'README.rst')
BUILD_PATH = os.path.join(ROOT_PATH, 'build')
STAGING_PATH = os.path.join(BUILD_PATH, 'ftrack-connect-maya-{0}')

MAYA_PLUGIN_PATH = os.path.join(RESOURCE_PATH, 'plug_ins')
MAYA_SCRIPTS_PATH = os.path.join(RESOURCE_PATH, 'scripts')

HOOK_PATH = os.path.join(RESOURCE_PATH, 'hook')

with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_maya', '_version.py')
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


STAGING_PATH = STAGING_PATH.format(VERSION)


# Custom commands.
class PyTest(TestCommand):
    '''Pytest command.'''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        '''Import pytest and run.'''
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


class BuildPlugin(Command):
    '''Build plugin.'''

    description = 'Download dependencies and build plugin .'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        '''Run the build step.'''
        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # Copy plugin files
        shutil.copytree(
            MAYA_PLUGIN_PATH,
            os.path.join(STAGING_PATH, 'resource', 'plug_ins')
        )

        # Copy scripts files
        shutil.copytree(
            MAYA_SCRIPTS_PATH,
            os.path.join(STAGING_PATH, 'resource', 'scripts')
        )

        # Copy hook files
        shutil.copytree(
            HOOK_PATH,
            os.path.join(STAGING_PATH, 'hook')
        )

        pip_main(
            [
                'install',
                '.',
                '--target',
                os.path.join(STAGING_PATH, 'dependencies'),
                '--process-dependency-links'
            ]
        )

        result_path = shutil.make_archive(
            os.path.join(
                BUILD_PATH,
                'ftrack-connect-maya-{0}'.format(VERSION)
            ),
            'zip',
            STAGING_PATH
        )

        print 'Result: ' + result_path


# Configuration.
setup(
    name='ftrack connect maya',
    version=VERSION,
    description='Maya integration with ftrack.',
    long_description=open(README_PATH).read(),
    keywords='',
    url='https://bitbucket.org/ftrack/ftrack-connect-maya',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'source'
    },
    setup_requires=[
        'sphinx >= 1.2.2, < 2',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 1'
    ],
    tests_require=[
        'pytest >= 2.3.5, < 3'
    ],
    cmdclass={
        'test': PyTest,
        'build_plugin': BuildPlugin,
    }
)
