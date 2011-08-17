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
NETWORK_DIR = "/etc/network.d"
RESOLV_FILE = "/etc/resolv.conf"

INTERFACE_LABELS = {"public": "eth0",
                    "private": "eth1"}


def _execute(command):
    pipe = subprocess.PIPE
    logging.info('executing %s' % ' '.join(command))
    p = subprocess.Popen(command, stdin=pipe, stdout=pipe, stderr=pipe, env={})
    logging.debug('waiting on pid %d' % p.pid)
    status = os.waitpid(p.pid, 0)[1]
    logging.debug('status = %d' % status)

    return status


def configure_network(network_config, *args, **kwargs):

    # Update config file with new interface configuration
    interfaces = network_config.get('interfaces', [])

    # Check if netcfg is installed (and should be used)
    status = _execute(['/usr/bin/pacman', '-Q', 'netcfg'])
    use_netcfg = (status == 0)

    update_files = {}

    if os.path.exists(CONF_FILE):
        update_files[CONF_FILE] = open(CONF_FILE).read()

    if use_netcfg:
        remove_files, netnames = process_interface_files_netcfg(
                update_files, interfaces)
    else:
        process_interface_files_legacy(update_files, interfaces)
        remove_files = set()

        # Generate new /etc/resolv.conf file
        data = _get_resolv_conf(interfaces)
        update_files[RESOLV_FILE] = data

    # Update config file with new hostname
    hostname = network_config.get('hostname')

    infile = StringIO(update_files.get(CONF_FILE, ''))

    data = get_hostname_file(infile, hostname)
    update_files[CONF_FILE] = data

    # Generate new /etc/hosts file
    filepath, data = commands.network.get_etc_hosts(interfaces, hostname)
    update_files[filepath] = data

    # Write out new files
    commands.network.update_files(update_files, remove_files)

    # Set hostname
    try:
        commands.network.sethostname(hostname)
    except Exception, e:
        logging.error("Couldn't sethostname(): %s" % str(e))
        return (500, "Couldn't set hostname: %s" % str(e))

    # Restart network
    if use_netcfg:
        for netname in netnames:
            status = _execute(['/usr/bin/netcfg', '-r', netname])
            if status != 0:
                return (500, "Couldn't restart %s: %d" % (netname, status))
    else:
        status = _execute(['/etc/rc.d/network', 'restart'])
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


def _parse_variable(line):
    k, v = line.split('=')
    v = v.strip()
    if v[0] == '(' and v[-1] == ')':
        v = v[1:-1]

    return [name.lstrip('!') for name in re.split('\s+', v.strip())]


def _update_rc_conf_legacy(infile, interfaces):
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
                    ip = ip_info.get('address', ip_info.get('ip'))
                    if not ip:
                        raise SystemError(
                                "Missing IP in interface's IP list")
                    netmask = ip_info.get('netmask')
                    if not netmask:
                        raise SystemError(
                                "Missing netmask in interface's IP list")

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

    # (Possibly) comment out NETWORKS
    lineno = variables.get('NETWORKS')
    if lineno is not None:
        for name in _parse_variable(lines[lineno]):
            nlineno = variables.get(name)
            if nlineno is not None:
                lines[nlineno] = '#' + lines[lineno]

        lines[lineno] = '#' + lines[lineno]

    # (Possibly) update DAEMONS
    lineno = variables.get('DAEMONS')
    if lineno is not None:
        daemons = _parse_variable(lines[lineno])
        try:
            network = daemons.index('!network')
            daemons[network] = 'network'
            if '@net-profiles' in daemons:
                daemons.remove('@net-profiles')
            lines[lineno] = 'DAEMONS=(%s)' % ' '.join(daemons)
        except ValueError:
            pass

    # Filter out any removed lines
    lines = filter(lambda l: l is not None, lines)

    # Patch into new file
    outfile = StringIO()
    for line in lines:
        print >> outfile, line

    outfile.seek(0)
    return outfile.read()


