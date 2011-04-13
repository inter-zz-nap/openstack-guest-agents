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
Unit test runner
"""

import glob
import logging

import tests.agent_test


logging.basicConfig(level=logging.CRITICAL)

mod_names = glob.glob('tests/test_*.py')

modules = set()

for mod in mod_names:
    modules.add("tests." + mod[:-3].split('/', 1)[1])

tests.agent_test.run_tests(modules)
