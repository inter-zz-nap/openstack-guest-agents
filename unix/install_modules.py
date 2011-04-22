#!/usr/bin/env python

import os
import shutil
import sys

import commands.command_list

# Other modules here that get lazy loaded.. :-/
import httplib
import zlib
import gzip
import bz2


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
            # Turn /usr/lib/python2.6/Crypto/Cipher/AES into:
            # /usr/lib/python2.6/Crypto
            rest_dir = mod_fn[len(base_dir) + 1:]
            if '/' in rest_dir:
                rest_dir = rest_dir.split('/', 1)[0]
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
        os.makedirs(installdir)
    elif not os.path.isdir(installdir):
        print "Error: '%s' exists and is not a directory" % installdir
        sys.exit(1)

    install_modules(sys_paths, installdir)
