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
            getattr(json, 'dumps', json.write)(buf)

        @staticmethod
        def deserialize(buf):
            getattr(json, 'loads', json.read)(buf)

from cStringIO import StringIO
import logging
import os
import platform
import pyxenstore
import re
import time

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
                        "gentoo": gentoo,
                        "FreeBSD": freebsd}

        system = os.uname()[0]
        if system == "Linux":
            try:
                system = platform.linux_distribution(None)[0]
            except AttributeError:
                # linux_distribution doesn't exist... try the older
                # call
                system = platform.dist(None)[0]

            # Gentoo returns 'Gentoo Base System', so let's make that
            # something easier to use
            if system:
                system = system.lower().split(' ')[0]
            # Arch Linux returns None for platform.linux_distribution()
            elif os.path.exists('/etc/arch-release'):
                system = 'arch'

        if not system:
            return None
        else:
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

        data = {"hostname": hostname, "interfaces": interfaces}

        return os_mod.network.configure_network(data)


def _get_etc_hosts(infile, interfaces, hostname):
    ips = set()
    for interface in interfaces:
        if not ips and interface['label'] == 'public':
            ip4s = interface.get('ips')
            if ip4s:
                ips.add(ip4s[0]['ip'])

            ip6s = interface.get('ip6s')
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
        bak_file = filepath + ".%d.bak" % time.time()

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
            os.rename(filepath, filepath + ".%d.bak" % time.time())
