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
JSON KMS activation
"""

import os
import platform

import commands
import redhat.kms


class ActivateCommand(commands.CommandBase):

    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def detect_os():
        """
        Return the Linux Distribution or other OS name
        """

        translations = {"redhat": redhat}

        system = os.uname()[0]
        if system == "Linux":
            try:
                system = platform.linux_distribution(None)[0]
            except AttributeError:
                # linux_distribution doesn't exist... try the older
                # call
                system = platform.dist(None)[0]

            # Gentoo returns 'Gentoo Base System', so let's make that
            # something easier to use
            if system:
                system = system.lower().split(' ')[0]

            # Arch Linux returns None for platform.linux_distribution()
            if not system and os.path.exists('/etc/arch-release'):
                system = 'arch'

        if not system:
            return None

        return translations.get(system)

    @commands.command_add('kmsactivate')
    def activate_cmd(self, data):

        os_mod = self.detect_os()
        if not os_mod:
            raise SystemError("Couldn't figure out my OS")

        return os_mod.kms.kms_activate(data)
