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
redhat/centos network helper module
"""

# Red Hat network configuration uses:
# - 1 network configuration file per interface
# - 1 IP per interface
# - routes are per interface
# - gateways are per interface
# - DNS is configured per interface

import os
import time
import glob
import subprocess
import logging
from cStringIO import StringIO

import commands.network

NETWORK_FILE = "/etc/sysconfig/network"
NETCONFIG_DIR = "/etc/sysconfig/network-scripts"
INTERFACE_FILE = "ifcfg-%s"
ROUTE_FILE = "route-%s"


def configure_network(hostname, interfaces):
    if os.path.exists(NETWORK_FILE):
        infile = open(NETWORK_FILE)
    else:
        infile = StringIO()

    update_files, remove_files = process_interface_files(infile, interfaces)

    # Generate new hostname file
    infile = StringIO(update_files.get(NETWORK_FILE, infile))

    data = get_hostname_file(infile, hostname)
    update_files[NETWORK_FILE] = data

    # Generate new /etc/hosts file
    filepath, data = commands.network.get_etc_hosts(interfaces, hostname)
    update_files[filepath] = data

    # Write out new files
    commands.network.update_files(update_files, remove_files)

    pipe = subprocess.PIPE

    # Set hostname
    try:
        commands.network.sethostname(hostname)
    except Exception, e:
        logging.error("Couldn't sethostname(): %s" % str(e))
        return (500, "Couldn't set hostname: %s" % str(e))

    # Restart network
    logging.debug('executing /etc/init.d/network restart')
    p = subprocess.Popen(["/etc/init.d/network", "restart"],
            stdin=pipe, stdout=pipe, stderr=pipe, env={})
    logging.debug('waiting on pid %d' % p.pid)
    status = os.waitpid(p.pid, 0)[1]
    logging.debug('status = %d' % status)

    if status != 0:
        return (500, "Couldn't restart network: %d" % status)

    return (0, "")


def _update_key_value(infile, key, value):
    """
    Update hostname on system
    """
    outfile = StringIO()

    found = False
    for line in infile:
        line = line.strip()
        if '=' in line:
            k, v = line.split('=', 1)
            k = k.strip()
            if k == key:
                print >> outfile, "%s=%s" % (key, value)
                found = True
            else:
                print >> outfile, line
        else:
            print >> outfile, line

    if not found:
        print >> outfile, "%s=%s" % (key, value)

    outfile.seek(0)
    return outfile.read()


def get_hostname_file(infile, hostname):
    """
    Update hostname on system
    """
    return _update_key_value(infile, 'HOSTNAME', hostname)


def _get_file_data(ifname_prefix, interface):
    """
    Return data for (sub-)interfaces and routes
    """

    ip4s = interface['ip4s']
    ip6s = interface['ip6s']

    gateway4 = interface['gateway4']
    gateway6 = interface['gateway6']

    dns = interface['dns']

    ifaces = []

    ifname_suffix_num = 0

    for i in xrange(max(len(ip4s), len(ip6s))):
        if ifname_suffix_num:
            ifname = "%s:%d" % (ifname_prefix, ifname_suffix_num)
        else:
            ifname = ifname_prefix

        iface_data = "# Automatically generated, do not edit\n"
        iface_data += "DEVICE=%s\n" % ifname
        iface_data += "BOOTPROTO=static\n"
        iface_data += "HWADDR=%s\n" % interface['mac']

        if i < len(ip4s):
            ip = ip4s[i]

            iface_data += "IPADDR=%s\n" % ip['address']
            iface_data += "NETMASK=%s\n" % ip['netmask']
            if gateway4:
                iface_data += "DEFROUTE=yes\n"
                iface_data += "GATEWAY=%s\n" % gateway4
                gateway4 = None

        if i < len(ip6s):
            ip = ip6s[i]

            iface_data += "IPV6INIT=yes\n"
            iface_data += "IPV6_AUTOCONF=no\n"
            iface_data += "IPV6ADDR=%s/%s\n" % \
                    (ip['address'], ip['prefixlen'])

            if gateway6:
                iface_data += "IPV6_DEFAULTGW=%s%%%s\n" % (gateway6, ifname)
                gateway6 = None

        if dns:
            for j, nameserver in enumerate(dns):
                iface_data += "DNS%d=%s\n" % (j + 1, nameserver)
            dns = None

        iface_data += "ONBOOT=yes\n"
        iface_data += "NM_CONTROLLED=no\n"
        ifname_suffix_num += 1

        ifaces.append((ifname, iface_data))

    route_data = ''
    for i, route in enumerate(interface['routes']):
        route_data += "ADDRESS%d=%s\n" % (i, route['network'])
        route_data += "NETMASK%d=%s\n" % (i, route['netmask'])
        route_data += "GATEWAY%d=%s\n" % (i, route['gateway'])

    return (ifaces, route_data)


def get_interface_files(interfaces):
    update_files = {}

    for ifname, interface in interfaces.iteritems():
        ifaces, route_data = _get_file_data(ifname, interface)

        for ifname, data in ifaces:
            update_files[INTERFACE_FILE % ifname] = data

        if route_data:
            update_files[ROUTE_FILE % ifname] = route_data

    return update_files


def process_interface_files(infile, interfaces):
    """
    Write out a new files for interfaces
    """

    # Enumerate all of the existing ifcfg-* files
    remove_files = set()
    for filepath in glob.glob(NETCONFIG_DIR + "/ifcfg-*"):
        if '.' not in filepath:
            remove_files.add(filepath)
    for filename in glob.glob(NETCONFIG_DIR + "/route-*"):
        if '.' not in filepath:
            remove_files.add(filepath)

    lo_file = os.path.join(NETCONFIG_DIR, INTERFACE_FILE % 'lo')
    if lo_file in remove_files:
        remove_files.remove(lo_file)

    update_files = {}

    ipv6 = False
    for ifname, interface in interfaces.iteritems():
        ifaces, route_data = _get_file_data(ifname, interface)
        if interface['ip6s']:
            ipv6 = True

        for ifname, data in ifaces:
            filepath = os.path.join(NETCONFIG_DIR, INTERFACE_FILE % ifname)
            update_files[filepath] = data
            if filepath in remove_files:
                remove_files.remove(filepath)

        if route_data:
            filepath = os.path.join(NETCONFIG_DIR, ROUTE_FILE % ifname)
            update_files[filepath] = route_data
            if filepath in remove_files:
                remove_files.remove(filepath)

    update_files[NETWORK_FILE] = _update_key_value(infile, 'NETWORKING_IPV6',
            ipv6 and 'yes' or 'no')

    return update_files, remove_files
