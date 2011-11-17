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
import commands
import plugins.jsonparser

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.CRITICAL)


class TestJsonParser(agent_test.TestCase):

    def setUp(self):
        super(TestJsonParser, self).setUp()
        self.jsonparser = plugins.jsonparser.JsonParser(self.commands)

    def test_1_no_data_in_req(self):
        """Test jsonparser 'data' key missing"""

        resp = self.jsonparser.parse_request({'moo': 'ok'})

        data = '{"message": "Internal error with request", ' + \
                '"returncode": "500"}'

        self.assertEqual(resp, {"data": data})

    def test_2_malformed_command(self):
        """Test jsonparser 'data' value not JSONs tring"""

        resp = self.jsonparser.parse_request({'data': 'abc'})

        data = '{"message": "Request is malformed", "returncode": "500"}'

        self.assertEqual(resp, {"data": data})

    def test_3_no_command(self):
        """Test jsonparser no command"""

        resp = self.jsonparser.parse_request({"data": '{"value":""}'})

        data = '{"message": "Request is missing \'name\' key", ' + \
                '"returncode": "500"}'

        self.assertEqual(resp, {"data": data})

    def test_4_unknown_command(self):
        """Test jsonparser unknown command"""

        resp = self.jsonparser.parse_request({"data": \
                '{"name": "<unknown_command>", "value": ""}'})

        data = '{"message": "No such agent command ' + \
                '\'<unknown_command>\'", "returncode": "404"}'

        self.assertEqual(resp, {"data": data})

if __name__ == "__main__":
    agent_test.main()
