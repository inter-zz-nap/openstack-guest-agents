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
Nova agent unit test module
"""

import unittest
import sys


class TestCase(unittest.TestCase):

    def setUp(self):

        self.commands_cls = __import__("commands.command_list")
        kwargs = getattr(self, 'command_kwargs', {})
        self.commands = self.commands_cls.init(testmode=True,
                tmpdir="/tmp", **kwargs)


def run_tests(modules):

    if isinstance(modules, str):
        modules = [modules]

    test_suite = unittest.TestLoader().loadTestsFromNames(modules)
    unittest.TextTestRunner(verbosity=2).run(test_suite)


def main(*args, **kwargs):
    kwargs['testRunner'] = unittest.TextTestRunner(verbosity=2)
    unittest.main(*args, **kwargs)

if __name__ != "__main__":
    if not len(sys.path) or sys.path[0] != "..":
        sys.path.insert(0, "..")
