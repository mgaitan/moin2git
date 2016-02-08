#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""moin2git.py

A tool to migrate the content of a MoinMoin wiki to a Git based system
like Waliki, Gollum or similar.

Usage:
  moin2git.py migrate <data_dir> <git_repo> [--convert-to-rst]
  moin2git.py users <data_dir>
  moin2git.py attachments <data_dir> <dest_dir>

Arguments:
    data_dir  Path where your MoinMoin content are
    git_repo  Path to the target repo (created if it doesn't exist)
    dest_dir  Path to copy attachments (created if it doesn't exist)

Options:
    --convert-to-rst    After migrate, convert to reStructuredText
"""
from sh import git, python, ErrorReturnCode_1
import docopt
import os
import re
import json
from datetime import datetime
from urllib2 import unquote
import shutil

__version__ = "0.1"
PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))


def _unquote(encoded):
    """
    >>> _unquote("Tom(c3a1)s(20)S(c3a1)nchez(20)Garc(c3ad)a")
    Tomás Sánchez García
    """
    chunks = re.findall('\(([a-f0-9]{2,4})\)', encoded)
    for chunk in chunks:
        encoded = encoded.replace('(' + chunk + ')', '%' + "%".join(re.findall('..', chunk)))
    return unquote(encoded)


def parse_users(data_dir=None):
    if not data_dir:
        data_dir = arguments['<data_dir>']
    users = {}
    users_dir = os.path.join(data_dir, 'user')
    for autor in os.listdir(users_dir):
        try:
            data = open(os.path.join(users_dir, autor)).read()
        except IOError:
            continue

        users[autor] = dict(re.findall(r'^([a-z_]+)=(.*)$', data, flags=re.MULTILINE))
    return users


def get_versions(page, users=None, data_dir=None, convert=False):
    if not data_dir:
        data_dir = arguments['<data_dir>']
    if not users:
        users = parse_users(data_dir)
    versions = []
    path = os.path.join(data_dir, 'pages', page)
    log = os.path.join(path, 'edit-log')
    if not os.path.exists(log):
        return versions
    log = open(log).read()
    if not log.strip():
        return versions

    logs_entries = [l.split('\t') for l in log.split('\n')]
    for entry in logs_entries:
        if len(entry) != 9:
            continue
        try:
            content = open(os.path.join(path, 'revisions', entry[1])).read()
        except IOError:
            continue

        date = datetime.fromtimestamp(int(entry[0][:-6]))
        comment = entry[-1]
        email = users.get(entry[-3], {}).get('email', 'an@nymous.com')
        # look for name, username. default to IP
        name = users.get(entry[-3], {}).get('name', None) or users.get(entry[-3], {}).get('username', entry[-5])

        versions.append({'date': date, 'content': content,
                         'author': "%s <%s>" % (name, email),
                         'm': comment,
                         'revision': entry[1]})
    if not convert:
        try:
            convert = arguments['--convert-to-rst']
        except NameError:
            convert = False

    if convert:
        conversor = os.path.join(PACKAGE_ROOT, "moin2rst", "moin2rst.py")
        basedir = os.path.abspath(os.path.join(data_dir, '..', '..'))
        try:
            rst = python(conversor, _unquote(page), d=basedir)

            versions.append({'m': 'Converted to reStructuredText via moin2rst',
                         'content': rst.stdout,
                         'revision': 'Converting to rst'})
        except ErrorReturnCode_1:
            print("Couldn't convert %s to rst" % page)


    return versions


def migrate_to_git():
    users = parse_users()
    git_repo = arguments['<git_repo>']

    if not os.path.exists(git_repo):
        os.makedirs(git_repo)
    if not os.path.exists(os.path.join(git_repo, '.git')):
        git.init(git_repo)

    data_dir = os.path.abspath(arguments['<data_dir>'])
    root = os.path.join(data_dir, 'pages')
    pages = os.listdir(root)
    os.chdir(git_repo)
    for page in pages:
        versions = get_versions(page, users=users, data_dir=data_dir)
        if not versions:
            print("### ignoring %s (no revisions found)" % page)
            continue
        path = _unquote(page) + '.rst'
        print("### Creating %s\n" % path)
        dirname, basename = os.path.split(path)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)

        for version in versions:
            print("revision %s" % version.pop('revision'))
            with open(path, 'w') as f:
                f.write(version.pop('content'))
            try:
                git.add(path)
                git.commit(path, allow_empty_message=True, **version)
            except:
                pass


def copy_attachments():
    dest_dir = arguments['<dest_dir>']

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    root = os.path.abspath(os.path.join(arguments['<data_dir>'], 'pages'))
    pages = os.listdir(root)
    # os.chdir(dest_dir)
    for page in pages:
        attachment_dir = os.path.join(root, page, 'attachments')
        if not os.path.exists(attachment_dir):
            continue
        print("Copying attachments for %s" % page)
        path = _unquote(page)
        dest_path = os.path.join(dest_dir, path)
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        for f in os.listdir(attachment_dir):
            print(".. %s" % f)
            full_file_name = os.path.join(attachment_dir, f)
            shutil.copy(full_file_name, dest_path)


if __name__ == '__main__':

    arguments = docopt.docopt(__doc__, version=__version__)

    if arguments['users']:
        print(json.dumps(parse_users(), sort_keys=True, indent=2))
    elif arguments['migrate']:
        migrate_to_git()
    elif arguments['attachments']:
        copy_attachments()
