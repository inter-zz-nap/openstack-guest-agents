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
Misc commands tester
"""

# This is to support older python versions that don't have hashlib
try:
    import hashlib
except ImportError:
    import md5

    class hashlib(object):
        """Fake hashlib module as a class"""

        @staticmethod
        def md5():
            return md5.new()

import os

import agent_test
import agentlib
import commands.update


class TestUpdateCommand(agent_test.TestCase):

    def setUp(self):
        super(TestUpdateCommand, self).setUp()
        self.update_inst = self.commands.command_instance("agentupdate")

    def test_1_valid_md5(self):
        """Test 'update' command's ability to get a file from a URL
        and verify valid MD5
        """

        test_file = os.path.abspath(__file__)

        f = file(test_file, 'rb')

        m = hashlib.md5()
        while True:
            file_data = f.read(8096)
            if not file_data:
                break
            m.update(file_data)
        f.close()

        md5sum = m.hexdigest()
        url = "file://" + test_file

        local_file = self.update_inst._get_to_local_file(url, md5sum)

        # Compare md5 against original

        f = file(local_file)

        m = hashlib.md5()
        while True:
            file_data = f.read(8096)
            if not file_data:
                break
            m.update(file_data)
        f.close()

        os.unlink(local_file)

        self.assertEqual(md5sum, m.hexdigest())

    def test_2_invalid_md5(self):
        """Test 'update' command's ability to get a file from a URL
        and verify valid MD5
        """

        test_file = os.path.abspath(__file__)
        url = "file://" + test_file

        self.assertRaises(commands.update.AgentUpdateError,
                self.update_inst._get_to_local_file, url, 'bogus')


if __name__ == "__main__":
    agent_test.main()
