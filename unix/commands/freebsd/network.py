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

INTERFACE_LABELS = {"public": "xn0",
                    "private": "xn1"}


def configure_network(network_config, *args, **kwargs):

    update_files = {}

    # Generate new interface files
    interfaces = network_config.get('interfaces', [])

    # Generate new hostname file
    hostname = network_config.get('hostname')

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


