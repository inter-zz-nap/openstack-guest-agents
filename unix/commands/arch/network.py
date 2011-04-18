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
arch linux network helper module
"""

import os
import re
import time
import subprocess
import logging
from cStringIO import StringIO

import commands.network

CONF_FILE = "/etc/rc.conf"

INTERFACE_LABELS = {"public": "eth0",
                    "private": "eth1"}


def configure_network(network_config, *args, **kwargs):

    # Update config file with new interface configuration
    interfaces = network_config.get('interfaces', [])

    if os.path.exists(CONF_FILE):
        infile = open(CONF_FILE)
    else:
        infile = StringIO()
    data = _get_interface_file(infile, interfaces)

    # Update config file with new hostname
    hostname = network_config.get('hostname')

    data = get_hostname_file(StringIO(data), hostname)
    update_files = {CONF_FILE: data}

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
    logging.debug('executing /etc/rc.d/network restart')
    p = subprocess.Popen(["/etc/rc.d/network", "restart"])
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
                print >> outfile, 'HOSTNAME="%s"' % hostname
                found = True
            else:
                print >> outfile, line
        else:
            print >> outfile, line

    if not found:
        print >> outfile, 'HOSTNAME="%s"' % hostname

    outfile.seek(0)
    return outfile.read()


def _parse_variable(line):
    k, v = line.split('=')
    v = v.strip()
    if v[0] == '(' and v[-1] == ')':
        v = v[1:-1]

    return [name.lstrip('!') for name in re.split('\s+', v.strip())]


def _get_interface_file(infile, interfaces):
    """
    Return data for (sub-)interfaces and routes
    """

    # Updating this file happens in two phases since it's non-trivial to
    # update. The INTERFACES and ROUTES variables the key lines, but they
    # will in turn reference other variables, which may be before or after.
    # As a result, we need to load the entire file, find the main variables
    # and then remove the reference variables. When that is done, we add
    # the lines for the new config.

    # First generate new config
    ifaces = []
    routes = []

    for interface in interfaces:
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
        else:
            gateway4 = gateway6 = None

        ifname_suffix_num = 0

        for i in xrange(max(len(ip4s), len(ip6s))):
            if ifname_suffix_num:
                ifname = "%s:%d" % (ifname_prefix, ifname_suffix_num)
            else:
                ifname = ifname_prefix

            line = [ifname]
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

                    line.append('%s netmask %s' % (ip, netmask))

            if i < len(ip6s):
                ip_info = ip6s[i]

                enabled = ip_info.get('enabled', '0')
                if enabled != '0':
                    try:
                        ip = ip_info['address']
                        netmask = ip_info['netmask']
                    except KeyError:
                        raise SystemError(
                                "Missing IP or netmask in interface's IP list")

                    if not gateway6:
                        gateway6 = ip_info.get('gateway', gateway6)

                    line.append('add %s/%s' % (ip, netmask))

            ifname_suffix_num += 1

            ifaces.append((ifname.replace(':', '_'), ' '.join(line)))

        for i, route in enumerate(interface.get('routes', [])):
            network = route['route']
            netmask = route['netmask']
            gateway = route['gateway']

            line = "-net %s netmask %s gw %s" % (network, netmask, gateway)

            routes.append(('%s_route%d' % (ifname_prefix, i), line))

    if gateway4:
        routes.append(('gateway', 'default gw %s' % gateway4))
    if gateway6:
        routes.append(('gateway6', 'default gw %s' % gateway6))

    # Then load old file
    lines = []
    variables = {}
    for line in infile:
        line = line.strip()
        lines.append(line)

        # FIXME: This doesn't correctly parse shell scripts perfectly. It
        # assumes a fairly simple subset

        if '=' not in line:
            continue

        k, v = line.split('=', 1)
        k = k.strip()
        variables[k] = len(lines) - 1

    # Update INTERFACES
    lineno = variables.get('INTERFACES')
    if lineno is not None:
        # Remove old lines
        for name in _parse_variable(lines[lineno]):
            if name in variables:
                lines[variables[name]] = None
    else:
        lines.append('')
        lineno = len(lines) - 1

    config = []
    names = []
    for name, line in ifaces:
        config.append('%s="%s"' % (name, line))
        names.append(name)

    config.append('INTERFACES=(%s)' % ' '.join(names))
    lines[lineno] = '\n'.join(config)

    # Update ROUTES
    lineno = variables.get('ROUTES')
    if lineno is not None:
        # Remove old lines
        for name in _parse_variable(lines[lineno]):
            if name in variables:
                lines[variables[name]] = None
    else:
        lines.append('')
        lineno = len(lines) - 1

    config = []
    names = []
    for name, line in routes:
        config.append('%s="%s"' % (name, line))
        names.append(name)

    config.append('ROUTES=(%s)' % ' '.join(names))
    lines[lineno] = '\n'.join(config)

    # Filter out any removed lines
    lines = filter(lambda l: l is not None, lines)

    # Patch into new file
    outfile = StringIO()
    for line in lines:
        print >> outfile, line

    outfile.seek(0)
    return outfile.read()


def get_interface_files(infile, interfaces):
    return {'rc.conf': _get_interface_file(infile, interfaces)}
