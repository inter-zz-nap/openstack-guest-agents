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
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface ISetNetworkRoutes
    {
        void Execute(Network network);
    }

    public class SetNetworkRoutes : ISetNetworkRoutes
    {
        private readonly IExecutableProcessQueue _executableProcessQueue;
        private readonly IRegistryReader _registryReader;
        private readonly ILogger _logger;

        public SetNetworkRoutes(IExecutableProcessQueue executableProcessQueue, IRegistryReader registryReader, ILogger logger) {
            _executableProcessQueue = executableProcessQueue;
            _registryReader = registryReader;
            _logger = logger;
        }

        public void Execute(Network network)
        {
            IList<NetworkRoute> routes = new List<NetworkRoute>();
            var publicGateway = "";

            foreach (var networkInterface in network.Interfaces.Values)
            {
                if (networkInterface.label.ToLower() == "public") publicGateway = networkInterface.gateway;
                if(networkInterface.routes == null || networkInterface.routes.Length < 1) continue;

                foreach (var route in networkInterface.routes)
                {
                    if (routes.Contains(route)) continue;
                    routes.Add(route);
                }
            }

            _logger.Log("Routes Found: " + routes.Count);

            DeleteExistingPersistentRoutesRoutes();
            _executableProcessQueue.Enqueue("route", String.Format("-p add 0.0.0.0 mask 0.0.0.0 {0} metric 2", publicGateway));

            foreach (var route in routes)
            {
                _executableProcessQueue.Enqueue("route", String.Format("-p add {0} mask {1} {2} metric 10", route.route, route.netmask, route.gateway));
            }

            _executableProcessQueue.Go();
        }

        private void DeleteExistingPersistentRoutesRoutes() {
            var persistedRoutesFromTheRegistry =
                _registryReader.GetValuesFrom(@"SYSTEM\CurrentControlSet\services\Tcpip\Parameters\PersistentRoutes");
            foreach(var persistedRoute in persistedRoutesFromTheRegistry) {
                var routeInfo = persistedRoute.Split(',');
                _executableProcessQueue.Enqueue("route", String.Format("delete {0}", routeInfo[0]));
            }
        }
    }
}