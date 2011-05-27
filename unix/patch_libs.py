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

    # Patching libraries on FreeBSD results in .so's that libelf
    # can't load.  It's a dumbness with libelf implementation
    if os.uname()[0] == 'FreeBSD':
        sys.exit(0)

    directory = sys.argv[1]
    libdir = sys.argv[2]

    patch_libs(directory, libdir)
