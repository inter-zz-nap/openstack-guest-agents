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

using System.IO;
using System.Net;
using Rackspace.Cloud.Server.Common.AgentUpdate;
using Rackspace.Cloud.Server.Common.Configuration;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.UpdaterService.Commands {
    public interface IAgentDownload : ICommand {
    }

    public class AgentDownload : IAgentDownload {
        private readonly ILogger _logger;

        public AgentDownload(ILogger logger) {
            _logger = logger;
        }

        public void Execute(AgentUpdateInfo agentUpdateInfo) {
            _logger.Log("Downloading Agent ...");

            if (!Directory.Exists(SvcConfiguration.AgentVersionUpdatesPath))
                Directory.CreateDirectory(SvcConfiguration.AgentVersionUpdatesPath);

            var webClient = new WebClient();
            webClient.DownloadFile(agentUpdateInfo.url, Constants.AgentServiceReleasePackage);

            _logger.Log("Agent downloaded.");
        }
    }
}
