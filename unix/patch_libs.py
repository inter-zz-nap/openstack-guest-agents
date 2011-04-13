#!/usr/bin/env python

import os
import re
import sys
import patch_binary


def patch_libs(directory, libdir):
    """
    Patch all shared libraries found in a directory and subdirectories
    """

    so_re = re.compile('.*\.so(\.\d+)*$')

    for root, dirs, files in os.walk(directory):
        for f in files:
            # Skip the interpreter
            if f.startswith('ld-'):
                continue
            if so_re.match(f):
                fname = root + '/' + f
                print "Patching %s" % fname
                patch_binary.patch_binary(fname, libdir)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage: patch_libs.py <directory> <lib_dir>"
        sys.exit(1)

    directory = sys.argv[1]
    libdir = sys.argv[2]

    patch_libs(directory, libdir)
