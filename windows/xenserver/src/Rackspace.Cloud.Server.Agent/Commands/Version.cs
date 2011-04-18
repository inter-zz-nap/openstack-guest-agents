// Copyright 2011 OpenStack LLC.
// All Rights Reserved.
//
//    Licensed under the Apache License, Version 2.0 (the "License"); you may
//    not use this file except in compliance with the License. You may obtain
//    a copy of the License at
//
//         http://www.apache.org/licenses/LICENSE-2.0
//
//    Unless required by applicable law or agreed to in writing, software
//    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
//    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
//    License for the specific language governing permissions and limitations
//    under the License.

using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Actions;

namespace Rackspace.Cloud.Server.Agent.Commands {
    /// <summary>
    /// Do not change name unless the server team is changing the command name in xen store.
    /// </summary>
    public class Version : IExecutableCommand {
        private readonly IVersionChecker _versionChecker;
        public const string XENTOOLS = "xentools";
        public const string AGENT = "agent";
        public const string AGENT_UPDATER = "updater";
        public const string XENTOOLS_PATH = @"C:\Program Files\Citrix\XenTools\xenservice.exe";
        public const string AGENT_PATH = @"C:\Program Files\Rackspace\Cloud Servers\Agent\Rackspace.Cloud.Server.Agent.dll";
        public const string AGENT_UPDATER_PATH = @"C:\Program Files\Rackspace\Cloud Servers\AgentUpdater\Rackspace.Cloud.Server.Agent.UpdaterService.exe";

        public Version(IVersionChecker versionChecker)
        {
            _versionChecker = versionChecker;
        }

        public ExecutableResult Execute(string value)
        {
            var path = "";
            if (value == XENTOOLS) path = XENTOOLS_PATH;
            if (value == AGENT) path = AGENT_PATH;
            if (value == AGENT_UPDATER) path = AGENT_UPDATER_PATH;

            return new ExecutableResult
                       {
                           Output = new[] {_versionChecker.Check(path)}
                       };
        }
    }
}
