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

using System;
using System.ServiceProcess;
using Rackspace.Cloud.Server.Common.AgentUpdate;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.UpdaterService.Commands {
    public interface IStopAgentService : ICommand {
    }

    public class StopAgentService : IStopAgentService {
        private readonly ILogger _logger;

        public StopAgentService(ILogger logger) {
            _logger = logger;
        }

        public void Execute(AgentUpdateInfo agentUpdateInfo) {
            _logger.Log("Stopping Agent Service ...");

            var serviceController = new ServiceController(Constants.AgentServiceName);
            if(serviceController.Status == ServiceControllerStatus.Stopped) {
                _logger.Log("Agent Service already stopped.");
                return;
            }

            if(!serviceController.CanStop) throw new ApplicationException("Service {0} can't be stop at this time, please try again later");
            
            serviceController.Stop();
            serviceController.WaitForStatus(ServiceControllerStatus.Stopped);

            serviceController.Close();

            _logger.Log("Agent Service successfully stopped.");
        }
    }
}
