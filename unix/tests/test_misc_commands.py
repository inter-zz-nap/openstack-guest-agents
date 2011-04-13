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

import agent_test
import agentlib


class TestMiscCommands(agent_test.TestCase):

    def test_features(self):
        """Test the 'features' command"""

        resp = self.commands.run_command('features', 'agent')
        expected = (0, ','.join(self.commands.command_names()))
        self.assertEqual(resp, expected)

    def test_version(self):
        """Test the 'version' command"""

        resp = self.commands.run_command('version', 'agent')
        expected = (0, agentlib.get_version())
        self.assertEqual(resp, expected)

if __name__ == "__main__":
    agent_test.main()
