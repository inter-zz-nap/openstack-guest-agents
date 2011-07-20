#!/usr/bin/python

import base64
import binascii
import os
import subprocess
import sys
import time
import simplejson as json


class AgentCommError(Exception):
    pass


class AgentCommArgError(AgentCommError):
    pass


class AgentCommUnknownCommand(AgentCommError):
    pass


class Commands(object):
    COMMANDS = {}

    @classmethod
    def command_opt(self, arg):
        """Decorator used to define a command"""

        def wrap(f):
            """Function argument to decorator"""

            self.COMMANDS[arg] = f
            return f
        return wrap


class AgentComm(object):
    """Agent Communication Class"""

    def __init__(self, domid):
        prefix = "/local/domain/%d" % domid
        self.xs_request_path = "%s/data/host" % prefix
        self.xs_response_path = "%s/data/guest" % prefix
        self.xs_networking_path = "%s/vm-data/networking" % prefix
        self.xs_hostname_path = "%s/vm-data/hostname" % prefix

    def _mod_exp(self, num, exp, mod):
        result = 1
        while exp > 0:
            if (exp & 1) == 1:
                result = (result * num) % mod
            exp = exp >> 1
            num = (num * num) % mod
        return result

    def _get_uuid(self):
        # Older Windows agents require something that actually looks like a
        # UUID. dom0 has an old python that doesn't have the uuid module, so
        # create it ourselves by hand
        return '-'.join([binascii.hexlify(os.urandom(x))
                         for x in (4, 2, 2, 2, 6)])

    def _do_request(self, command, value):
        uuid = self._get_uuid()

        req = json.dumps({"name": command, "value": value})

        req_path = "%s/%s" % (self.xs_request_path, uuid)
        resp_path = "%s/%s" % (self.xs_response_path, uuid)

        print "Writing request to %s: %s" % (req_path, req)
        subprocess.call(["xenstore-write", req_path, req])

        resp = None

        for x in xrange(0, 30):
            p = subprocess.Popen(["xenstore-read %s" % resp_path],
                    shell=True, stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE).stdout
            resp = p.read()
            p.close()
            if resp:
                break
            time.sleep(1)

        if not resp:
            raise SystemError("No response received")

        subprocess.call(["xenstore-rm", resp_path])

        resp = json.loads(resp.rstrip())

        return (resp['returncode'], resp['message'])

    def run_command(self, command, *args):

        cmd_func = Commands.COMMANDS.get(command, None)
        if not cmd_func:
            raise AgentCommUnknownCommand()
        result = cmd_func(self, *args)
        if result:
            print "Got result: %s" % repr(result)
        return True

    @Commands.command_opt("password")
    def _password_cmd(self, args):
        if len(args) < 1:
            print "Usage: password <password>"
            return None

        password = args[0]
        # prime to use
        prime = 162259276829213363391578010288127
        my_private_key = int(binascii.hexlify(os.urandom(10)), 16)
        my_public_key = self._mod_exp(5, my_private_key, prime)

        # Older Windows agent requires public key to be a string, not an
        # integer
        retcode, message = self._do_request("keyinit", str(my_public_key))

        if retcode != 'D0':
            raise SystemError(
                    "Invalid response to keyinit: %s" % retcode)

        # Older Windows agent will sometimes add \\r\\n (escaped CRLF) to
        # the end of responses.
        shared_key = str(self._mod_exp(int(message.strip('\\r\\n')),
                my_private_key, prime))

        cmd = ["openssl", "enc", "-aes-128-cbc", "-a",
                "-nosalt", "-pass", "pass:%s" % shared_key]

        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Older Windows and Linux agents require password to have trailing
        # newline added
        p.stdin.write(password + '\n')
        p.stdin.close()
        b64_pass = p.stdout.read().rstrip()
        err = p.stderr.read()
        del p

        if err != '':
            print err
            return(500, "Doh")

        return self._do_request("password", b64_pass)

    @Commands.command_opt("version")
    def _version_cmd(self, args):
        if args:
            arg = args[0]
        else:
            arg = "agent"
        return self._do_request("version", arg)

    @Commands.command_opt("features")
    def _features_cmd(self, args):
        return self._do_request("features", "")

    @Commands.command_opt("agentupdate")
    def _update_cmd(self, args):
        if len(args) < 2:
            raise AgentCommArgError("Usage: agentupdate <url> <md5sum>")

        return self._do_request("agentupdate", args[0] + "," + args[1])

    @Commands.command_opt("resetnetwork")
    def _reset_network(self, args):
        return self._do_request("resetnetwork", "")

    @Commands.command_opt("injectfile")
    def _inject_file(self, args):

        if len(args) < 2:
            raise AgentCommArgError(
                    "Usage: injectfile <local_filename> <dest_filename>")

        filename = args[0]
        filepath = args[1]

        f = open(filename, 'rb')
        data = f.read()
        f.close()

        b64_arg = base64.b64encode("%s,%s" % (filepath, data))

        return self._do_request("injectfile", b64_arg)

    @Commands.command_opt("kmsactivate")
    def _kmsactivate_cmd(self, args):
        if args:
            arg = args[0]
        else:
            arg = "agent"
        return self._do_request("kmsactivate",
            {'activation_key': args[0],
             'profile': args[1],
             'domains': [args[2]]})

    @Commands.command_opt("help")
    def _help_cmd(self, args):
        print "Available commands:"
        for cmd_name in Commands.COMMANDS:
            print cmd_name

if __name__ == "__main__":
    args = sys.argv
    prog = args.pop(0)

    if len(args) < 2:
        print "Usage: %s <domid> <command> [<args>]" % prog
        AgentComm(0).run_command("help", "")
        sys.exit(1)

    arg1 = args.pop(0)

    try:
        domid = int(arg1)
    except ValueError:
        print "Error: Invalid domain ID"
        print "Usage: %s <domid> <command> [<args>]"
        sys.exit(1)

    cmd = args.pop(0)

    if domid == 0:
        print "Invalid dom id"
        sys.exit(1)

    if len(cmd) == 0:
        print "Invalid command"
        sys.exit(1)

    try:
        AgentComm(domid).run_command(cmd, args)
    except AgentCommUnknownCommand:
        print "Error: Unknown command '%s'" % cmd
        sys.exit(1)
    except AgentCommArgError, e:
        print e
        sys.exit(1)

    sys.exit(0)
