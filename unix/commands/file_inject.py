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

"""
JSON File injection plugin
"""

import base64
import commands
import os
import os.path
import time


class FileInject(commands.CommandBase):

    def __init__(self, *args, **kwargs):
        pass

    @commands.command_add('injectfile')
    def injectfile_cmd(self, data):

        try:
            b64_decoded = base64.b64decode(data)
        except:
            return (500, "Error doing base64 decoding of data")

        (filename, data) = b64_decoded.split(',', 1)

        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        tempfilename = filename + '.tmp.%s' % time.time()

        f = open(tempfilename, 'w')
        f.write(data)
        f.close()

        os.chown(tempfilename, 0, 0)
        os.chmod(tempfilename, 0644)

        if os.path.exists(filename):
            # Backup old file first
            os.rename(filename, filename + '.bak.%s' % time.time())

        os.rename(tempfilename, filename)

        return (0, "")
