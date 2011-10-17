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
JSON misc commands plugin
"""

try:
    import anyjson
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json

    class anyjson(object):
        """Fake anyjson module as a class"""

        @staticmethod
        def serialize(buf):
            return json.dumps(buf)

        @staticmethod
        def deserialize(buf):
            return json.loads(buf)

from cStringIO import StringIO
import fcntl
import logging
import os
import platform
import pyxenstore
import re
import socket
import time
from ctypes import *

import agentlib
import commands
import debian.network
import redhat.network
import arch.network
import suse.network
import gentoo.network
import freebsd.network


XENSTORE_INTERFACE_PATH = "vm-data/networking"
XENSTORE_HOSTNAME_PATH = "vm-data/hostname"
DEFAULT_HOSTNAME = ''
HOSTS_FILE = '/etc/hosts'
RESOLV_CONF_FILE = '/etc/resolv.conf'

INTERFACE_LABELS = {"public": "eth0",
                    "private": "eth1"}

# FIXME: Use these interface names for FreeBSD
#INTERFACE_LABELS = {"public": "xn0",
#                    "private": "xn1"}

SIOCGIFCONF   = 0x8912
SIOCGIFFLAGS  = 0x8913
SIOCGIFHWADDR = 0x8927

IFF_LOOPBACK  = 0x8

IFNAMSIZ = 16


class sockaddr(Structure):
    _fields_ = [
        ('sa_len', c_uint8),
        ('sa_family', c_uint8),
        ('sa_data', c_uint8 * 14)
    ]


class ifmap(Structure):
    _fields_ = [
        ('mem_start', c_long),
        ('mem_end', c_long),
        ('base_addr', c_short),
        ('irq', c_char),
        ('dma', c_char),
        ('port', c_char),
    ]


class _ifreq(Union):
    _fields_ = [
        ('ifr_addr', sockaddr),
        ('ifr_dstaddr', sockaddr),
        ('ifr_broadaddr', sockaddr),
        ('ifr_netmask', sockaddr),
        ('ifr_hwaddr', sockaddr),
        ('ifr_flags', c_short), 
        ('ifr_ifindex', c_int),
        ('ifr_metric', c_int),
        ('ifr_mtu', c_int),  
        ('ifr_map', ifmap),
        ('ifr_slave', c_char * IFNAMSIZ),
        ('ifr_newname', c_char * IFNAMSIZ),
        ('ifr_data', c_char_p),  
    ]


class ifreq(Structure):
    _fields_ = [
        ('ifr_name', c_char * IFNAMSIZ),
        ('u', _ifreq),
    ]
    _anonymous_ = ('u',)


class _ifconf(Union):
    _fields_ = [
        ('ifc_buf', c_char_p),
        ('ifc_req', POINTER(ifreq)),
    ]


class ifconf(Structure):
    _fields_ = [
        ('ifc_len', c_int),
        ('u', _ifconf),
    ]
    _anonymous_ = ('u',)


def network_interfaces():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

    # Create array of ifreqs
    maxifs = 32
    ifrs = (ifreq * maxifs)()

    # Create ifconf and point to ifrs
    ifc = ifconf()
    ifc.ifc_len = len(buffer(ifrs))
    ifc.ifc_buf = cast(pointer(ifrs), c_char_p)

    fcntl.ioctl(sock, SIOCGIFCONF, ifc)

    numifrs = ifc.ifc_len / len(buffer(ifrs[0]))
    for ifr in ifrs[:numifrs]:
        if_name = ifr.ifr_name

        fcntl.ioctl(sock, SIOCGIFFLAGS, ifr)

        if ifr.ifr_flags & IFF_LOOPBACK:
            continue

        fcntl.ioctl(sock, SIOCGIFHWADDR, ifr)
        mac_addr = ':'.join(['%02x' % i for i in ifr.ifr_hwaddr.sa_data[:6]])
        yield (if_name, mac_addr)


class NetworkCommands(commands.CommandBase):

    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def detect_os():
        """
        Return the Linux Distribution or other OS name
        """

        translations = {"debian": debian,
                        "ubuntu": debian,
                        "redhat": redhat,
                        "centos": redhat,
                        "fedora": redhat,
                        "oracle": redhat,
                        "arch": arch,
                        "opensuse": suse,
                        "suse": suse,
                        "gentoo": gentoo,
                        "freebsd": freebsd}

        system = os.uname()[0]
        if system == "Linux":
            system = platform.linux_distribution(full_distribution_name=0)[0]

            # Arch Linux returns None for platform.linux_distribution()
            if not system and os.path.exists('/etc/arch-release'):
                system = 'arch'

        if not system:
            return None

        system = system.lower()
        global DEFAULT_HOSTNAME
        DEFAULT_HOSTNAME = system

        return translations.get(system)

    @commands.command_add('resetnetwork')
    def resetnetwork_cmd(self, data):

        os_mod = self.detect_os()
        if not os_mod:
            raise SystemError("Couldn't figure out my OS")

        xs_handle = pyxenstore.Handle()

        try:
            hostname = xs_handle.read(XENSTORE_HOSTNAME_PATH)
        except pyxenstore.NotFoundError:
            hostname = DEFAULT_HOSTNAME

        interfaces = []

        try:
            entries = xs_handle.entries(XENSTORE_INTERFACE_PATH)
        except pyxenstore.NotFoundError:
            entries = []

        for entry in entries:
            data = xs_handle.read(XENSTORE_INTERFACE_PATH + '/' + entry)
            interfaces.append(anyjson.deserialize(data))

        del xs_handle

        # Normalize interfaces data. It can come in a couple of different
        # (similar) formats, none of which are convenient.
        by_macaddr = dict([(m, n) for n, m in network_interfaces()])

        config = {}

        for interface in interfaces:
            ifconfig = {}

            mac = interface.get('mac')
            if not mac:
                raise RuntimeError('No MAC found in config')

            # by_macaddr is keyed using lower case hexadecimal
            mac = mac.lower()

            ifconfig['mac'] = mac

            # 'label' used to be the method to determine which interface
            # this configuration applies to, but 'mac' is safer to use.
            # 'label' is being phased out now.
            ifname = by_macaddr.get(mac)
            if not ifname:
                raise RuntimeError('Unknown interface MAC %s' %
                                   interface['mac'])

            # List of IPv4 and IPv6 addresses
            ip4s = interface.get('ips', [])
            ip6s = interface.get('ip6s', [])
            if not ip4s and not ip6s:
                raise RuntimeError('No IPs found for interface')

            # Filter out any IPs that aren't enabled
            ip4s = filter(lambda i: i.get('enabled', '0') != '0', ip4s)
            ip6s = filter(lambda i: i.get('enabled', '0') != '0', ip6s)

            # Validate and normalize IPv4 and IPv6 addresses
            for ip in ip4s:
                if 'ip' not in ip:
                    raise RuntimeError("Missing 'ip' key for IPv4 address")
                if 'netmask' not in ip:
                    raise RuntimeError("Missing 'netmask' key for IPv4 address")

                # Rename 'ip' to 'address' to be more specific
                ip['address'] = ip['ip']
                del ip['ip']

            for ip in ip6s:
                if 'ip' not in ip and 'address' not in ip:
                    raise RuntimeError("Missing 'ip' or 'address' key for IPv6 address")
                if 'netmask' not in ip:
                    raise RuntimeError("Missing 'netmask' key for IPv6 address")

                # FIXME: Should we fail if both 'ip' and 'address' are
                # specified but differ?

                # Rename 'ip' to 'address' to be more specific
                if 'address' not in ip:
                    ip['address'] = ip['ip']
                    del ip['ip']

                # Rename 'netmask' to 'prefixlen' to be more accurate
                ip['prefixlen'] = ip['netmask']
                del ip['netmask']

            ifconfig['ip4s'] = ip4s
            ifconfig['ip6s'] = ip6s

            # Gateway (especially IPv6) can be interface specific
            gateway4 = interface.get('gateway')
            gateway6 = interface.get('gateway6')

            ifconfig['gateway4'] = gateway4
            ifconfig['gateway6'] = gateway6

            # Routes are optional
            routes = interface.get('routes', [])

            # Validate and normalize routes
            for route in routes:
                if 'route' not in route:
                    raise RuntimeError("Missing 'route' key for route")
                if 'netmask' not in route:
                    raise RuntimeError("Missing 'netmask' key for route")
                if 'gateway' not in route:
                    raise RuntimeError("Missing 'gateway' key for route")

                # Rename 'route' to 'network' to be more specific
                route['network'] = route['route']
                del route['route']

            ifconfig['routes'] = routes

            ifconfig['dns'] = interface.get('dns', [])

            config[ifname] = ifconfig

        # TODO: Should we fail if there isn't at least one gateway specified?
        #if not gateway4 and not gateway6:
        #    raise RuntimeError('No gateway found for public interface')

        return os_mod.network.configure_network(hostname, config)


def _get_etc_hosts(infile, interfaces, hostname):
    ips = set()
    for interface in interfaces.itervalues():
        ip4s = interface['ip4s']
        if ip4s:
            ips.add(ip4s[0]['address'])

        ip6s = interface['ip6s']
        if ip6s:
            ips.add(ip6s[0]['address'])

    outfile = StringIO()

    for line in infile:
        line = line.strip()

        if '#' in line:
            config, comment = line.split('#', 1)
            config = config.strip()
            comment = '\t#' + comment
        else:
            config, comment = line, ''

        parts = re.split('\s+', config)
        if parts:
            if parts[0] in ips:
                confip = parts.pop(0)
                if len(parts) == 1 and parts[0] != hostname:
                    # Single hostname that differs, we replace that one
                    print >> outfile, '# %s\t# Removed by nova-agent' % line
                    print >> outfile, '%s\t%s%s' % (confip, hostname, comment)
                elif len(parts) == 2 and len(
                        filter(lambda h: '.' in h, parts)) == 1:
                    # Two hostnames, one a hostname, one a domain name. Replace
                    # the hostname
                    hostnames = map(
                            lambda h: ('.' in h) and h or hostname, parts)
                    print >> outfile, '# %s\t# Removed by nova-agent' % line
                    print >> outfile, '%s\t%s%s' % (confip,
                            ' '.join(hostnames), comment)
                else:
                    # Don't know how to handle this line, so skip it
                    print >> outfile, line

                ips.remove(confip)
            else:
                print >> outfile, line
        else:
            print >> outfile, line

    # Add public IPs we didn't manage to patch
    for ip in ips:
        print >> outfile, '%s\t%s' % (ip, hostname)

    outfile.seek(0)
    return outfile.read()


def get_etc_hosts(interfaces, hostname):
    if os.path.exists(HOSTS_FILE):
        infile = open(HOSTS_FILE)
    else:
        infile = StringIO()

    return HOSTS_FILE, _get_etc_hosts(infile, interfaces, hostname)


def get_gateways(interfaces):
    gateway4s = []
    gateway6s = []

    for interface in interfaces.itervalues():
        gateway = interface.get('gateway4')
        if gateway:
            gateway4s.append(gateway)

        gateway = interface.get('gateway6')
        if gateway:
            gateway6s.append(gateway)

    if len(gateway4s) > 1:
        raise RuntimeError("Multiple IPv4 default routes specified")
    if len(gateway6s) > 1:
        raise RuntimeError("Multiple IPv6 default routes specified")

    gateway4 = gateway4s and gateway4s[0] or None
    gateway6 = gateway6s and gateway6s[0] or None

    return gateway4, gateway6


def get_nameservers(interfaces):
    for interface in interfaces.itervalues():
        for nameserver in interface['dns']:
            yield nameserver


def get_resolv_conf(interfaces):
    resolv_data = ''
    for nameserver in get_nameservers(interfaces):
        resolv_data += 'nameserver %s\n' % nameserver

    if not resolv_data:
        return None, None

    return RESOLV_CONF_FILE, '# Automatically generated, do not edit\n' + \
                             resolv_data


def sethostname(hostname):
    agentlib.sethostname(hostname)


def update_files(update_files, remove_files=None, dont_rename=False):
    if not remove_files:
        remove_files = set()
    for filepath, data in update_files.iteritems():
        if os.path.exists(filepath):
            # If the data is the same, skip it, nothing to do
            if data == open(filepath).read():
                logging.info("skipping %s (no changes)" % filepath)
                continue

        tmp_file = filepath + ".%d~" % os.getpid()
        bak_file = filepath + ".%d~" % time.time()

        logging.info("writing %s" % filepath)

        f = open(tmp_file, 'w')
        try:
            f.write(data)
            f.close()

            os.chown(tmp_file, 0, 0)
            os.chmod(tmp_file, 0644)
            if not dont_rename and os.path.exists(filepath):
                os.rename(filepath, bak_file)
        except Exception, e:
            os.unlink(tmp_file)
            raise e

        if not dont_rename:
            try:
                os.rename(tmp_file, filepath)
            except Exception, e:
                os.rename(bak_file, filepath)
                raise e
        else:
            os.rename(bak_file, filepath)

    for filepath in remove_files:
        logging.info("moving aside old file %s" % filepath)
        if not dont_rename:
            os.rename(filepath, filepath + ".%d~" % time.time())
