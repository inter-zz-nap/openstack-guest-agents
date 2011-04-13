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
using System.Management;

namespace Rackspace.Cloud.Server.Agent.WMI {
    public interface IWmiMacNetworkNameGetter {
        IDictionary<string, string> Get();
    }

    public class WmiMacNetworkNameGetter : IWmiMacNetworkNameGetter {
        public IDictionary<string, string> Get() {
            var macAndNetworkName = new Dictionary<string, string>();
            var query = new ObjectQuery("select netconnectionid, MACAddress from win32_NetworkAdapter where netconnectionid is not null");

            var scope = new ManagementScope();
            var searcher = new ManagementObjectSearcher(scope, query);
            var obj = searcher.Get();

            foreach (ManagementObject collection in obj) {
                var macAddress = collection["MACAddress"] == null ? "" : collection["MACAddress"].ToString();
                macAndNetworkName.Add(collection["netconnectionid"].ToString(), macAddress);
            }

            return macAndNetworkName;
        }
    }
}