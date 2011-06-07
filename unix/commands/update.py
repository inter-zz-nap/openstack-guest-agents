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
JSON agent update handling plugin
"""

import os
import shutil
import subprocess
import tarfile
import urllib

import commands

TMP_PATH = "/var/run"
DEST_PATH = "/usr/share/nova-agent"
DEST_FILE = "/var/run/nova-agent.tar"
INIT_SCRIPTS = ["/etc/init.d/nova-agent",
        "/etc/rc.d/nova-agent",
        "/etc/nova-agent.init"]

# This is to support older python versions that don't have hashlib
try:
    import hashlib
except ImportError:
    import md5

    class hashlib(object):
        """Fake hashlib module as a class"""

        @staticmethod
        def md5():
            return md5.new()


class AgentUpdateError(Exception):

    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return self.arg

    __repr__ = __str__


class UpdateCommand(commands.CommandBase):

    def __init__(self, *args, **kwargs):
        self.tmp_path = kwargs.get("tmpdir", TMP_PATH)

    def _get_to_local_file(self, url, md5sum):
        try:
            filename = url[url.rindex('/') + 1:]
            ext_pos = filename.index('.')
            local_filename = "%s/%s-%d%s" % (
                    self.tmp_path,
                    filename[:ext_pos],
                    os.getpid(),
                    filename[ext_pos:])
        except ValueError:
            raise AgentUpdateError("Invalid URL")

        try:
            urllib.urlretrieve(url, local_filename)
        except Exception, e:
            raise AgentUpdateError(str(e))

        try:
            f = file(local_filename, 'rb')
        except:
            os.unlink(local_filename)
            raise AgentUpdateError("Couldn't open local file")

        m = hashlib.md5()
        while True:
            file_data = f.read(8096)
            if not file_data:
                break
            m.update(file_data)

        f.close()

        digest = m.hexdigest()
        if digest != md5sum:
            os.unlink(local_filename)
            raise AgentUpdateError("MD5 sums do not match (%s != %s)" % (
                    md5sum, digest))

        return local_filename

    @commands.command_add('agentupdate')
    def update_cmd(self, data):

        if isinstance(data, basestring):
            (url, md5sum) = data.split(',', 1)
        elif isinstance(data, dict):
            try:
                url = data['url']
                md5sum = data['md5sum']
            except KeyError:
                return (500,
                        "Missing URL or MD5 sum in dictionary arguments")
        else:
            return (500, "Invalid arguments")

        try:
            local_filename = self._get_to_local_file(url, md5sum)
        except AgentUpdateError, e:
            return (500, str(e))

        ext = local_filename[local_filename.rindex('.') + 1:]

        if ext != ".tar":
            dest_filename = "%s.%s" % (
                    DEST_FILE,
                    ext)
        else:
            dest_filename = "%s"

        try:
            t = tarfile.open(local_filename, 'r:*')
        except tarfile.TarError, e:
            os.unlink(local_filename)
            return (500, "%s: %s" % (local_filename, str(e)))

        found_installer = None
        for tarinfo in t.getmembers():
            name = tarinfo.name
            while name.startswith('../') or name.startswith('./') \
                    or name.startswith('/'):
                name = name[1:]
            # Check for 'installer.sh' in root of the tar or in a
            # subdirectory off of the root
            if name == "installer.sh" or (name.count('/') == 1 and
                    name.split('/')[1] == "installer.sh"):
                found_installer = name
                break

        pipe = subprocess.PIPE

        if found_installer:
            dest_path = "%s.%d" % (DEST_PATH, os.getpid())

            try:
                t.extractall(dest_path)
                t.close()
            except tarfile.TarError, e:
                os.unlink(local_filename)
                return (500, str(e))

            os.unlink(local_filename)

            p = subprocess.Popen(["%s/%s" % (dest_path, found_installer)],
                    stdin=pipe, stdout=pipe, stderr=pipe, env={})
            p.communicate(None)
            retcode = p.returncode

            shutil.rmtree(dest_path, ignore_errors=True)

            if retcode != 0:
                return (500, "Agent installer script failed: %d" % retcode)
        else:
            #
            # Old way, no installer
            #

            t.close()

            # Using shutil.move instead of os.rename() because we might be
            # moving across filesystems.
            shutil.move(local_filename, dest_filename)

        init_script = None
        for script in INIT_SCRIPTS:
            if os.path.exists(script):
                init_script = script
                break

        if not init_script:
            return(404, "No init script found to restart")

        try:
            p = subprocess.Popen(["sh", init_script, "restart"],
                    stdin=pipe, stdout=pipe, stderr=pipe, env={})
            p.communicate(None)
            retcode = p.returncode
        except OSError, e:
            return (500, "Couldn't restart the agent: %s" % str(e))

        if retcode != 0:
            return (500, "Couldn't restart the agent: %d" % retcode)

        return (0, "")
