Prerequisites
=============

* OS Linux
* Python version 2.7

Preinstalled packages
---------------------

Included to module installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* :mod:`sh` module for Python
* :mod:`mechanize` module for Python
* :mod:`requests` module for Python


Optional (used for special VCS types)
-------------------------------------

Perforce
~~~~~~~~

* p4 CLI (see `official installation manual
  <https://www.perforce.com/perforce/doc.current/manuals/p4sag/chapter.install.html#install.linux.packages>`__
  for details)
* P4Python (see `official installation manual
  <https://www.perforce.com/helix-p4python-package-repositories-overview>`__ for details)

Git
~~~

* `Git` client (use ``sudo apt-get install git``)
* :mod:`gitpython` module for Python (use ``sudo pip install gitpython``)


Optional (used for internal tests)
----------------------------------

Need to be installed manually
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Docker (Right now only used for internal tests. See `official installation manual
  <https://docs.docker.com/engine/installation/linux/ubuntu/#install-using-the-repository>`__ for details)
* PIP version 9.0 or greater (See `official installation manual
  <https://pip.pypa.io/en/stable/installing/>`__ for details)


Included to module installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* :mod:`pytest` module for Python
* :mod:`pylint` module for Python
* :mod:`docker` module for Python
* :mod:`httpretty` module for Python
* :mod:`mock` module for Python
* :mod:`sphinx` module for Python
* :mod:`sphinx-argparse` extension for Sphinx module
