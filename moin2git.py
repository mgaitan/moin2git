#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""moin2git.py

A tool to convert the content of a MoinMoin wiki as a Git repository

Usage:
  moin2git.py --users <data_dir>
  moin2git.py [--convert] <data_dir> <git_repo>


Arguments:
    data_dir  Path where your MoinMoin content are
    git_repo  Path to the target repo (created if it doesn't exist)

Options:
    --users         Dump users database as json
    --convert       After migrate, convert to reStructuredText
"""
from sh import git
import docopt
import os
import re
import json
from datetime import datetime
from urllib2 import unquote

__version__ = "0.1"

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
        data = open(os.path.join(users_dir, autor)).read()

        users[autor] = dict(re.findall(r'^([a-z_]+)=(.*)$', data, flags=re.MULTILINE))
    return users


def get_versions(page, users=None, data_dir=None):
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
        email = users.get(entry[-3], {}).get('email', '')
        # look for name, username. default to IP
        name = users.get(entry[-3], {}).get('name', None) or users.get(entry[-3], {}).get('username', '')

        versions.append({'date': date, 'content': content, 'email': email, 'name': name or entry[-5]})

    return versions


def main():
    users = parse_users()


    git_repo = arguments['<git_repo>']
    if not os.path.exists(git_repo):
        os.makedirs(git_repo)

    if not os.path.exists(os.path.join(git_repo, '.git')):
        git.init(git_repo)

    root = os.path.join(arguments['<data_dir>'], 'pages')
    pages = os.listdir(root)


    for page in pages:
        path = _unquote(page)
        dirname, basename = os.path.split(path)
        basename += '.rst'
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        versions_path = os.path.join(root, page, 'versions')
        versions = os.listdir(versions_path)
        for version in versions:
            pass



if __name__ == '__main__':

    arguments = docopt.docopt(__doc__, version=__version__)


    if arguments['--users']:
        print json.dumps(parse_users(), sort_keys=True, indent=2)
    else:
        print(arguments)
