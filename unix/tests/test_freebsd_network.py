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
resetnetwork interfaces tester
"""

import os
from cStringIO import StringIO

import agent_test
from commands.freebsd import network


class TestFreeBSDRCConf(agent_test.TestCase):
    """Tests for FreeBSD rc.conf generation"""

    def test_ipv4_0_aliases(self):
        """Test setting public IPv4 for FreeBSD networking"""

        interfaces = [
                {"label":"public",
                    "ips":[
                        {"netmask":"255.255.255.0",
                            "enabled":"1","ip":"10.127.31.38"}],
                    "mac":"40:40:8f:1e:a0:0a",
                    "gateway":"10.127.31.1",
                    "dns":["10.6.24.4","10.6.24.5"]},
                {"label":"private",
                    "ips":[{
                        "netmask":"255.255.224.0",
                        "enabled":"1",
                        "ip":"192.168.2.30"}],
                    "routes":[
                        {"route":"10.176.0.0",
                            "netmask":"255.248.0.0",
                            "gateway":"10.177.96.1"},
                        {"route":"10.191.192.0",
                            "netmask":"255.255.192.0",
                            "gateway":"10.177.96.1"}],
                    "mac":"40:40:a2:87:6e:26"}]

        inputdata = '\n'.join([
            'hostname="oldhostname"',
            'check_quotas="NO"',
            'ipv6_enable="YES"',
            'pf_enable="YES"',
            'pflog_enable="YES"',
            'sshd_enable="YES"',
            'ifconfig_re0="DHCP"',
            'ifconfig_rl0="10.0.1.1 netmask 255.255.255.0 up"',
            'ifconfig_rl0_alias0="10.0.1.2 netmask 255.255.255.255"',
            'dhcpd_enable="YES"',
            'dhcpd_flags="-q"',
            'dhcpd_conf="/usr/local/etc/dhcpd.conf"',
            ''])

        expecteddata = '\n'.join([
            'check_quotas="NO"',
            'pf_enable="YES"',
            'pflog_enable="YES"',
            'sshd_enable="YES"',
            'dhcpd_enable="NO"',
            'hostname=myhostname',
            'ifconfig_xn0="10.127.31.38 netmask 255.255.255.0 up"',
            'ifconfig_xn1="192.168.2.30 netmask 255.255.224.0 up"',
            'route_lan0="-net 10.176.0.0 -netmask 255.248.0.0 10.177.96.1"',
            'route_lan1="-net 10.191.192.0 -netmask 255.255.192.0 ' \
                    '10.177.96.1"',
            'static_routes="lan0,lan1"',
            'defaultrouter="10.127.31.1"',
            ''])

        filedata = network._create_rcconf_file(StringIO(inputdata),
                interfaces, 'myhostname')

        self.assertEqual(filedata, expecteddata)

    def test_ipv4_2_aliases(self):
        """Test setting public IPv4 with an IP alias"""

        interfaces = [
                {"label":"public",
                    "ips":[
                        {"netmask":"255.255.255.0",
                            "enabled":"1","ip":"10.127.31.38"},
                        {"netmask":"255.255.255.0",
                            "enabled":"1","ip":"10.127.32.38"},
                        {"netmask":"255.255.255.255",
                            "enabled":"1","ip":"10.127.32.39"}],
                    "mac":"40:40:8f:1e:a0:0a",
                    "gateway":"10.127.31.1",
                    "dns":["10.6.24.4","10.6.24.5"]},
                {"label":"private",
                    "ips":[{
                        "netmask":"255.255.224.0",
                        "enabled":"1",
                        "ip":"192.168.2.30"}],
                    "routes":[
                        {"route":"10.176.0.0",
                            "netmask":"255.248.0.0",
                            "gateway":"10.177.96.1"},
                        {"route":"10.191.192.0",
                            "netmask":"255.255.192.0",
                            "gateway":"10.177.96.1"}],
                    "mac":"40:40:a2:87:6e:26"}]

        inputdata = '\n'.join([
            'hostname="oldhostname"',
            'check_quotas="NO"',
            'ipv6_enable="YES"',
            'pf_enable="YES"',
            'pflog_enable="YES"',
            'sshd_enable="YES"',
            'ifconfig_re0="DHCP"',
            'ifconfig_rl0="10.0.1.1 netmask 255.255.255.0 up"',
            'ifconfig_rl0_alias0="10.0.1.2 netmask 255.255.255.255"',
            'dhcpd_enable="YES"',
            'dhcpd_flags="-q"',
            'dhcpd_conf="/usr/local/etc/dhcpd.conf"',
            ''])

        expecteddata = '\n'.join([
            'check_quotas="NO"',
            'pf_enable="YES"',
            'pflog_enable="YES"',
            'sshd_enable="YES"',
            'dhcpd_enable="NO"',
            'hostname=myhostname',
            'ifconfig_xn0="10.127.31.38 netmask 255.255.255.0 up"',
            'ifconfig_xn0_alias0="10.127.32.38 netmask 255.255.255.0"',
            'ifconfig_xn0_alias1="10.127.32.39 netmask 255.255.255.255"',
            'ifconfig_xn1="192.168.2.30 netmask 255.255.224.0 up"',
            'route_lan0="-net 10.176.0.0 -netmask 255.248.0.0 10.177.96.1"',
            'route_lan1="-net 10.191.192.0 -netmask 255.255.192.0 ' \
                    '10.177.96.1"',
            'static_routes="lan0,lan1"',
            'defaultrouter="10.127.31.1"',
            ''])

        filedata = network._create_rcconf_file(StringIO(inputdata),
                interfaces, 'myhostname')

        self.assertEqual(filedata, expecteddata)

    def test_ipv4and6_0_aliases(self):
        """Test setting public IPv4 for FreeBSD networking"""

        interfaces = [
                {"label":"public",
                    "ips":[
                        {"netmask":"255.255.255.0",
                            "enabled":"1","ip":"10.127.31.38"}],
                    "ip6s":[
                        {"netmask":"96",
                            "enabled":"1","address":"ffff::2"}],
                    "mac":"40:40:8f:1e:a0:0a",
                    "gateway":"10.127.31.1",
                    "gateway6":"ffff::1",
                    "dns":["10.6.24.4","10.6.24.5"]},
                {"label":"private",
                    "ips":[{
                        "netmask":"255.255.224.0",
                        "enabled":"1",
                        "ip":"192.168.2.30"}],
                    "routes":[
                        {"route":"10.176.0.0",
                            "netmask":"255.248.0.0",
                            "gateway":"10.177.96.1"},
                        {"route":"10.191.192.0",
                            "netmask":"255.255.192.0",
                            "gateway":"10.177.96.1"}],
                    "mac":"40:40:a2:87:6e:26"}]

        inputdata = '\n'.join([
            'hostname="oldhostname"',
            'check_quotas="NO"',
            'ipv6_enable="YES"',
            'pf_enable="YES"',
            'pflog_enable="YES"',
            'sshd_enable="YES"',
            'ifconfig_re0="DHCP"',
            'ifconfig_rl0="10.0.1.1 netmask 255.255.255.0 up"',
            'ifconfig_rl0_alias0="10.0.1.2 netmask 255.255.255.255"',
            'dhcpd_enable="YES"',
            'dhcpd_flags="-q"',
            'dhcpd_conf="/usr/local/etc/dhcpd.conf"',
            ''])

        expecteddata = '\n'.join([
            'check_quotas="NO"',
            'pf_enable="YES"',
            'pflog_enable="YES"',
            'sshd_enable="YES"',
            'dhcpd_enable="NO"',
            'hostname=myhostname',
            'ifconfig_xn0="10.127.31.38 netmask 255.255.255.0 up"',
            'ipv6_ifconfig_xn0="ffff::2/96"',
            'ifconfig_xn1="192.168.2.30 netmask 255.255.224.0 up"',
            'route_lan0="-net 10.176.0.0 -netmask 255.248.0.0 10.177.96.1"',
            'route_lan1="-net 10.191.192.0 -netmask 255.255.192.0 ' \
                    '10.177.96.1"',
            'static_routes="lan0,lan1"',
            'ipv6_enable="YES"',
            'ipv6_network_interfaces="xn0"',
            'defaultrouter="10.127.31.1"',
            'ipv6_defaultrouter="ffff::1"',
            ''])

        filedata = network._create_rcconf_file(StringIO(inputdata),
                interfaces, 'myhostname')

        self.assertEqual(filedata, expecteddata)

    def test_ipv4and6_2_aliases(self):
        """Test setting public IPv4 with an IP alias"""

        interfaces = [
                {"label":"public",
                    "ips":[
                        {"netmask":"255.255.255.0",
                            "enabled":"1","ip":"10.127.31.38"},
                        {"netmask":"255.255.255.0",
                            "enabled":"1","ip":"10.127.32.38"},
                        {"netmask":"255.255.255.255",
                            "enabled":"1","ip":"10.127.32.39"}],
                    "ip6s":[
                        {"netmask":"96",
                            "enabled":"1","address":"ffff::2"},
                        {"netmask":"96",
                            "enabled":"1","address":"ffff::1:2"},
                        {"netmask":"128",
                            "enabled":"1","address":"ffff::1:3"}],
                    "mac":"40:40:8f:1e:a0:0a",
                    "gateway":"10.127.31.1",
                    "gateway6":"ffff::1",
                    "dns":["10.6.24.4","10.6.24.5"]},
                {"label":"private",
                    "ips":[{
                        "netmask":"255.255.224.0",
                        "enabled":"1",
                        "ip":"192.168.2.30"}],
                    "routes":[
                        {"route":"10.176.0.0",
                            "netmask":"255.248.0.0",
                            "gateway":"10.177.96.1"},
                        {"route":"10.191.192.0",
                            "netmask":"255.255.192.0",
                            "gateway":"10.177.96.1"}],
                    "mac":"40:40:a2:87:6e:26"}]

        inputdata = '\n'.join([
            'hostname="oldhostname"',
            'check_quotas="NO"',
            'ipv6_enable="YES"',
            'pf_enable="YES"',
            'pflog_enable="YES"',
            'sshd_enable="YES"',
            'ifconfig_re0="DHCP"',
            'ifconfig_rl0="10.0.1.1 netmask 255.255.255.0 up"',
            'ifconfig_rl0_alias0="10.0.1.2 netmask 255.255.255.255"',
            'dhcpd_enable="YES"',
            'dhcpd_flags="-q"',
            'dhcpd_conf="/usr/local/etc/dhcpd.conf"',
            ''])

        expecteddata = '\n'.join([
            'check_quotas="NO"',
            'pf_enable="YES"',
            'pflog_enable="YES"',
            'sshd_enable="YES"',
            'dhcpd_enable="NO"',
            'hostname=myhostname',
            'ifconfig_xn0="10.127.31.38 netmask 255.255.255.0 up"',
            'ipv6_ifconfig_xn0="ffff::2/96"',
            'ifconfig_xn0_alias0="10.127.32.38 netmask 255.255.255.0"',
            'ipv6_ifconfig_xn0_alias0="ffff::1:2/96"',
            'ifconfig_xn0_alias1="10.127.32.39 netmask 255.255.255.255"',
            'ipv6_ifconfig_xn0_alias1="ffff::1:3/128"',
            'ifconfig_xn1="192.168.2.30 netmask 255.255.224.0 up"',
            'route_lan0="-net 10.176.0.0 -netmask 255.248.0.0 10.177.96.1"',
            'route_lan1="-net 10.191.192.0 -netmask 255.255.192.0 ' \
                    '10.177.96.1"',
            'static_routes="lan0,lan1"',
            'ipv6_enable="YES"',
            'ipv6_network_interfaces="xn0"',
            'defaultrouter="10.127.31.1"',
            'ipv6_defaultrouter="ffff::1"',
            ''])

        filedata = network._create_rcconf_file(StringIO(inputdata),
                interfaces, 'myhostname')

        self.assertEqual(filedata, expecteddata)

if __name__ == "__main__":
    agent_test.main()
