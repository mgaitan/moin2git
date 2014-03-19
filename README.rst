moin2git
========

A tool to migrate a MoinMoin wiki as a Git repository.

Hopefully to be done and used at the `PyCamp <2014 http://python.org.ar/PyCamp/2014>`_ to migrate the `website of Python Argentina <http://python.org.ar/>`_  (because... `moin must die`_).

.. attention:: there is nothing but info and ideas, yet


Dive in
-------

MoinMoin_ is a wiki engine powered by Python that store its content
(including pages, history of changes and users) as flat files under
the directory ``/data``.

An overview of the structure of this tree is this::

    data/
    ├── cache
    │   │     ...
    │
    ├── pages
    │   │
    │   ├── AdoptaUnNewbie
    │   │   ├── cache
    │   │   │   ├── hitcounts
    │   │   │   ├── pagelinks
    │   │   │   └── text_html
    │   │   ├── current
    │   │   ├── edit-lock
    │   │   ├── edit-log
    │   │   └── revisions
    │   │       ├── 00000001
    │   │       ├── 00000002
    │   │       ├── 00000003
    │   │       ├── 00000004
    │   │
    │   ├── AlejandroJCura
    │   │   ├── cache
    │   │   │   ├── pagelinks
    │   │   │   └── text_html
    │   │   ├── current
    │   │   ├── edit-lock
    │   │   ├── edit-log
    │   │   └── revisions
    │   │       ├── 00000001
    │   │       ├── 00000002
    │   │       └── 00000003
    │   │ 
    │   ├── AlejandroJCura(2f)ClassDec(c3b3)
    │   │   ├── cache
    │   │   │   ├── pagelinks
    │   │   │   └── text_html
    │   │   ├── current
    │   │   ├── edit-lock
    │   │   ├── edit-log
    │   │   └── revisions
    │   │       ├── 00000001
    │   │       ├── 00000002
    │   │       └── 00000003
     ...
    │   └── YynubJakyfe
    │       ├── edit-lock
    │       └── edit-log
    │
    └── user
        ├── 1137591729.59.35593
        ├── 1137611536.06.62624
        ├── 1138297101.79.62731
        ├── 1138912320.61.21990
        ├── 1138912840.93.11353
        ├── 1140549890.71.33402
        ├── 1140635789.97.15153
        ...

(In advance) autopsy
--------------------

- Each wiki page (no matter how *deep* be its url) is stored in a directory
  ``/data/pages/<URL>``. For example in our example the url
  ``/AlejandroJCura/ClassDec%C3%B3`` [1]_ is ``data/pages/AlejandroJCura(2f)ClassDec(c3b3)``

- The content itself is in the directory ``/revisions``, describing
  the history of a page. Each file in this directory is a full version of a the page (not a diff). The date of last modification of each file,
  is the revision date.

- The file ``/data/pages/<URL>/current`` works as a pointer to the current
  revision (in general, the more recent one, but a page could be "restored" to an older revision). For example:

  .. code-block:: bash

      tin@morochita:~/lab/moin$ cat data/pages/AlejandroJCura/current
      00000003

- The ``edit-log`` file describes *who*, *when* and (if there is
  a log a message) *why*:

  .. code-block:: bash

      tin@morochita:~/lab/moin$ cat data/pages/AlejandroJCura/edit-log
        1141363609000000    00000001    SAVENEW AlejandroJCura  201.235.8.161   161-8-235-201.fibertel.com.ar   1140672427.37.17771     Una pagina para mi?
        1155690306000000    00000002    SAVE    AlejandroJCura  201.231.181.174 174-181-231-201.fibertel.com.ar 1140672427.37.17771
        1218483772000000    00000003    SAVE    AlejandroJCura  201.250.38.50   201-250-38-50.speedy.com.ar 1140672427.37.17771

  The data logged is (in this order):

    ``EDITION_ID``, ``REVISION``, ``ACTION``, ``PAGE``, ``IP``, ``HOST``, ``USER_ID``, ``LOG_MESSAGE``

- The ``USER_ID`` point to a file under the directory ``/data/user`` contained a lot of information related to the user. For example:


    .. code-block:: bash

        (preciosa)tin@morochita:~/lab/moin$ cat data/user/1140549890.71.33402
        remember_me=1
        theme_name=pyar
        editor_default=text
        show_page_trail=1
        disabled=0
        quicklinks[]=Noticias
        css_url=
        edit_rows=20
        show_nonexist_qm=0
        show_fancy_diff=1
        tz_offset=-10800
        subscribed_pages[]=
        aliasname=
        remember_last_visit=0
        enc_password={SHA}5kXNi+HjaTCGItkg6yTPNRtSDGE=
        email=mautuc@yahoo(....)
        show_topbottom=0
        editor_ui=freechoice
        datetime_fmt=
        want_trivial=0
        last_saved=1219176737.74
        wikiname_add_spaces=0
        name=MauricioFerrari
        language=
        show_toolbar=1
        edit_on_doubleclick=0
        date_fmt=
        mailto_author=0
        bookmarks{}=

Solving the puzzle
------------------

We will use git to handle the *history*, so don't need files to track
revision nor users: just pages.

For instance,  in the root of our target directory (the git repo) we should
get a file ``AlejandroJCura``:

 - 3 revisions (commits), from ``revisions/00000001`` until ``revisions/00000003``
 - the committer name/nickname and email (if available) will be parsed from the user file of each revision. To know who do what revision, we will parse the ``edit-log`` file.
 - The date of each commit will be extracted from the last-modified date of each revision file.

We should also get a file ``AlejandroJCura/ClassDecó`` [2]_ where, in this case, ``AlejandroJCura/`` is a directory.


What to use
-------------

There are many python wrappers for git libraries. The most promoted is
pygit2_, wich probably is the faster one (because it's based on libgit2_ library). However, I choose GitPython_ for Waliki_ because it has a higher level API and a pretty useful fallback to git's executables (wrappers via subprocess) for the those deep and obscure corners.



.. [1] http://python.org.ar/AlejandroJCura/ClassDec%C3%B3
.. [2] Note we should parse the ugly escaping. ``(2f)`` is ``/`` and determines the left part is a directory. ``(c3b3)`` means ``%C3%B3``, i.e. ``ó``

.. _MoinMoin: http://moinmo.in/
.. _moin must die: Muerte_a_Moin_Moin_.2BAC8ALw_django-waliki_.3F
.. _pygit2: http://www.pygit2.org/
.. _libgit2: http://libgit2.github.com/
.. _GitPython: https://pythonhosted.org/GitPython/0.3.1/index.html
.. _Waliki: https://github.com/mgaitan/waliki/