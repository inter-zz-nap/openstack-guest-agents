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

# SuSE network configuration uses:
# - 1 network configuration file per interface
# - 1 IP per interface
# - routes are per interface
# - gateways are per interface
# - DNS is global (/etc/sysconfig/network/config)

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


def configure_network(hostname, interfaces):

    # Generate new interface files
    update_files, remove_files = process_interface_files(interfaces)

    # Update nameservers
    if os.path.exists(DNS_CONFIG_FILE):
        infile = open(DNS_CONFIG_FILE)
    else:
        infile = StringIO()

    dns = commands.network.get_nameservers(interfaces)
    data = get_nameservers_file(infile, dns)
    update_files[DNS_CONFIG_FILE] = data

    # Generate new hostname file
    data = get_hostname_file(hostname)
    update_files[HOSTNAME_FILE] = data

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


def get_hostname_file(hostname):
    """
    Update hostname on system
    """
    return hostname + '\n'


def get_nameservers_file(infile, dns):
    outfile = StringIO()
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


def _get_file_data(ifname, interface):
    """
    Return data for (sub-)interfaces and routes
    """

    ip4s = interface['ip4s']
    ip6s = interface['ip6s']

    gateway4 = interface['gateway4']
    gateway6 = interface['gateway6']

    ifnum = None

    iface_data = "# Automatically generated, do not edit\n"
    iface_data += "BOOTPROTO='static'\n"

    for ip in ip4s:
        if ifnum is None:
            iface_data += "IPADDR='%s'\n" % ip['address']
            iface_data += "NETMASK='%s'\n" % ip['netmask']
            ifnum = 0
        else:
            iface_data += "IPADDR_%s='%s'\n" % (ifnum, ip['address'])
            iface_data += "NETMASK_%s='%s'\n" % (ifnum, ip['netmask'])
            iface_data += "LABEL_%s='%s'\n" % (ifnum, ifnum)
            ifnum += 1

    for ip in ip6s:
        if ifnum is None:
            iface_data += "IPADDR='%s'\n" % ip['address']
            iface_data += "PREFIXLEN='%s'\n" % ip['prefixlen']
            ifnum = 0
        else:
            iface_data += "IPADDR_%s='%s'\n" % (ifnum, ip)
            iface_data += "PREFIXLEN_%s='%s'\n" % (ifnum, netmask)
            iface_data += "LABEL_%s='%s'\n" % (ifnum, ifnum)
            ifnum += 1

    iface_data += "STARTMODE='auto'\n"
    iface_data += "USERCONTROL='no'\n"

    route_data = ''
    for route in interface['routes']:
        network = route['network']
        netmask = route['netmask']
        gateway = route['gateway']

        route_data += '%s %s %s %s\n' % (network, gateway, netmask, ifname)

    if gateway4:
        route_data += 'default %s - -\n' % gateway4

    if gateway6:
        route_data += 'default %s - -\n' % gateway6

    return (iface_data, route_data)


def get_interface_files(interfaces):
    results = {}

    for ifname, interface in interfaces.iteritems():
        iface_data, route_data = _get_file_data(ifname, interface)

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
