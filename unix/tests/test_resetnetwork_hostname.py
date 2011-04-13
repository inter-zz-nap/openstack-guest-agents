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
resetnetwork hostname tester
"""

import os
import unittest
from cStringIO import StringIO

import commands.redhat.network
import commands.debian.network
import commands.arch.network
import commands.gentoo.network
import commands.suse.network


class TestHostNameUpdates(unittest.TestCase):

    def _run_test(self, dist, hostname, infile=None):
        mod = getattr(commands, dist).network
        if infile:
            return mod.get_hostname_file(infile, hostname)
        else:
            return mod.get_hostname_file(hostname)

    def test_redhat_add_entry(self):
        """Test adding hostname to Red Hat /etc/sysconfig/network"""
        infile = StringIO('NETWORKING=yes\n' +
            'NETWORKING_IPV6=yes\n')
        data = self._run_test('redhat', 'example', infile)
        self.assertEqual(data, 'NETWORKING=yes\n' +
            'NETWORKING_IPV6=yes\n' +
            'HOSTNAME=example\n')

    def test_redhat_update_entry(self):
        """Test updating hostname in Red Hat /etc/sysconfig/network"""
        infile = StringIO('NETWORKING=yes\n' +
            'NETWORKING_IPV6=yes\n' +
            'HOSTNAME=other\n')
        data = self._run_test('redhat', 'example', infile)
        self.assertEqual(data, 'NETWORKING=yes\n' +
            'NETWORKING_IPV6=yes\n' +
            'HOSTNAME=example\n')

    def test_debian(self):
        """Test updating hostname in Debian /etc/hostname"""
        data = self._run_test('debian', 'example')
        self.assertEqual(data, 'example\n')

    def test_arch_add_entry(self):
        """Test adding hostname to Arch Linux /etc/rc.conf"""
        infile = StringIO('eth0="eth0 192.0.2.42 netmask 255.255.255.0"\n' +
            'INTERFACES=(eth0)\n')
        data = self._run_test('arch', 'example', infile)
        self.assertEqual(data,
            'eth0="eth0 192.0.2.42 netmask 255.255.255.0"\n' +
            'INTERFACES=(eth0)\n' +
            'HOSTNAME="example"\n')

    def test_arch_update_entry(self):
        """Test updating hostname in Arch Linux /etc/rc.conf"""
        infile = StringIO('eth0="eth0 192.0.2.42 netmask 255.255.255.0"\n' +
            'INTERFACES=(eth0)\n' +
            'HOSTNAME="other"\n')
        data = self._run_test('arch', 'example', infile)
        self.assertEqual(data,
            'eth0="eth0 192.0.2.42 netmask 255.255.255.0"\n' +
            'INTERFACES=(eth0)\n' +
            'HOSTNAME="example"\n')

    def test_gentoo(self):
        """Test updating hostname in Gentoo /etc/conf.d/hostname"""
        data = self._run_test('gentoo', 'example')
        self.assertEqual(data,
            '# Automatically generated, do not edit\n' +
            'HOSTNAME="example"\n')

    def test_suse(self):
        """Test updating hostname in SuSE /etc/HOSTNAME"""
        data = self._run_test('suse', 'example')
        self.assertEqual(data, 'example\n')


if __name__ == "__main__":
    agent_test.main()
