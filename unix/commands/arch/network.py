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

# Arch has two different kinds of network configuration. More recently,
# there's 'netcfg' and previously (for lack of a better term) 'legacy'.
#
# legacy uses:
# - 1 shell-script-style global configuration (/etc/rc.conf)
# - one IP per interface
# - routes are per interface
# - gateways are global
# - DNS is per interface
#
# netcfg uses:
# - multiple shell-script-style network configurations, 1 per interface
# - one IP per configuration
# - routes are per interface
# - gateways are per interface
# - DNS is global (/etc/resolv.conf)
#
# netcfg is designed for one IP per configuration, but it's not tolerant
# of the older style colon interfaces for IP aliasing. So we have to use
# a hack to get IP aliasing working:
# https://bbs.archlinux.org/viewtopic.php?pid=951573#p951573
#
# Arch is a rolling release, meaning new features and updated packages
# roll out on a unpredictable schedule. It also means there is no such
# thing as v1.0 or v2.0. We check if the netcfg package is installed to
# determine which format should be used.

import os
import re
import time
import subprocess
import logging
from cStringIO import StringIO

import commands.network

CONF_FILE = "/etc/rc.conf"
NETWORK_DIR = "/etc/network.d"


def _execute(command):
    logging.info('executing %s' % ' '.join(command))

    pipe = subprocess.PIPE
    p = subprocess.Popen(command, stdin=pipe, stdout=pipe, stderr=pipe, env={})

    # Wait for process to finish and get output
    stdout, stderr = p.communicate()

    logging.debug('status = %d' % p.returncode)
    if p.returncode:
        logging.info('stdout = %r' % stdout)
        logging.info('stderr = %r' % stderr)

    return p.returncode


def configure_network(hostname, interfaces):
    update_files = {}

    # We need to figure out what style of network configuration is
    # currently being used by looking at /etc/rc.conf and then look
    # to see what style of network configuration we want to use by
    # looking to see if the netcfg package is installed

    if os.path.exists(CONF_FILE):
        update_files[CONF_FILE] = open(CONF_FILE).read()

    infile = StringIO(update_files.get(CONF_FILE, ''))

    cur_netcfg = True	# Currently using netcfg
    lines, variables = _parse_config(infile)
    lineno = variables.get('DAEMONS')
    if lineno is not None:
        daemons = _parse_variable(lines[lineno])
        if 'network' in daemons:
            # Config uses legacy style networking
            cur_netcfg = False

    status = _execute(['/usr/bin/pacman', '-Q', 'netcfg'])
    use_netcfg = (status == 0)
    logging.info('using %s style configuration' %
                 (use_netcfg and 'netcfg' or 'legacy'))

    if use_netcfg:
        remove_files, netnames = process_interface_files_netcfg(
                update_files, interfaces)
    else:
        process_interface_files_legacy(update_files, interfaces)
        remove_files = set()

        # Generate new /etc/resolv.conf file
        filepath, data = commands.network.get_resolv_conf(interfaces)
        if data:
            update_files[filepath] = data

    # Update config file with new hostname
    infile = StringIO(update_files.get(CONF_FILE, ''))

    data = get_hostname_file(infile, hostname)
    update_files[CONF_FILE] = data

    # Generate new /etc/hosts file
    filepath, data = commands.network.get_etc_hosts(interfaces, hostname)
    update_files[filepath] = data

    # Set hostname
    try:
        commands.network.sethostname(hostname)
    except Exception, e:
        logging.error("Couldn't sethostname(): %s" % str(e))
        return (500, "Couldn't set hostname: %s" % str(e))

    # Stage files
    commands.network.stage_files(update_files)

    errors = set()

    # Down network
    logging.info('configuring interfaces down')
    if cur_netcfg:
        for netname in netnames:
            if not interfaces[netname]['up']:
                # Don't try to down an interface that isn't already up
                logging.info('  %s, skipped (already down)' %
                             netname)
                continue

            status = _execute(['/usr/bin/netcfg', '-d', netname])
            if status != 0:
                logging.info('  %s, failed (status %d)' % (netname, status))
                # Treat down failures as soft failures
            else:
                logging.info('  %s, success' % netname)
    else:
        status = _execute(['/etc/rc.d/network', 'stop'])
        if status != 0:
            return (500, "Couldn't stop network: %d" % status)

    # Move files
    commands.network.move_files(update_files, remove_files)

    # Up network
    logging.info('configuring interfaces up')
    if use_netcfg:
        for netname in netnames:
            status = _execute(['/usr/bin/netcfg', '-u', netname])
            if status != 0:
                logging.info('  %s, failed (status %d), trying again' %
                             (netname, status))

                # HACK: Migrating from legacy to netcfg configurations is
                # troublesome because of Arch bugs. Stopping the network
                # in legacy downs the interface, but doesn't remove the IP
                # addresses. This causes netcfg to complain and fail when
                # we go to configure the interface up. As a side-effect, it
                # will remove the offending IP. A second attempt to configure
                # the interface up succeeds. So we'll try a second time.
                status = _execute(['/usr/bin/netcfg', '-u', netname])
                if status != 0:
                    logging.info('  %s, failed (status %d)' %
                                 (netname, status))
                    errors.add(netname)
                else:
                    logging.info('  %s, success' % netname)
            else:
                logging.info('  %s, success' % netname)
    else:
        status = _execute(['/etc/rc.d/network', 'start'])
        if status != 0:
            return (500, "Couldn't start network: %d" % status)

    if errors:
        errors = list(errors)
        errors.sort()
        return (500, 'Failed to start ' + ', '.join(errors))

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


