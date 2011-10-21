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

# FreeBSD network configuration uses:
# - 1 shell-script-style global configuration file (/etc/rc.conf)
# - 1 IP per interface
# - routes are global
# - gateways are global
# - DNS is configured via resolv.conf 

import os
import re
import time
import subprocess
import logging
from cStringIO import StringIO

import commands.network

RCCONF_FILE = "/etc/rc.conf"


def configure_network(hostname, interfaces):
    update_files = {}

    # Generate new /etc/rc.conf
    data = _get_file_data(interfaces, hostname)
    update_files[RCCONF_FILE] = data

    # Generate new /etc/resolv.conf file
    filepath, data = commands.network.get_resolv_conf(interfaces)
    if data:
        update_files[filepath] = data

    # Generate new /etc/hosts file
    filepath, data = commands.network.get_etc_hosts(interfaces, hostname)
    update_files[filepath] = data

    # Write out new files
    commands.network.update_files(update_files)

    pipe = subprocess.PIPE

    # Set hostname
    try:
        commands.network.sethostname(hostname)
    except Exception, e:
        logging.error("Couldn't sethostname(): %s" % str(e))
        return (500, "Couldn't set hostname: %s" % str(e))

    # Restart network
    logging.debug('executing /etc/rc.d/netif restart')
    p = subprocess.Popen(["/etc/rc.d/netif", "restart"],
            stdin=pipe, stdout=pipe, stderr=pipe, env={})
    logging.debug('waiting on pid %d' % p.pid)
    status = os.waitpid(p.pid, 0)[1]
    logging.debug('status = %d' % status)

    if status != 0:
        return (500, "Couldn't restart IPv4 networking: %d" % status)

    # Restart network
    logging.debug('executing /etc/rc.d/network_ipv6 restart')
    p = subprocess.Popen(["/etc/rc.d/network_ipv6", "restart"],
            stdin=pipe, stdout=pipe, stderr=pipe, env={})
    logging.debug('waiting on pid %d' % p.pid)
    status = os.waitpid(p.pid, 0)[1]
    logging.debug('status = %d' % status)

    if status != 0:
        return (500, "Couldn't restart IPv6 networking: %d" % status)

    return (0, "")


def _create_rcconf_file(infile, interfaces, hostname):
    """
    Return new rc.conf, merging in 'infile'
    """

    ipv6_interfaces = []
    static_route_entries = []

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

    gateway4, gateway6 = commands.network.get_gateways(interfaces)

    ifnames = interfaces.keys()
    ifnames.sort()
    for ifname_prefix in ifnames:
        interface = interfaces[ifname_prefix]

        ip4s = interface['ip4s']
        ip6s = interface['ip6s']

        if ip6s:
            ipv6_interfaces.append(ifname_prefix)

        ifname_suffix_num = 0

        for ip4, ip6 in map(None, ip4s, ip6s):
            if ifname_suffix_num:
                ifname = "%s_alias%d" % (ifname_prefix, ifname_suffix_num - 1)
            else:
                ifname = ifname_prefix

            if ip4:
                if ifname_suffix_num:
                    # XXX -- Known bug here.  If we're adding an alias
                    # that is on the same network as another address already
                    # configured, the netmask here should be 255.255.255.255
                    print >> outfile, 'ifconfig_%s="%s netmask %s"' % \
                            (ifname, ip4['address'], ip4['netmask'])
                else:
                    print >> outfile, 'ifconfig_%s="%s netmask %s up"' % \
                            (ifname, ip4['address'], ip4['netmask'])

            if ip6:
                print >> outfile, 'ipv6_ifconfig_%s="%s/%s"' % \
                        (ifname, ip6['address'], ip6['prefixlen'])

            ifname_suffix_num += 1

        for route in interface['routes']:
            if ':' in route['network']:
                # ipv6
                fmt = '-net %(network)s/%(netmask)s %(gateway)s'
            else:
                fmt = '-net %(network)s -netmask %(netmask)s %(gateway)s'

            static_route_entries.append(fmt % route)

    if static_route_entries:
        names = []
        for i, line in enumerate(static_route_entries):
            name = 'lan%d' % i
            names.append(name)
            print >> outfile, 'route_%s="%s"' % (name, line)

        print >> outfile, 'static_routes="%s"' % ','.join(names)

    if ipv6_interfaces:
        print >> outfile, 'ipv6_enable="YES"'
        print >> outfile, 'ipv6_network_interfaces="%s"' % \
            ','.join(ipv6_interfaces)

    if gateway4:
        print >> outfile, 'defaultrouter="%s"' % gateway4

    if gateway6:
        print >> outfile, 'ipv6_defaultrouter="%s"' % gateway6

    outfile.seek(0)
    return outfile.read()


def _get_file_data(interfaces, hostname):
    """
    Return the data for a new rc.conf file
    """

    return _create_rcconf_file(open(RCCONF_FILE), interfaces, hostname)
