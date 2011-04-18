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
using System.Collections.Generic;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Utilities;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Commands {
    /// <summary>
    /// Do not change name unless the server team is changing the command name in xen store.
    /// </summary>
    public class AgentUpdate : IExecutableCommand {
        private readonly IAgentUpdateMessageSender _agentUpdateMessageSender;
        private readonly IConnectionChecker _connectionChecker;
        private readonly IAgentUpdateMessageHandler _agentUpdateMessageHandler;
        private readonly ILogger _logger;

        public AgentUpdate(IAgentUpdateMessageSender agentUpdateMessageSender, IConnectionChecker connectionChecker, IAgentUpdateMessageHandler agentUpdateMessageHandler, ILogger logger) {
            _agentUpdateMessageSender = agentUpdateMessageSender;
            _connectionChecker = connectionChecker;
            _agentUpdateMessageHandler = agentUpdateMessageHandler;
            _logger = logger;
        }

        public ExecutableResult Execute(string value) {
            _connectionChecker.Check();
            _logger.Log("Agent Update value: " + value);
            var agentUpdateInfo = _agentUpdateMessageHandler.Handle(value);

            try {
                _agentUpdateMessageSender.Send(agentUpdateInfo);

                Statics.ShouldPollXenStore = false;
                return new ExecutableResult();
            }
            catch (Exception ex) {

                _logger.Log("Exception was : " + ex.Message + "\nStackTrace Was: " + ex.StackTrace);
                return new ExecutableResult { Error = new List<string> { "Update failed" }, ExitCode = "1" };
            }
        }
    }
}
