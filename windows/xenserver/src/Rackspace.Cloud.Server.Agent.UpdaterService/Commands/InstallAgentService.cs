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

using Rackspace.Cloud.Server.Common.AgentUpdate;
using ICSharpCode.SharpZipLib.Zip;
using Rackspace.Cloud.Server.Common.Configuration;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.UpdaterService.Commands {
    public interface IInstallAgentService : ICommand {
    }

    public class InstallAgentService : IInstallAgentService {
        private readonly ILogger _logger;

        public InstallAgentService(ILogger logger) {
            _logger = logger;
        }

        public void Execute(AgentUpdateInfo agentUpdateInfo) {
            _logger.Log("Installing a new version of Agent ...");

            _logger.Log("Unzipping agent zip...");
            UnzipNewAgentVersion();
            _logger.Log("Copying new agent files");
            Utility.CopyFiles(Constants.AgentServiceUnzipPath, SvcConfiguration.AgentPath, _logger);
            _logger.Log("Done copying agent files.");
        }

        private void UnzipNewAgentVersion() {
            _logger.Log("Unzipping files");
            var fz = new FastZip();
            fz.ExtractZip(Constants.AgentServiceReleasePackage, Constants.AgentServiceUnzipPath, "");
            _logger.Log("Unzipping files complete");
        }
    }
}