def _parse_variable(line, strip_bang=False):
    k, v = line.split('=')
    v = v.strip()
    if v[0] == '(' and v[-1] == ')':
        v = v[1:-1]

    vars = re.split('\s+', v.strip())
    if strip_bang:
        vars = [v.lstrip('!') for v in vars]
    return vars


def _parse_config(infile):
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

    return lines, variables


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

    gateway4, gateway6 = commands.network.get_gateways(interfaces)

    ifnames = interfaces.keys()
    ifnames.sort()

    for ifname_prefix in ifnames:
        interface = interfaces[ifname_prefix]

        ip4s = interface['ip4s']
        ip6s = interface['ip6s']

        ifname_suffix_num = 0

        for ip4, ip6 in map(None, ip4s, ip6s):
            if ifname_suffix_num:
                ifname = "%s:%d" % (ifname_prefix, ifname_suffix_num)
            else:
                ifname = ifname_prefix

            line = [ifname]
            if ip4:
                line.append('%(address)s netmask %(netmask)s' % ip4)

            if ip6:
                line.append('add %(address)s/%(prefixlen)s' % ip6)

            ifname_suffix_num += 1

            ifaces.append((ifname.replace(':', '_'), ' '.join(line)))

        for i, route in enumerate(interface['routes']):
            line = "-net %(network)s netmask %(netmask)s gw %(gateway)s" % \
                    route

            routes.append(('%s_route%d' % (ifname_prefix, i), line))

    if gateway4:
        routes.append(('gateway', 'default gw %s' % gateway4))
    if gateway6:
        routes.append(('gateway6', 'default gw %s' % gateway6))

    # Then load old file
    lines, variables = _parse_config(infile)

    # Update INTERFACES
    lineno = variables.get('INTERFACES')
    if lineno is not None:
        # Remove old lines
        for name in _parse_variable(lines[lineno], strip_bang=True):
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
        for name in _parse_variable(lines[lineno], strip_bang=True):
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
        for name in _parse_variable(lines[lineno], strip_bang=True):
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

    # Serialize into new file
    outfile = StringIO()
    for line in lines:
        print >> outfile, line

    outfile.seek(0)
    return outfile.read()


def _get_file_data_netcfg(ifname, interface):
    """
    Return data for (sub-)interfaces
    """

    ifaces = []

    ip4s = interface['ip4s']
    ip6s = interface['ip6s']

    gateway4 = interface['gateway4']
    gateway6 = interface['gateway6']

    dns = interface['dns']

    outfile = StringIO()

    print >>outfile, 'CONNECTION="ethernet"'
    print >>outfile, 'INTERFACE=%s' % ifname

    if ip4s:
        ip4 = ip4s.pop(0)
        print >>outfile, 'IP="static"'
        print >>outfile, 'ADDR="%(address)s"' % ip4
        print >>outfile, 'NETMASK="%(netmask)s"' % ip4

        if gateway4:
            print >>outfile, 'GATEWAY="%s"' % gateway4

    if ip6s:
        ip6 = ip6s.pop(0)
        print >>outfile, 'IP6="static"'
        print >>outfile, 'ADDR6="%(address)s/%(prefixlen)s"' % ip6

        if gateway6:
            print >>outfile, 'GATEWAY6="%s"' % gateway6

    routes = ['"%(network)s/%(netmask)s via %(gateway)s"' % route 
              for route in interface['routes']]

    if routes:
        print >>outfile, 'ROUTES=(%s)' % ' '.join(routes)

    if dns:
        print >>outfile, 'DNS=(%s)' % ' '.join(dns)

    # Finally add remaining aliases. This is kind of hacky, see comment at
    # top for explanation
    aliases = ['%(address)s/%(netmask)s' % ip4 for ip4 in ip4s] + \
              ['%(address)s/%(prefixlen)s' % ip6 for ip6 in ip6s]

    if aliases:
        commands = '; '.join(['ip addr add %s dev %s' % (a, ifname)
                              for a in aliases])
        print >>outfile, 'POST_UP="%s"' % commands

        aliases.reverse()
        commands = '; '.join(['ip addr del %s dev %s' % (a, ifname)
                              for a in aliases])
        print >>outfile, 'PRE_DOWN="%s"' % commands

    outfile.seek(0)
    return outfile.read()


def _update_rc_conf_netcfg(infile, netnames):
    # Load old file
    lines, variables = _parse_config(infile)

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
        for name in _parse_variable(lines[lineno], strip_bang=True):
            nlineno = variables.get(name)
            if nlineno is not None:
                lines[nlineno] = '#' + lines[lineno]

        lines[lineno] = '#' + lines[lineno]

    # (Possibly) comment out ROUTES
    lineno = variables.get('ROUTES')
    if lineno is not None:
        for name in _parse_variable(lines[lineno], strip_bang=True):
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

    # Serialize into new file
    outfile = StringIO()
    for line in lines:
        print >> outfile, line

    outfile.seek(0)
    return outfile.read()


def get_interface_files(infiles, interfaces, version):
    if version == 'netcfg':
        update_files = {}
        netnames = []
        for ifname, interface in interfaces.iteritems():
            data = _get_file_data_netcfg(ifname, interface)

            filepath = os.path.join(NETWORK_DIR, ifname)
            update_files[filepath] = data

            netnames.append(ifname)

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
    for ifname, interface in interfaces.iteritems():
        data = _get_file_data_netcfg(ifname, interface)

        filepath = os.path.join(NETWORK_DIR, ifname)
        update_files[filepath] = data
        if filepath in remove_files:
            remove_files.remove(filepath)

        netnames.append(ifname)

    infile = StringIO(update_files.get(CONF_FILE, ''))
    data = _update_rc_conf_netcfg(infile, netnames)
    update_files[CONF_FILE] = data

    return remove_files, netnames
