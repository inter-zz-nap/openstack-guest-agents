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
debian/ubuntu network helper module
"""

# Debian/Ubuntu network configuration uses:
# - 1 network configuration file (/etc/network/interfaces)
# - 1 IP per interface
# - routes are per interface
# - gateways are per interface
# - DNS is per interface (but see comments below about /etc/resolv.conf)

import logging
import os
import subprocess
import time
from cStringIO import StringIO

import commands.network

HOSTNAME_FILE = "/etc/hostname"
INTERFACE_FILE = "/etc/network/interfaces"

INTERFACE_HEADER = \
"""
# Used by ifup(8) and ifdown(8). See the interfaces(5) manpage or
# /usr/share/doc/ifupdown/examples for more information.
# The loopback network interface
auto lo
iface lo inet loopback
""".lstrip('\n')


def configure_network(hostname, interfaces):
    # Generate new interface files
    data = _get_file_data(interfaces)
    update_files = {INTERFACE_FILE: data}

    # Generate new hostname file
    data = get_hostname_file(hostname)
    update_files[HOSTNAME_FILE] = data

    # Generate new /etc/resolv.conf file
    # We do write dns-nameservers into the interfaces file, but that
    # only updates /etc/resolv.conf if the 'resolvconf' package is
    # installed.  Let's go ahead and modify /etc/resolv.conf.  It's just
    # possible that it could get re-written twice.. oh well.
    filepath, data = commands.network.get_resolv_conf(interfaces)
    if data:
        update_files[filepath] = data

    # Generate new /etc/hosts file
    filepath, data = commands.network.get_etc_hosts(interfaces, hostname)
    update_files[filepath] = data

    pipe = subprocess.PIPE

    # Set hostname
    try:
        commands.network.sethostname(hostname)
    except Exception, e:
        logging.error("Couldn't sethostname(): %s" % str(e))
        return (500, "Couldn't set hostname: %s" % str(e))

    #
    # So, debian is kinda dumb in how it manages its interfaces.
    # A 'networking restart' doesn't actually down all interfaces that
    # might have been removed from the interfaces file.  So, we first
    # need to 'ifdown' everything we find.
    #
    # Now it's possible we'll fail to update files.. and if we do,
    # we need to try to bring the networking back up, anyway.  So,
    # no matter what, after we run 'ifdown' on everything, we need to
    # restart networking.
    #
    # Also: restart networking doesn't always seem to bring all
    # interfaces up, either!  Argh. :)  So, we also need to run 'ifup'
    # on everything.
    #
    # Now, ifdown and ifup can fail when it shouldn't be dealing with
    # a certain interface.. so we have to ignore all errors from them.
    #

    _run_on_interfaces("/sbin/ifdown")

    files_update_error = None
    # Write out new files
    try:
        commands.network.update_files(update_files)
    except Exception, e:
        files_update_error = e

    # Restart network
    logging.debug('executing /etc/init.d/networking restart')
    p = subprocess.Popen(["/etc/init.d/networking", "restart"],
            stdin=pipe, stdout=pipe, stderr=pipe, env={})
    logging.debug('waiting on pid %d' % p.pid)
    p.wait()
    status = p.returncode
    logging.debug('"/etc/init.d/networking restart" exited with code %d' %
            status)

    # Bring back up what we can
    _run_on_interfaces("/sbin/ifup")

    if files_update_error:
        raise files_update_error

    if status != 0:
        return (500, "Couldn't restart network: %d" % status)

    return (0, "")


def get_hostname_file(hostname):
    return hostname + '\n'


def _get_current_interfaces():
    """Get the current list of interfaces ignoring lo"""

    if not os.path.exists(INTERFACE_FILE):
        return set()

    interfaces = set()
    with open(INTERFACE_FILE, 'r') as f:
        for line in f.readlines():
            line = line.strip().lstrip()
            if line.startswith('iface') or \
                    line.startswith('auto') or \
                    line.startswith('allow-hotplug'):
                interface = line.split()[1]
                if not interface.startswith('lo'):
                    interfaces.add(interface)
    return interfaces


def _run_on_interfaces(cmd):
    """For all interfaces found, run a command with the interface as an
    argument
    """

    interfaces = _get_current_interfaces()
    pipe = subprocess.PIPE
    for i in interfaces:
        logging.debug('executing "%s %s"' % (cmd, i))
        p = subprocess.Popen([cmd, i],
            stdin=pipe, stdout=pipe, stderr=pipe, env={})
        logging.debug('waiting on pid %d' % p.pid)
        p.wait()
        status = p.returncode
        logging.debug('"%s %s" exited with code %d' % (
                cmd, i, status))


def _get_file_data(interfaces):
    """
    Return interfaces file data in 1 long string
    """

    file_data = INTERFACE_HEADER

    ifnames = interfaces.keys()
    ifnames.sort()

    for ifname_prefix in ifnames:
        interface = interfaces[ifname_prefix]

        ip4s = interface['ip4s']
        ip6s = interface['ip6s']

        gateway4 = interface['gateway4']
        gateway6 = interface['gateway6']

        dns = interface['dns']

        ifname_suffix_num = 0

        for i in xrange(max(len(ip4s), len(ip6s))):
            if ifname_suffix_num:
                ifname = "%s:%d" % (ifname_prefix, ifname_suffix_num)
            else:
                ifname = ifname_prefix

            file_data += "\n"
            file_data += "auto %s\n" % ifname

            if i < len(ip4s):
                ip = ip4s[i]

                file_data += "iface %s inet static\n" % ifname
                file_data += "    address %s\n" % ip['address']
                file_data += "    netmask %s\n" % ip['netmask']

                if gateway4:
                    file_data += "    gateway %s\n" % gateway4
                    gateway4 = None

            if i < len(ip6s):
                ip = ip6s[i]

                file_data += "iface %s inet6 static\n" % ifname
                file_data += "    address %s\n" % ip['address']
                file_data += "    netmask %s\n" % ip['prefixlen']

                if gateway6:
                    file_data += "    gateway %s\n" % gateway6
                    gateway6 = None

            if dns:
                file_data += "    dns-nameservers %s\n" % ' '.join(dns)
                dns = None

            ifname_suffix_num += 1

        for route in interface['routes']:
            file_data += "up route add -net %(network)s " \
                         "netmask %(netmask)s gw %(gateway)s\n" % route
            file_data += "down route del -net %(network)s " \
                         "netmask %(netmask)s gw %(gateway)s\n" % route

    return file_data


def get_interface_files(interfaces):
    return {'interfaces': _get_file_data(interfaces)}
