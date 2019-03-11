.. role:: raw-html(raw)
   :format: html

githack
=======

.. image:: https://badge.fury.io/gh/owenchia%2Fgithack.svg
    :target: https://github.com/owenchia/githack
.. image:: https://travis-ci.com/OwenChia/githack.svg?branch=master
    :target: https://travis-ci.com/OwenChia/githack
.. image:: https://badge.fury.io/py/githack.svg
    :target: https://pypi.org/project/githack/
.. image:: https://img.shields.io/pypi/pyversions/githack.svg
    :alt: PyPI - Python Version
    :target: https://pypi.org/project/githack/
.. image:: https://img.shields.io/github/license/owenchia/githack.svg
    :alt: GitHub
    :target: ./LICENSE

Basically it an py3k version with own implemented Git objects parser for `GitHack <https://github.com/lijiejie/GitHack>`_:

::

  GitHack is a `.git` folder disclosure exploit.

**Why another git dumper tool?**

- python 3.6+ support
- pure-Python implementation without third-party dependencies
- git database crawling support
- zipapp mode support

**How it works?**

- step 1:
  fetch metadata (eg. .git/{HEAD,index,config})
- step 2:
  using commit objects as seed, crawling whole git database
- step 3:
  parse index, then restore objects to source code

**Usage:**

- portable standalone

  > make zipapp

  > python githack.pyz \http://example.com/.git

- pip

  > pip install githack

  > githack \http://example.com/.git

**Known Issues:**

- :raw-html:`<del><a href="https://github.com/OwenChia/githack/issues/1">worrong file permissions</a></del>`
