..
    :copyright: Copyright (c) 2015 ftrack

.. _installing:

**********
Installing
**********

Using ftrack Connect
====================

The primary way of installing and launching the Maya integration is
through the ftrack Connect package. Go to 
`ftrack Connect package <https://www.ftrack.com/portfolio/connect>`_ and
download it for your platform.

.. seealso::

    Once ftrack Connect package is installed please follow this
    :ref:`article <using/launching>` to launch Maya with the ftrack
    integration.


Building from source
====================

You can also build manually from the source for more control. First obtain a
copy of the source by either downloading the
`zipball <https://bitbucket.org/ftrack/ftrack-connect-maya/get/master.zip>`_ or
cloning the public repository::

    git clone git@bitbucket.org:ftrack/ftrack-connect-maya.git

Then you can build and install the package into your current Python
site-packages folder::

    python setup.py build_plugin

The result plugin will then be available under the build folder.
Copy or symlink the result plugin folder in your FTRACK_CONNECT_PLUGIN_PATH.


Building documentation from source
----------------------------------

To build the documentation from source::

    python setup.py build_sphinx

Then view in your browser::

    file:///path/to/ftrack-connect-maya/build/doc/html/index.html

Dependencies
============

* `Python <http://python.org>`_ >= 2.6, < 3
* `ftrack connect <https://bitbucket.org/ftrack/ftrack-connect>`_ >= 0.1.2, < 2
* `Maya <http://www.autodesk.com/products/maya/overview>`_ >= 2014, <= 2019

Additional For building
-----------------------

* `Sphinx <http://sphinx-doc.org/>`_ >= 1.2.2, < 2
* `sphinx_rtd_theme <https://github.com/snide/sphinx_rtd_theme>`_ >= 0.1.6, < 1
