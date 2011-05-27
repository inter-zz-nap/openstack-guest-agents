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

import os
import time
import glob
import subprocess
import logging
from cStringIO import StringIO

import commands.network

HOSTNAME_FILE = "/etc/sysconfig/network"
NETCONFIG_DIR = "/etc/sysconfig/network-scripts"
INTERFACE_FILE = "ifcfg-%s"
ROUTE_FILE = "route-%s"

INTERFACE_LABELS = {"public": "eth0",
                    "private": "eth1"}


def configure_network(network_config, *args, **kwargs):

    # Generate new interface files
    interfaces = network_config.get('interfaces', [])

    update_files, remove_files = process_interface_files(interfaces)

    # Generate new hostname file
    hostname = network_config.get('hostname')

    if os.path.exists(HOSTNAME_FILE):
        infile = open(HOSTNAME_FILE)
    else:
        infile = StringIO()
    data = get_hostname_file(infile, hostname)
    update_files[HOSTNAME_FILE] = data

    # Generate new /etc/hosts file
    filepath, data = commands.network.get_etc_hosts(interfaces, hostname)
    update_files[filepath] = data

    # Write out new files
    commands.network.update_files(update_files, remove_files)

    pipe = subprocess.PIPE

    # Set hostname
    logging.debug('executing /bin/hostname %s' % hostname)
    p = subprocess.Popen(["/bin/hostname", hostname],
            stdin=pipe, stdout=pipe, stderr=pipe)
    logging.debug('waiting on pid %d' % p.pid)
    status = os.waitpid(p.pid, 0)[1]
    logging.debug('status = %d' % status)

    if status != 0:
        return (500, "Couldn't set hostname: %d" % status)

    # Restart network
    logging.debug('executing /etc/init.d/network restart')
    p = subprocess.Popen(["/etc/init.d/network", "restart"],
            stdin=pipe, stdout=pipe, stderr=pipe)
    logging.debug('waiting on pid %d' % p.pid)
    status = os.waitpid(p.pid, 0)[1]
    logging.debug('status = %d' % status)

    if status != 0:
        return (500, "Couldn't restart network: %d" % status)

    return (0, "")


def get_hostname_file(infile, hostname):
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
            if k == "HOSTNAME":
                print >> outfile, "HOSTNAME=%s" % hostname
                found = True
            else:
                print >> outfile, line
        else:
            print >> outfile, line

    if not found:
        print >> outfile, "HOSTNAME=%s" % hostname

    outfile.seek(0)
    return outfile.read()


def _get_file_data(interface):
    """
    Return data for (sub-)interfaces and routes
    """

    try:
        label = interface['label']
    except KeyError:
        raise SystemError("No interface label found")

    try:
        ifname_prefix = INTERFACE_LABELS[label]
    except KeyError:
        raise SystemError("Invalid label '%s'" % label)

    ip4s = interface.get('ips', [])
    ip6s = interface.get('ip6s', [])

    if not ip4s and not ip6s:
        raise SystemError("No IPs found for interface")

    try:
        mac = interface['mac']
    except KeyError:
        raise SystemError("No mac address found for interface")

    if label == "public":
        gateway4 = interface.get('gateway')
        gateway6 = interface.get('gateway6')

        if not gateway4 and not gateway6:
            raise SystemError("No gateway found for public interface")

        try:
            dns = interface['dns']
        except KeyError:
            raise SystemError("No DNS found for public interface")

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
        iface_data += "HWADDR=%s\n" % mac

        if i < len(ip4s):
            ip_info = ip4s[i]

            enabled = ip_info.get('enabled', '0')
            if enabled != '0':
                try:
                    ip = ip_info['ip']
                    netmask = ip_info['netmask']
                except KeyError:
                    raise SystemError(
                            "Missing IP or netmask in interface's IP list")

                iface_data += "IPADDR=%s\n" % ip
                iface_data += "NETMASK=%s\n" % netmask
                if label == "public" and gateway4:
                    iface_data += "DEFROUTE=yes\n"
                    iface_data += "GATEWAY=%s\n" % gateway4

        if i < len(ip6s):
            ip_info = ip6s[i]

            enabled = ip_info.get('enabled', '0')
            if enabled != '0':
                ip = ip_info.get('address', ip_info.get('ip'))
                if not ip:
                    raise SystemError(
                            "Missing IP in interface's IP list")
                netmask = ip_info.get('netmask')
                if not netmask:
                    raise SystemError(
                            "Missing netmask in interface's IP list")

                gateway = ip_info.get('gateway', gateway6)

                iface_data += "IPV6INIT=yes\n"
                iface_data += "IPV6_AUTOCONF=no\n"
                iface_data += "IPV6ADDR=%s/%s\n" % (ip, netmask)

                if gateway:
                    iface_data += "IPV6_DEFAULTGW=%s\n" % gateway

        if gateway4 or gateway6:
            for j, nameserver in enumerate(dns):
                iface_data += "DNS%d=%s\n" % (j + 1, nameserver)

        iface_data += "ONBOOT=yes\n"
        iface_data += "NM_CONTROLLED=no\n"
        ifname_suffix_num += 1

        ifaces.append((ifname, iface_data))

    route_data = ''
    for route in interface.get('routes', []):
        network = route['route']
        netmask = route['netmask']
        gateway = route['gateway']

        route_data += "-net %s netmask %s gw %s\n" % (
                network, netmask, gateway)

    return (ifname_prefix, ifaces, route_data)


def get_interface_files(interfaces):
    update_files = {}

    for interface in interfaces:
        ifname, ifaces, route_data = _get_file_data(interface)

        for ifname, data in ifaces:
            update_files[INTERFACE_FILE % ifname] = data

        if route_data:
            update_files[ROUTE_FILE % ifname] = route_data

    return update_files


def process_interface_files(interfaces):
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

    for interface in interfaces:
        ifname, ifaces, route_data = _get_file_data(interface)

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

    return update_files, remove_files
