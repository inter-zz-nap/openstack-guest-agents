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

using System.ServiceProcess;
using Rackspace.Cloud.Server.Common.AgentUpdate;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.UpdaterService.Commands {
    public interface IStartAgentService : ICommand {
    }

    public class StartAgentService : IStartAgentService {
        private readonly ILogger _logger;

        public StartAgentService(ILogger logger) {
            _logger = logger;
        }

        public void Execute(AgentUpdateInfo agentUpdateInfo) {
            _logger.Log("Starting Agent Service ...");
            var serviceController = new ServiceController(Constants.AgentServiceName);
            if (serviceController.Status == ServiceControllerStatus.Running) {
                _logger.Log("Agent service already started.");
                return;
            }

            serviceController.Start();
            serviceController.WaitForStatus(ServiceControllerStatus.Running);

            serviceController.Close();
            _logger.Log("Agent Service started and now running ...");
        }
    }
}
