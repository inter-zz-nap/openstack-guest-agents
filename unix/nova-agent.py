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

# Needed to register the exchange/parser plugin combiniation with the
# main daemon
import agentlib

# To get jsonparser and xscomm
import plugins

# Loads 'commands' plus all modules that contain command classes
import commands.command_list

# Not required, as the default is False
test_mode = False

# Inits all command classes
c = commands.init()

# Creates instance of JsonParser, passing in available commands
parser = plugins.JsonParser(c)
# Create the XSComm intance
xs = plugins.XSComm()

# Register an exchange/parser combination with the main daemon
agentlib.register(xs, parser)
