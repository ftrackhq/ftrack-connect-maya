..
    :copyright: Copyright (c) 2015 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: Upcoming

    .. change:: changed

        Import type of scenes are determined initially from file type.

    .. change:: changed
       :tags: Internal

       Enforce QtExt minimum version in setup.

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
