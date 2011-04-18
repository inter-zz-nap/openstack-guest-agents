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

import base64
import os

import agent_test
import agentlib


class InjectFileTests(agent_test.TestCase):
    """InjectFile tests"""

    def test_random_data(self):
        """Test 'injectfile' with a random binary data filled file"""

        file_data = os.urandom(2048)

        file_path = os.getcwd() + "/file_inject_test.%d" % os.getpid()

        if os.path.exists(file_path):
            os.unlink(file_path)

        b64_arg = base64.b64encode("%s,%s" % (file_path, file_data))

        self.commands.run_command('injectfile', b64_arg)

        self.assertTrue(os.path.exists(file_path))

        f = open(file_path, 'rb')
        target_file_data = f.read()
        f.close()

        self.assertEqual(file_data, target_file_data)

        os.unlink(file_path)

    def test_comma_data(self):
        """Test 'injectfile' with commas in the file"""

        file_data = "test123,456,789\ntest456,789\n"

        file_path = os.getcwd() + "/file_inject_test.%d" % os.getpid()

        if os.path.exists(file_path):
            os.unlink(file_path)

        b64_arg = base64.b64encode("%s,%s" % (file_path, file_data))

        self.commands.run_command('injectfile', b64_arg)

        self.assertTrue(os.path.exists(file_path))

        f = open(file_path, 'rb')
        target_file_data = f.read()
        f.close()

        self.assertEqual(file_data, target_file_data)

        os.unlink(file_path)

if __name__ == "__main__":
    agent_test.main()
