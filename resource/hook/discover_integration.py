# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import functools
import getpass
import sys
import pprint
import logging
import re
import os

import ftrack_api


cwd = os.path.dirname(__file__)
sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
ftrack_connect_maya_resource_path = os.path.abspath(os.path.join(cwd, '..',  'resource'))
sys.path.append(sources)


def on_discover_maya_integration(session, event):

    from ftrack_connect_maya import __version__ as integration_version

    data = {
        'integration': {
            'name': 'ftrack-connect-maya',
            'version': integration_version
        }
    }

    return data


def on_launch_maya_integration(session, event):
    maya_base_data = on_discover_maya_integration(session, event)

    maya_connect_scripts = os.path.join(ftrack_connect_maya_resource_path, 'scripts')
    maya_connect_plugins = os.path.join(ftrack_connect_maya_resource_path, 'plug_ins')


    maya_base_data['integration']['env'] = {
        'PYTHONPATH.prepend': os.path.pathsep.join([maya_connect_scripts, sources]),
        'MAYA_SCRIPT_PATH': maya_connect_scripts,
        'MAYA_PLUG_IN_PATH': maya_connect_plugins,
        'LOGNAME.set': session._api_user,
        'FTRACK_APIKEY.set': session._api_key,
    }
    
    selection = event['data'].get('context', {}).get('selection', [])
    
    if selection:
        task = session.get('Context', selection[0]['entityId'])
        maya_base_data['integration']['env']['FTRACK_TASKID.set'] =  task['id']
        maya_base_data['integration']['env']['FTRACK_SHOTID.set'] =  task['parent']['id']
        maya_base_data['integration']['env']['FS.set'] = task['parent']['custom_attributes'].get('fstart', '1.0')
        maya_base_data['integration']['env']['FE.set'] = task['parent']['custom_attributes'].get('fend', '100.0')

    return maya_base_data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return


    handle_discovery_event = functools.partial(
        on_discover_maya_integration,
        session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=maya*'
        ' and data.application.version <= 2020',
        handle_discovery_event
    )

    handle_launch_event = functools.partial(
        on_launch_maya_integration,
        session
    )    

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=maya*'
        ' and data.application.version <= 2020',
        handle_launch_event
    )
    
