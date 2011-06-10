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

import logging
import os
import subprocess
import time
from cStringIO import StringIO

import commands.network

HOSTNAME_FILE = "/etc/hostname"
RESOLV_FILE = "/etc/resolv.conf"
INTERFACE_FILE = "/etc/network/interfaces"

INTERFACE_HEADER = \
"""
# Used by ifup(8) and ifdown(8). See the interfaces(5) manpage or
# /usr/share/doc/ifupdown/examples for more information.
# The loopback network interface
auto lo
iface lo inet loopback
""".lstrip('\n')

INTERFACE_LABELS = {"public": "eth0",
                    "private": "eth1"}


def configure_network(network_config):

    # Generate new interface files
    interfaces = network_config.get('interfaces', [])

    data = _get_file_data(interfaces)
    update_files = {INTERFACE_FILE: data}

    # Generate new hostname file
    hostname = network_config.get('hostname')

    data = get_hostname_file(hostname)
    update_files[HOSTNAME_FILE] = data

    # Generate new /etc/resolv.conf file
    # We do write dns-nameservers into the interfaces file, but that
    # only updates /etc/resolv.conf if the 'resolvconf' package is
    # installed.  Let's go ahead and modify /etc/resolv.conf.  It's just
    # possible that it could get re-written twice.. oh well.
    data = _get_resolv_conf(interfaces)
    update_files[RESOLV_FILE] = data

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
    p.communicate()
    status = p.returncode

    # Bring back up what we can
    _run_on_interfaces("/sbin/ifup")

    if files_update_error:
        raise files_update_error

    if status != 0:
        return (500, "Couldn't restart network: %d" % status)

    return (0, "")


def get_hostname_file(hostname):
    return hostname + '\n'


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


def _get_current_interfaces():
    """Get the current list of interfaces ignoring lo"""

    if not os.path.exists(INTERFACE_FILE):
        return []

    interfaces = []
    with open(INTERFACE_FILE, 'r') as f:
        for line in f.readlines():
            line = line.strip().lstrip()
            if line.startswith('iface') or \
                    line.startswith('auto') or \
                    line.startswith('allow-hotplug'):
                interface = line.split()[1]
                if not interface.startswith('lo'):
                    interfaces.append(interface)
    return set(interfaces)


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
        p.communicate()
        status = p.returncode
        if status != 0:
            logging.debug('ignoring failure of "%s %s": %d' % (
                cmd, i, status))


def _get_file_data(interfaces):
    """
    Return interfaces file data in 1 long string
    """

    file_data = INTERFACE_HEADER

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

            try:
                dns = interface['dns']
            except KeyError:
                raise SystemError("No DNS found for public interface")
        else:
            gateway4 = gateway6 = None

        ifname_suffix_num = 0

        for i in xrange(max(len(ips), len(ip6s))):
            if ifname_suffix_num:
                ifname = "%s:%d" % (ifname_prefix, ifname_suffix_num)
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

            file_data += "\n"
            file_data += "auto %s\n" % ifname

            if ip_info and ip_info.get('enabled', '0') != '0':
                try:
                    ip = ip_info['ip']
                    netmask = ip_info['netmask']
                except KeyError:
                    raise SystemError(
                            "Missing IP or netmask in interface's IP list")

                file_data += "iface %s inet static\n" % ifname
                file_data += "    address %s\n" % ip
                file_data += "    netmask %s\n" % netmask
                if gateway4:
                    file_data += "    gateway %s\n" % gateway4
                    gateway4 = None
                if dns:
                    file_data += "    dns-nameservers %s\n" % ' '.join(dns)
                    dns = None

            if ip6_info and ip6_info.get('enabled', '0') != '0':
                ip = ip6_info.get('address', ip6_info.get('ip'))
                if not ip:
                    raise SystemError(
                            "Missing IP in interface's IPv6 list")
                netmask = ip6_info.get('netmask')
                if not netmask:
                    raise SystemError(
                            "Missing netmask in interface's IPv6 list")

                gateway6 = ip6_info.get('gateway', gateway6)

                file_data += "iface %s inet6 static\n" % ifname
                file_data += "    address %s\n" % ip
                file_data += "    netmask %s\n" % netmask
                if gateway6:
                    file_data += "    gateway %s\n" % gateway6
                    gateway6 = None
                if dns:
                    file_data += "    dns-nameservers %s\n" % ' '.join(dns)
                    dns = None

            ifname_suffix_num += 1

        for route in routes:
            network = route['route']
            netmask = route['netmask']
            gateway = route['gateway']

            file_data += "up route add -net %s netmask %s gw %s\n" % (
                    network, netmask, gateway)
            file_data += "down route del -net %s netmask %s gw %s\n" % (
                    network, netmask, gateway)

    return file_data


def get_interface_files(interfaces):
    return {'interfaces': _get_file_data(interfaces)}
