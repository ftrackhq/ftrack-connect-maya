..
    :copyright: Copyright (c) 2015 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: 1.4.0
    :date: 2021-09-08

    .. change:: change
        :tags: Hook

        Update hook for application-launcher.

    .. change:: change
        :tags: Setup

        Provide dependency to ftrack-connector-legacy module.


.. release:: 1.3.0
    :date: 2020-09-28

    .. change:: change

        Update pyside signal signature for pyside2 compatiblity.
    
    .. change:: add
        :tags: Import

        Add support for FBX import.


.. release:: 1.2.3
    :date: 2020-01-21

    ..change:: changed
        :tags: Setup

        Pip compatibility for version 19.3.0 or higher

    .. change:: fix

        Fix QStringListModel compatibility for PySide2 5.9+.

    .. change:: add
        :tags: Import

        Added import single frame image sequence as image texture.

.. release:: 1.2.2
    :date: 2019-06-25

    .. change:: fix
        :tags: Import

        Allow alembic to be imported as reference.

    .. change:: fix
        :tags: Export

        Fbx export breaks under windows.

    .. change:: new
        :tags: Import

        Added "Open" import mode, which replaces current scene.


.. release:: 1.2.1
    :date: 2019-04-02

    .. change:: new
        :tags: Export

        Provide fbx export options.

.. release:: 1.2.0
    :date: 2018-12-19

    .. change:: changed
        :tags: Internal

        Convert code to standalone ftrack-connect plugin.

.. release:: 1.1.4
    :date: 2018-10-11

    .. change:: fix
        :tags: Hook

        Version check breaks due to changes in application version sorting with
        connect >= 1.5.0.

.. release:: 1.1.3
    :date: 2018-04-27

    .. change:: changed

        Import type of scenes are determined initially from file type.

    .. change:: changed
       :tags: Internal

       Enforce QtExt minimum version in setup.

    .. change:: changed

       Explicit radio buttons for import modes; "Import" and "Reference".
       Change default import mode to "Reference".

    .. change:: changed
       :tags: Asset manager

        Allow import support for different audio file formats.

.. release:: 1.1.2
    :date: 2018-02-02

    .. change:: fixed
        :tags: Compatibility

        QtWebWidgets incompatibility for windows.

.. release:: 1.1.1
    :date: 2017-12-14

    .. change:: fixed
        :tags: Compatibility

        Integration does not load in Maya 2018 on windows.


    .. change:: new
       :tags: Logging

       Improved feedback gathering.

.. release:: 1.0.0
    :date: 2017-07-07

    .. change:: fixed
        :tags: Logging

        Legacy api event hub spams Maya.

    .. change:: new
        :tags: Import

        Add more options for import namespace.

    .. change:: fixed
        :tags: Timeline

        Error when setting timeline if task parent is not a Shot.

    .. change:: fixed
        :tags: Compatibility

        If PySide is installed on the system Maya 2017 may crash.

.. release:: 0.2.5
    :date: 2016-12-01

    .. change:: fixed
        :tags: Performance

        Scanning for new asset versions at scene startup is very slow.

    .. change:: fixed
        :tags: Performance

        All panels are created on Maya startup which has a negative impact
        on performance.

    .. change:: fixed
        :tags: Compatibility

        Integration breaks on Maya 2015.

    .. change:: fixed

        Can't import abc which does not have "alembic" as component name.

.. release:: 0.2.4
    :date: 2016-09-16

    .. change:: changed

        Add support for Maya 2017.

.. release:: 0.2.3
    :date: 2016-06-07

    .. change:: fixed
        :tags: Ui

        Asset without transform nodes doesn't show in Maya Asset manager.

    .. change:: fixed
        :tags: Ui

        Publish asset doesn't work correctly if changing context.

    .. change:: fixed
        :tags: Ui

        Cannot switch version of alembic from the Asset manager.

        .. note::

            This fix applies to later versions of Maya 2016.

    .. change:: fixed

        Timeline does not set correctly when importing a scene asset.

    .. change:: fixed

        Assets not always deleted correctly from the Asset manager.

.. release:: 0.2.2
    :date: 2016-05-10

    .. change:: fixed

        When taking a screenshot for publish the entire window is captured
        rather than only the view port.

.. release:: 0.2.1
    :date: 2016-04-25

    .. change:: fixed
        :tags: Hook

        Maya versions appear twice in connect.

    .. change:: fixed
        :tags: Ui

        Restore :py:class:`ftrack_connect.panelcom.PanelComInstance` communication with contextSelector,
        so changes to the environments get reflected into the widgets.

.. release:: 0.2.0
    :date: 2016-01-08

    .. change:: new

        Initial release of ftrack connect maya plugin.
