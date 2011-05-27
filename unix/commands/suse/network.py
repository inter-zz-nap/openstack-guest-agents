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
suse network helper module
"""

import os
import time
import glob
import subprocess
import logging
from cStringIO import StringIO

import commands.network

HOSTNAME_FILE = "/etc/HOSTNAME"
DNS_CONFIG_FILE = "/etc/sysconfig/network/config"
NETCONFIG_DIR = "/etc/sysconfig/network"
INTERFACE_FILE = "ifcfg-%s"
ROUTE_FILE = "ifroute-%s"

INTERFACE_LABELS = {"public": "eth0",
                    "private": "eth1"}


def configure_network(network_config, *args, **kwargs):

    # Generate new interface files
    interfaces = network_config.get('interfaces', [])

    update_files, remove_files = process_interface_files(interfaces)

    # Update nameservers
    if os.path.exists(DNS_CONFIG_FILE):
        infile = open(DNS_CONFIG_FILE)
    else:
        infile = StringIO()

    data = get_nameservers_file(infile, interfaces)
    update_files[DNS_CONFIG_FILE] = data

    # Generate new hostname file
    hostname = network_config.get('hostname')

    data = get_hostname_file(hostname)
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


def get_hostname_file(hostname):
    """
    Update hostname on system
    """
    return hostname + '\n'


def get_nameservers_file(infile, interfaces):
    outfile = StringIO()

    dns = []
    for interface in interfaces:
        if interface['label'] != 'public':
            continue

        dns = interface.get('dns', [])

    if not dns:
        return outfile

    found = False
    for line in infile:
        line = line.strip()
        if '=' not in line:
            print >> outfile, line
            continue

        k, v = line.split('=', 1)
        k = k.strip()
        if k == 'NETCONFIG_DNS_STATIC_SERVERS':
            print >> outfile, \
                    'NETCONFIG_DNS_STATIC_SERVERS="%s"' % ' '.join(dns)
            found = True
        else:
            print >> outfile, line

    if not found:
        print >> outfile, 'NETCONFIG_DNS_STATIC_SERVERS="%s"' % ' '.join(dns)

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
        ifname = INTERFACE_LABELS[label]
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
    else:
        gateway4 = gateway6 = None

    ifnum = None

    iface_data = "# Automatically generated, do not edit\n"
    iface_data += "BOOTPROTO='static'\n"

    for ip_info in ip4s:
        enabled = ip_info.get('enabled', '0')
        if enabled != '1':
            continue

        try:
            ip = ip_info['ip']
            netmask = ip_info['netmask']
        except KeyError:
            raise SystemError(
                    "Missing IP or netmask in interface's IP list")

        if ifnum is None:
            iface_data += "IPADDR='%s'\n" % ip
            iface_data += "NETMASK='%s'\n" % netmask
            ifnum = 0
        else:
            iface_data += "IPADDR_%s='%s'\n" % (ifnum, ip)
            iface_data += "NETMASK_%s='%s'\n" % (ifnum, netmask)
            iface_data += "LABEL_%s='%s'\n" % (ifnum, ifnum)
            ifnum += 1

    for ip_info in ip6s:
        enabled = ip_info.get('enabled', '0')
        if enabled != '1':
            continue

        ip = ip_info.get('address', ip_info.get('ip'))
        if not ip:
            raise SystemError(
                    "Missing IP in interface's IP list")
        netmask = ip_info.get('netmask')
        if not netmask:
            raise SystemError(
                    "Missing netmask in interface's IP list")

        gateway6 = ip_info.get('gateway', gateway6)

        if ifnum is None:
            iface_data += "IPADDR='%s'\n" % ip
            iface_data += "PREFIXLEN='%s'\n" % netmask
            ifnum = 0
        else:
            iface_data += "IPADDR_%s='%s'\n" % (ifnum, ip)
            iface_data += "PREFIXLEN_%s='%s'\n" % (ifnum, netmask)
            iface_data += "LABEL_%s='%s'\n" % (ifnum, ifnum)
            ifnum += 1

    iface_data += "STARTMODE='auto'\n"
    iface_data += "USERCONTROL='no'\n"

    route_data = ''
    for route in interface.get('routes', []):
        network = route['route']
        netmask = route['netmask']
        gateway = route['gateway']

        route_data += '%s %s %s %s\n' % (network, gateway, netmask, ifname)

    if gateway4:
        route_data += 'default %s - -\n' % gateway4

    if gateway6:
        route_data += 'default %s - -\n' % gateway6

    return (ifname, iface_data, route_data)


def get_interface_files(interfaces):
    results = {}

    for interface in interfaces:
        ifname, iface_data, route_data = _get_file_data(interface)

        results[INTERFACE_FILE % ifname] = iface_data

        if route_data:
            results[ROUTE_FILE % ifname] = route_data

    return results


def process_interface_files(interfaces):
    """
    Write out a new files for interfaces
    """

    # Enumerate all of the existing ifcfg-* files
    remove_files = set()
    for filepath in glob.glob(NETCONFIG_DIR + "/ifcfg-*"):
        if '.' not in filepath:
            remove_files.add(filepath)
    for filepath in glob.glob(NETCONFIG_DIR + "/route-*"):
        if '.' not in filepath:
            remove_files.add(filepath)

    route_file = os.path.join(NETCONFIG_DIR, 'routes')
    if os.path.exists(route_file):
        remove_files.add(route_file)

    # We never write config for lo interface, but it should stay
    lo_file = os.path.join(NETCONFIG_DIR, INTERFACE_FILE % 'lo')
    if lo_file in remove_files:
        remove_files.remove(lo_file)

    update_files = {}
    for filename, data in get_interface_files(interfaces).iteritems():
        filepath = os.path.join(NETCONFIG_DIR, filename)

        update_files[filepath] = data

        if filepath in remove_files:
            remove_files.remove(filepath)

    return update_files, remove_files
