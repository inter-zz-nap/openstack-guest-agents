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

using System.Collections.Generic;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Utilities;

namespace Rackspace.Cloud.Server.Agent {
    public interface IXenNetworkInformation {
        Network Get();
    }

    public class XenNetworkInformation : IXenNetworkInformation {
        private readonly IXenStore _xenStore;
        private readonly string _networkKeyLocation = Constants.Combine(Constants.ReadOnlyDataConfigBase, Constants.NetworkingBase);
        public XenNetworkInformation(IXenStore xenstore) {
            _xenStore = xenstore;
        }

        public Network Get() {
            return new Network { Interfaces = GetInterfaces() };
        }

        private IDictionary<string, NetworkInterface> GetInterfaces() {
            IDictionary<string, NetworkInterface> interfaces = new Dictionary<string, NetworkInterface>();

            var macAddressesWithoutColons =
                _xenStore.Read(_networkKeyLocation);

            foreach (var macAddress in macAddressesWithoutColons) {
                var jsonData = _xenStore.ReadVmDataKey(macAddress);
                var networkInterface = new Json<NetworkInterface>().Deserialize(jsonData);
                interfaces.Add(networkInterface.mac.ToUpper(), networkInterface);
            }

            return interfaces;
        }
    }
}