def _get_file_data_netcfg(interface):
    """
    Return data for (sub-)interfaces
    """

    ifaces = []

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

        outfile = StringIO()

        print >>outfile, 'CONNECTION="ethernet"'
        print >>outfile, 'INTERFACE=%s' % ifname

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

                print >>outfile, 'IP="static"'
                print >>outfile, 'ADDR="%s"' % ip
                print >>outfile, 'NETMASK="%s"' % netmask
                if gateway4:
                    print >>outfile, 'GATEWAY="%s"' % gateway4

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

                print >>outfile, 'IP6="static"'
                print >>outfile, 'ADDR6="%s/%s"' % (ip, netmask)

                gateway6 = ip_info.get('gateway', gateway6)
                if gateway6:
                    print >>outfile, 'GATEWAY6="%s"' % gateway6

        if not ifname_suffix_num:
            # Add routes to first interface
            routes = []
            for route in interface.get('routes', []):
                network = route['route']
                netmask = route['netmask']
                gateway = route['gateway']
                routes.append('"%s/%s via %s"' % (network, netmask, gateway))

            if routes:
                print >>outfile, 'ROUTES=(%s)' % ' '.join(routes)

            if dns:
                print >>outfile, 'DNS=(%s)' % ' '.join(dns)

        outfile.seek(0)
        ifaces.append((ifname, outfile.read()))

        ifname_suffix_num += 1

    return ifaces


def _update_rc_conf_netcfg(infile, netnames):
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

    # Update NETWORKS
    lineno = variables.get('NETWORKS')
    if lineno is None:
        # Add new line to contain it
        lines.append('')
        lineno = len(lines) - 1

    lines[lineno] = 'NETWORKS=(%s)' % ' '.join(netnames)

    # (Possibly) comment out INTERFACES
    lineno = variables.get('INTERFACES')
    if lineno is not None:
        for name in _parse_variable(lines[lineno]):
            nlineno = variables.get(name)
            if nlineno is not None:
                lines[nlineno] = '#' + lines[lineno]

        lines[lineno] = '#' + lines[lineno]

    # (Possibly) comment out ROUTES
    lineno = variables.get('ROUTES')
    if lineno is not None:
        for name in _parse_variable(lines[lineno]):
            nlineno = variables.get(name)
            if nlineno is not None:
                lines[nlineno] = '#' + lines[lineno]

        lines[lineno] = '#' + lines[lineno]

    # (Possibly) update DAEMONS
    lineno = variables.get('DAEMONS')
    if lineno is not None:
        daemons = _parse_variable(lines[lineno])
        try:
            network = daemons.index('network')
            daemons[network] = '!network'
            if '@net-profiles' not in daemons:
                daemons.insert(network + 1, '@net-profiles')
            lines[lineno] = 'DAEMONS=(%s)' % ' '.join(daemons)
        except ValueError:
            pass

    # Patch into new file
    outfile = StringIO()
    for line in lines:
        print >> outfile, line

    outfile.seek(0)
    return outfile.read()


def get_interface_files(infiles, interfaces, netcfg):
    if netcfg:
        update_files = {}
        netnames = []
        for interface in interfaces:
            ifaces = _get_file_data_netcfg(interface)

            for ifname, data in ifaces:
                filename = ifname.replace(':', '_')
                filepath = os.path.join(NETWORK_DIR, filename)
                update_files[filepath] = data

                netnames.append(filename)

        infile = StringIO(infiles.get(CONF_FILE, ''))
        data = _update_rc_conf_netcfg(infile, netnames)
        update_files[CONF_FILE] = data

        return update_files
    else:
        infile = StringIO(infiles.get(CONF_FILE, ''))
        data = _update_rc_conf_legacy(infile, interfaces)
        return {CONF_FILE: data}


def process_interface_files_legacy(update_files, interfaces):
    """Generate changeset for interface configuration"""

    infile = StringIO(update_files.get(CONF_FILE, ''))
    data = _update_rc_conf_legacy(infile, interfaces)
    update_files[CONF_FILE] = data


def process_interface_files_netcfg(update_files, interfaces):
    """Generate changeset for interface configuration"""

    # Enumerate all of the existing network files
    remove_files = set()
    for filename in os.listdir(NETWORK_DIR):
        filepath = os.path.join(NETWORK_DIR, filename)
        if not filename.endswith('~') and not os.path.isdir(filepath):
            remove_files.add(filepath)

    netnames = []
    for interface in interfaces:
        subifaces = _get_file_data_netcfg(interface)

        for ifname, data in subifaces:
            filename = ifname.replace(':', '_')
            filepath = os.path.join(NETWORK_DIR, filename)
            update_files[filepath] = data
            if filepath in remove_files:
                remove_files.remove(filepath)

            netnames.append(filename)

    infile = StringIO(update_files.get(CONF_FILE, ''))
    data = _update_rc_conf_netcfg(infile, netnames)
    update_files[CONF_FILE] = data

    return remove_files, netnames
