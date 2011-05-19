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
FreeBSD network helper module
"""

import os
import re
import time
import subprocess
import logging
from cStringIO import StringIO

import commands.network

RESOLV_FILE = "/etc/resolv.conf"
RCCONF_FILE = "/etc/rc.conf"

INTERFACE_LABELS = {"public": "xn0",
                    "private": "xn1"}


def configure_network(network_config, *args, **kwargs):

    update_files = {}

    # Generate new interface files
    interfaces = network_config.get('interfaces', [])

    # Generate new hostname file
    hostname = network_config.get('hostname')

    # Generate new /etc/rc.conf
    data = _get_file_data(interfaces, hostname)
    update_files[RCCONF_FILE] = data

    # Generate new /etc/resolv.conf file
    data = _get_resolv_conf(interfaces)
    update_files[RESOLV_FILE] = data

    # Generate new /etc/hosts file
    filepath, data = commands.network.get_etc_hosts(interfaces, hostname)
    update_files[filepath] = data

    # Write out new files
    commands.network.update_files(update_files)

    # Set hostname
    logging.debug('executing /bin/hostname %s' % hostname)
    p = subprocess.Popen(["/bin/hostname", hostname])
    logging.debug('waiting on pid %d' % p.pid)
    status = os.waitpid(p.pid, 0)[1]
    logging.debug('status = %d' % status)

    if status != 0:
        return (500, "Couldn't set hostname: %d" % status)

    # Restart network
    logging.debug('executing /etc/rc.d/netif restart')
    p = subprocess.Popen(["/etc/rc.d/netif", "restart"])
    logging.debug('waiting on pid %d' % p.pid)
    status = os.waitpid(p.pid, 0)[1]
    logging.debug('status = %d' % status)

    if status != 0:
        return (500, "Couldn't restart IPv4 networking: %d" % status)

    # Restart network
    logging.debug('executing /etc/rc.d/network_ipv6 restart')
    p = subprocess.Popen(["/etc/rc.d/network_ipv6", "restart"])
    logging.debug('waiting on pid %d' % p.pid)
    status = os.waitpid(p.pid, 0)[1]
    logging.debug('status = %d' % status)

    if status != 0:
        return (500, "Couldn't restart IPv6 networking: %d" % status)

    return (0, "")


def _get_resolv_conf(interfaces):
    resolv_data = ''
    for interface in interfaces:
        if interface['label'] != 'public':
            continue

        for nameserver in interface.get('dns', []):
            resolv_data += 'nameserver %s\n' % nameserver

    if not resolv_data:
        return ''

    return '# Automatically generated, do not edit\n' + resolv_data


def _create_rcconf_file(infile, interfaces, hostname):
    """
    Return new rc.conf, merging in 'infile'
    """

    ipv6_interfaces = ''
    static_route_entries = []
    defaultrouter = ''
    ipv6_defaultrouter = ''

    outfile = StringIO()

    for line in infile:
        line = line.strip()
        if line.startswith("ifconfig") or \
                line.startswith("defaultrouter") or \
                line.startswith("ipv6_ifconfig") or \
                line.startswith("ipv6_defaultrouter") or \
                line.startswith("ipv6_enable") or \
                line.startswith("static_routes") or \
                line.startswith("route_") or \
                line.startswith("dhcpd_") or \
                line.startswith("hostname"):
            continue
        print >> outfile, line

    print >> outfile, 'dhcpd_enable="NO"'
    print >> outfile, 'hostname=%s' % hostname

    for interface in interfaces:
        try:
            label = interface['label']
        except KeyError:
            raise SystemError("No interface label found")

        try:
            ifname_prefix = INTERFACE_LABELS[label]
        except KeyError:
            raise SystemError("Invalid label '%s'" % label)

        try:
            ips = interface['ips']
        except KeyError:
            raise SystemError("No IPs found for interface")

        ip6s = interface.get('ip6s', [])

        try:
            mac = interface['mac']
        except KeyError:
            raise SystemError("No mac address found for interface")

        try:
            routes = interface['routes']
        except KeyError:
            routes = []

        if label == "public":
            gateway4 = interface.get('gateway')
            gateway6 = interface.get('gateway6')
            if not gateway4 and not gateway6:
                raise SystemError("No gateway found for public interface")
            if gateway4 and not len(defaultrouter):
                defaultrouter = gateway4
            if gateway6 and not len(ipv6_defaultrouter):
                ipv6_defaultrouter = gateway6
            if len(ip6s):
                if len(ipv6_interfaces):
                    ipv6_interfaces += ','
                ipv6_interfaces += ifname_prefix

        ifname_suffix_num = 0

        for i in xrange(max(len(ips), len(ip6s))):
            if ifname_suffix_num:
                ifname = "%s_alias%d" % (ifname_prefix, ifname_suffix_num - 1)
            else:
                ifname = ifname_prefix

            if i < len(ips):
                ip_info = ips[i]
            else:
                ip_info = None

            if i < len(ip6s):
                ip6_info = ip6s[i]
            else:
                ip6_info = None

            if not ip_info and not ip6_info:
                continue

            if ip_info and ip_info.get('enabled', '0') != '0':
                try:
                    ip = ip_info['ip']
                    netmask = ip_info['netmask']
                except KeyError:
                    raise SystemError(
                            "Missing IP or netmask in interface's IP list")

                if ifname_suffix_num:
                    # XXX -- Known bug here.  If we're adding an alias
                    # that is on the same network as another address already
                    # configured, the netmask here should be 255.255.255.255
                    print >> outfile, 'ifconfig_%s="%s netmask %s"' % \
                            (ifname, ip, netmask)
                else:
                    print >> outfile, 'ifconfig_%s="%s netmask %s up"' % \
                            (ifname, ip, netmask)

            if ip6_info and ip6_info.get('enabled', '0') != '0':
                try:
                    ip = ip6_info['address']
                    netmask = ip6_info['netmask']
                except KeyError:
                    raise SystemError(
                            "Missing IP or netmask in interface's IPv6 list")

                print >> outfile, 'ipv6_ifconfig_%s="%s/%s"' % \
                        (ifname, ip, netmask)

                gateway = ip6_info.get('gateway', gateway6)

            ifname_suffix_num += 1

        for x in xrange(len(routes)):
            route = routes[x]
            network = route['route']
            netmask = route['netmask']
            gateway = route['gateway']

            if ':' in network:
                # ipv6
                fmt = '-net %s/%s %s'
            else:
                fmt = '-net %s -netmask %s %s'

            static_route_entries.append(fmt % (network, netmask, gateway))

    if len(static_route_entries):
        names = []
        for x in xrange(len(static_route_entries)):
            name = 'lan%d' % x
            names.append(name)
            print >> outfile, 'route_lan%d="%s"' % \
                    (x, static_route_entries[x])
        print >> outfile, 'static_routes="%s"' % ','.join(names)
    if len(ipv6_interfaces):
        print >> outfile, 'ipv6_enable="YES"'
        print >> outfile, 'ipv6_network_interfaces="%s"' % ipv6_interfaces
    if len(defaultrouter):
        print >> outfile, 'defaultrouter="%s"' % defaultrouter
    if len(ipv6_defaultrouter):
        print >> outfile, 'ipv6_defaultrouter="%s"' % ipv6_defaultrouter

    outfile.seek(0)
    return outfile.read()


def _get_file_data(interfaces, hostname):
    """
    Return the data for a new rc.conf file
    """

    return _create_rcconf_file(open(RCCONF_FILE), interfaces, hostname)
