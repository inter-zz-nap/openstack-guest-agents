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
KMS activation tester
"""

import os
import unittest
from cStringIO import StringIO

import commands.redhat.kms


class TestKMSUpdates(unittest.TestCase):

    def test_redhat_up2date(self):
        """Test updating up2date config for Red Hat"""
        outfiles = commands.redhat.kms.configure_up2date([
            'proxy1.example.com', 'proxy2.example.com'])
        self.assertEqual(outfiles['/etc/sysconfig/rhn/up2date'], '\n'.join([
            '# Automatically generated Red Hat Update Agent config file, '
                'do not edit.',
            '# Format: 1.0',
            'versionOverride[comment]=Override the automatically determined '
                'system version',
            'versionOverride=',
            '',
            'enableProxyAuth[comment]=To use an authenticated proxy or not',
            'enableProxyAuth=0',
            '',
            'networkRetries[comment]=Number of attempts to make at network '
                'connections before giving up',
            'networkRetries=5',
            '',
            'hostedWhitelist[comment]=None',
            'hostedWhitelist=',
            '',
            'enableProxy[comment]=Use a HTTP Proxy',
            'enableProxy=0',
            '',
            'serverURL[comment]=Remote server URL',
            'serverURL=https://proxy1.example.com/XMLRPC;'
                'https://proxy2.example.com/XMLRPC;',
            '',
            'proxyPassword[comment]=The password to use for an authenticated '
                'proxy',
            'proxyPassword=',
            '',
            'noSSLServerURL[comment]=None',
            'noSSLServerURL=http://proxy1.example.com/XMLRPC;'
                'http://proxy2.example.com/XMLRPC;',
            '',
            'proxyUser[comment]=The username for an authenticated proxy',
            'proxyUser=',
            '',
            'disallowConfChanges[comment]=Config options that can not be '
                'overwritten by a config update action',
            'disallowConfChanges=noReboot;sslCACert;useNoSSLForPackages;'
                'noSSLServerURL;serverURL;disallowConfChanges;',
            '',
            'sslCACert[comment]=The CA cert used to verify the ssl server',
            'sslCACert=/usr/share/rhn/RHN-ORG-TRUSTED-SSL-CERT',
            '',
            'debug[comment]=Whether or not debugging is enabled',
            'debug=0',
            '',
            'httpProxy[comment]=HTTP proxy in host:port format, e.g. '
                'squid.redhat.com:3128',
            'httpProxy=',
            '',
            'systemIdPath[comment]=Location of system id',
            'systemIdPath=/etc/sysconfig/rhn/systemid',
            '',
            'noReboot[comment]=Disable the reboot action',
            'noReboot=0']) + '\n')


if __name__ == "__main__":
    agent_test.main()
