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
gentoo network helper module
"""

# Gentoo has two different kinds of network configuration. More recently,
# there's 'openrc' and previously (for lack of a better term) 'legacy'.
# They are fairly similar, the differences being more implementation
# defined (bash vs sh, etc).
#
# They both use:
# - 1 shell-script-style network configuration (/etc/conf.d/net)
# - multiple IPs per interface
# - routes are per interface
# - gateways are per interface
# - DNS is configured via resolv.conf

import os
import re
import time
import subprocess
import logging
from cStringIO import StringIO

import commands.network

HOSTNAME_FILE = "/etc/conf.d/hostname"
NETWORK_FILE = "/etc/conf.d/net"


def configure_network(hostname, interfaces):
    # Figure out if this system is running OpenRC
    if os.path.islink('/sbin/runscript'):
        data, ifaces = _get_file_data_openrc(interfaces)
    else:
        data, ifaces = _get_file_data_legacy(interfaces)

    update_files = {NETWORK_FILE: data}

    # Generate new /etc/resolv.conf file
    filepath, data = commands.network.get_resolv_conf(interfaces)
    if data:
        update_files[filepath] = data

    # Generate new hostname file
    data = get_hostname_file(hostname)
    update_files[HOSTNAME_FILE] = data

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
    for ifname in ifaces:
        scriptpath = '/etc/init.d/net.%s' % ifname

        if not os.path.exists(scriptpath):
            # Gentoo won't create these symlinks automatically
            os.symlink('net.lo', scriptpath)

        logging.debug('executing %s restart' % scriptpath)
        p = subprocess.Popen([scriptpath, 'restart'],
                stdin=pipe, stdout=pipe, stderr=pipe, env={})
        logging.debug('waiting on pid %d' % p.pid)
        status = os.waitpid(p.pid, 0)[1]
        logging.debug('status = %d' % status)

        if status != 0:
            return (500, "Couldn't restart network %s: %d" % (ifname, status))

    return (0, "")


def get_hostname_file(hostname):
    """
    Update hostname on system
    """
    return '# Automatically generated, do not edit\nHOSTNAME="%s"\n' % hostname


def _get_file_data_legacy(interfaces):
    """
    Return data for (sub-)interfaces and routes
    """

    ifaces = set()

    network_data = '# Automatically generated, do not edit\n'
    network_data += 'modules=( "ifconfig" )\n\n'

    ifnames = interfaces.keys()
    ifnames.sort()

    for ifname in ifnames:
        interface = interfaces[ifname]

        ip4s = interface['ip4s']
        ip6s = interface['ip6s']

        gateway4 = interface['gateway4']
        gateway6 = interface['gateway6']

        network_data += 'config_%s=(\n' % ifname

        for ip in ip4s:
            network_data += '    "%s netmask %s"\n' % \
                    (ip['address'], ip['netmask'])

        for ip in ip6s:
            network_data += '    "%s/%s"\n' % \
                    (ip['address'], ip['prefixlen'])

        network_data += ')\n'

        routes = []
        for route in interface['routes']:
            routes.append('%(network)s netmask %(netmask)s via %(gateway)s' %
                          route)

        if gateway4:
            routes.append('default via %s' % gateway4)
        if gateway6:
            routes.append('default via %s' % gateway6)

        if routes:
            network_data += 'routes_%s=(\n' % ifname
            for config in routes:
                network_data += '    "%s"\n' % config
            network_data += ')\n'

        ifaces.add(ifname)

    return network_data, ifaces


def _get_file_data_openrc(interfaces):
    """
    Return data for (sub-)interfaces and routes
    """

    ifaces = set()

    network_data = '# Automatically generated, do not edit\n'
    network_data += 'modules="ifconfig"\n\n'

    ifnames = interfaces.keys()
    ifnames.sort()

    for ifname in ifnames:
        interface = interfaces[ifname]

        ip4s = interface['ip4s']
        ip6s = interface['ip6s']

        gateway4 = interface['gateway4']
        gateway6 = interface['gateway6']

        iface_data = []

        for ip in ip4s:
            iface_data.append('%s netmask %s' %
                              (ip['address'], ip['netmask']))

        for ip in ip6s:
            iface_data.append('%s/%s' % (ip['address'], ip['prefixlen']))

        network_data += 'config_%s="%s"\n' % (ifname, '\n'.join(iface_data))

        route_data = []
        for route in interface['routes']:
            route_data.append('%(network)s netmask %(netmask)s '
                              'via %(gateway)s' % route)

        if gateway4:
            route_data.append('default via %s' % gateway4)
        if gateway6:
            route_data.append('default via %s' % gateway6)

        if route_data:
            network_data += 'routes_%s="%s"\n' % (ifname, '\n'.join(route_data))

        ifaces.add(ifname)

    return network_data, ifaces


def get_interface_files(interfaces, version):
    if version == 'openrc':
        data, ifaces = _get_file_data_openrc(interfaces)
    else:
        data, ifaces = _get_file_data_legacy(interfaces)

    return {'net': data}
