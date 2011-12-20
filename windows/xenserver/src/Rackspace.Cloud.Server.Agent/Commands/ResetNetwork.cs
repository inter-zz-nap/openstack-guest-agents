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

using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using System.Linq;

namespace Rackspace.Cloud.Server.Agent.Commands {
    /// <summary>
    /// Do not change name unless the server team is changing the command name in xen store.
    /// </summary>
    public class ResetNetwork : IExecutableCommand {
        private readonly ISetNetworkInterface _setNetworkInterface;
        private readonly IXenNetworkInformation _xenNetworkInformation;
        private readonly ISetNetworkRoutes _setNetworkRoutes;

        public ResetNetwork(ISetNetworkInterface setNetworkInterface, IXenNetworkInformation xenNetworkInformation, ISetNetworkRoutes setNetworkRoutes) {
            _setNetworkInterface = setNetworkInterface;
            _xenNetworkInformation = xenNetworkInformation;
            _setNetworkRoutes = setNetworkRoutes;
        }

        public ExecutableResult Execute(string keyValue) {
            var network = _xenNetworkInformation.Get();

            _setNetworkInterface.Execute(network.Interfaces.Values.ToList());
            _setNetworkRoutes.Execute(network);

            return new ExecutableResult();
        }
    }
}