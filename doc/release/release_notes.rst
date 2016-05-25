..
    :copyright: Copyright (c) 2015 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: Upcoming

    .. change:: fixed
        :tags: Api

        Asset without transform nodes doesn’t show in Maya asset manager

    .. change:: fixed
        :tags: Ui

        Cannot switch version of alembic from the asset manager.

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
