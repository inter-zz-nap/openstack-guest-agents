#!/usr/bin/env python

# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
#  Copyright (c) 2011 Openstack, LLC.
#  All Rights Reserved.
#
#     Licensed under the Apache License, Version 2.0 (the "License"); you may
#     not use this file except in compliance with the License. You may obtain
#     a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#     WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#     License for the specific language governing permissions and limitations
#     under the License.
#

import os
import shutil
import re
import sys

import commands.command_list

# Other modules here that get lazy loaded.. :-/
import httplib
import zlib
import gzip
import bz2
# Make sure we get at least one of these
try:
    import anyjson
except Exception:
    pass
try:
    import json
except Exception:
    pass
try:
    import simplejson
except Exception:
    pass


def install_modules(system_paths, installdir):

    c = commands.init(testmode=True)

    to_install = set()

    def copy_tree(srcdir, destdir):
        if not os.path.exists(destdir):
            os.mkdir(destdir)
        for root, dirs, files in os.walk(srcdir):
            for d in dirs:
                if not os.path.exists(os.path.join(destdir, d)):
                    os.mkdir(os.path.join(destdir, d))
            for f in files:
                # Only install .pyc or .sos, etc
                if not f.endswith('.py'):
                    fname = os.path.join(destdir + root[len(srcdir):], f)
                    shutil.copy2(os.path.join(root, f), fname)

    def _do_install(src, destdir):
        print "Installing %s" % src
        if os.path.isdir(src):
            subdir = src.rsplit('/', 1)[1]
            copy_tree(src, os.path.join(destdir, subdir))
        else:
            shutil.copy2(src, destdir)

    # Install any .pth files from site-packages for eggs
    for x in system_paths:
        if x.endswith('site-packages') and os.path.isdir(x):
            files = os.listdir(x)
            for file in files:
                if re.match('.*\.pth$', file):
                    _do_install(os.path.join(x, file),
                            installdir + '/site-packages')

    for modname in sys.modules:

        if modname == "__main__":
            continue

        try:
            mod_fn = sys.modules[modname].__file__
        except:
            continue

        mod_fn = os.path.normpath(mod_fn)
        base_dir = ''

        for p in system_paths:
            p_len = len(p)

            if mod_fn.startswith(p) and p > len(base_dir):
                base_dir = p

        # Only install modules that are in the system paths.  We install
        # our command modules separately.
        if base_dir:
            if base_dir.endswith('site-packages'):
                site = True
            else:
                site = False
            # Turn /usr/lib/python2.6/Crypto/Cipher/AES into:
            # /usr/lib/python2.6/Crypto
            rest_dir = mod_fn[len(base_dir) + 1:]
            if '/' in rest_dir:
                rest_dir = rest_dir.split('/', 1)[0]
            if base_dir.endswith('site-packages'):
                _do_install(os.path.join(base_dir, rest_dir),
                        installdir + '/site-packages')
            else:
                _do_install(os.path.join(base_dir, rest_dir),
                        installdir)

if __name__ == "__main__":
    prog_name = sys.argv[0]

    if len(sys.argv) != 2:
        print "Usage: %s <install_dir>" % prog_name
        sys.exit(1)

    installdir = sys.argv[1]

    sys_paths = sys.path
    # Pop off the first directory, which is the directory of this script.
    # We do this so we can ignore *our* modules, which are installed
    # separately
    sys_paths.pop(0)

    if not os.path.exists(installdir):
        os.makedirs(installdir + '/site-packages')
    elif not os.path.exists(installdir + '/site-packages'):
        os.mkdir(installdir + '/site-packages')
    elif not os.path.isdir(installdir + '/site-packages'):
        print "Error: '%s/site-packages' exists and is not a directory" % \
                installdir
        sys.exit(1)

    install_modules(sys_paths, installdir)
