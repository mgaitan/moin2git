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
import sh
import docopt
import os
import re
import json
from urllib2 import unquote

__version__ = "0.1"
arguments = docopt.docopt(__doc__, version=__version__)


def unflat(encoded):
    chunks = re.findall('\(([a-f0-9]{2,4})\)', encoded)
    for chunk in chunks:
        encoded = encoded.replace('(' + chunk + ')', '%' + "%".join(re.findall('..', chunk)))
    return unquote(encoded)


def parse_users():
    users = {}
    users_dir = os.path.join(arguments['<data_dir>'], 'user')
    for autor in os.listdir(users_dir):
        data = open(os.path.join(users_dir, autor)).read()

        users[autor] = dict(re.findall(r'^([a-z_]+)=(.*)$', data, flags=re.MULTILINE))
    return users


def main():
    print(arguments)


if __name__ == '__main__':

    if arguments['--users']:
        print json.dumps(parse_users(), sort_keys=True, indent=2)
    else:
        print(arguments)
