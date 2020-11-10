# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import functools
import getpass
import sys
import pprint
import logging
import re
import os
from distutils.version import LooseVersion

import ftrack_api

cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
ftrack_connect_maya_resource_path = os.path.abspath(os.path.join(cwd, '..',  'resource'))
sys.path.append(sources)

import ftrack_connect_maya



def on_discover_maya_integration(session, event):
    entity = event['data']['context']['selection'][0]
    task = session.get('Context', entity['entityId'])

    maya_connect_scripts = os.path.join(ftrack_connect_maya_resource_path, 'scripts')
    maya_connect_plugins = os.path.join(ftrack_connect_maya_resource_path, 'plug_ins')

    data = {
        'integration': {
            "name": 'ftrack-connect-maya',
            'version': ftrack_connect_maya.__version__
        },
        'env': {
            'PYTHONPATH.prepend': os.path.pathsep.join([maya_connect_scripts, sources]),
            'MAYA_SCRIPT_PATH': maya_connect_scripts,
            'MAYA_PLUG_IN_PATH': maya_connect_plugins,
            'FTRACK_TASKID.set': task['id'],
            'FTRACK_SHOTID.set': task['parent']['id'],
            'LOGNAME.set': session._api_user,
            'FTRACK_APIKEY.set': session._api_key,
            'FS.set': task['parent']['id']['custom_attributes'].get('fstart', 1.0),
            'FE.set': task['parent']['id']['custom_attributes'].get('fend', 100.0)
        }
    }
    return data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return


    handle_event = functools.partial(
        on_discover_maya_integration,
        session
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch',
        handle_event
    )