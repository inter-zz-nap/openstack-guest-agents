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
import subprocess
import sys


def execute(*args):
    p = subprocess.Popen(args)
    status = os.waitpid(p.pid, 0)[1]

    if status:
        raise Exception(
                "failed to execute %s: status %d" % ' '.join(args), status)


def patch_binary(binary, libdir, interpreter=None):
    if interpreter:
        execute('patchelf', '--set-interpreter',
                os.path.join(libdir, interpreter), binary)
    execute('patchelf', '--set-rpath', libdir, binary)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Usage: patch_binary.py <binary_name> <dest_dir> <lib_dir>"
        sys.exit(1)

    binary = sys.argv[1]
    destdir = sys.argv[2]
    libdir = sys.argv[3]

    interpreter = filter(lambda f: f.startswith('ld-'),
            os.listdir(destdir + libdir))
    if interpreter:
        interpreter = interpreter[0]

    patch_binary(binary, libdir, interpreter)
