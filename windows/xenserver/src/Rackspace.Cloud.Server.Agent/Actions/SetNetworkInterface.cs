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
using System.Collections.ObjectModel;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Utilities;
using Rackspace.Cloud.Server.Agent.WMI;
using Rackspace.Cloud.Server.Common.Logging;
using System.Linq;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface ISetNetworkInterface {
        void Execute(List<NetworkInterface> networkInterfaces);
    }

    public class SetNetworkInterface : ISetNetworkInterface {
        private readonly IExecutableProcessQueue _executableProcessQueue;
        private readonly IWmiMacNetworkNameGetter _wmiMacNetworkNameGetter;
        private readonly ILogger _logger;

        public SetNetworkInterface(IExecutableProcessQueue executableProcessQueue, IWmiMacNetworkNameGetter wmiMacNetworkNameGetter, ILogger logger) {
            _executableProcessQueue = executableProcessQueue;
            _wmiMacNetworkNameGetter = wmiMacNetworkNameGetter;
            _logger = logger;
        }

        public void Execute(List<NetworkInterface> networkInterfaces) {
            var nameAndMacs = _wmiMacNetworkNameGetter.Get();
            if (WereInterfacesEnabled(nameAndMacs)) nameAndMacs = _wmiMacNetworkNameGetter.Get();
            LogLocalInterfaces(nameAndMacs);

            VerifyAllNetworkInterfacesFoundOnMachine(nameAndMacs, networkInterfaces);

            foreach (var networkName in ReverseSortWithKey(nameAndMacs))
            {
                var matchedNetworkInterface = networkInterfaces.Find(x => nameAndMacs[networkName].Equals(x.mac.ToUpper()));
                if (matchedNetworkInterface != null)
                    SetNetworkInterfaceValues(matchedNetworkInterface, networkName);
            }
        }

        private void VerifyAllNetworkInterfacesFoundOnMachine(IDictionary<string, string> nameAndMacs, List<NetworkInterface> networkInterfaces)
        {
            var networkInterfaceNotFoundOnMachine = networkInterfaces.Find(x => nameAndMacs.FindKey(x.mac.ToUpper()) == null);
            if (networkInterfaceNotFoundOnMachine != null)
                throw new ApplicationException(String.Format("Interface with MAC Addres {0} not found on machine", networkInterfaceNotFoundOnMachine.mac));
        }

        private string[] ReverseSortWithKey(IDictionary<string, string> keyValuePair)
        {
            var allKeys = keyValuePair.Keys.ToArray();
            Array.Sort(allKeys);Array.Reverse(allKeys);
            return allKeys;
        }

        private void SetNetworkInterfaceValues(NetworkInterface networkInterface, string interfaceName)
        {
            CleanseInterfaceForSetup(interfaceName);
            SetupInterface(interfaceName, networkInterface);

            if (networkInterface.dns != null && networkInterface.dns.Length > 0) {
                CleanseDnsForSetup(interfaceName);
                SetupDns(interfaceName, networkInterface);
            }
                    
            if(interfaceName != networkInterface.label)
                _executableProcessQueue.Enqueue("netsh", String.Format("interface set interface name=\"{0}\" newname=\"{1}\"", interfaceName, networkInterface.label));
            
            _executableProcessQueue.Go();
        }

        private void LogLocalInterfaces(IDictionary<string, string> nameAndMacs) {
            _logger.Log("Network Interfaces found locally:");
            foreach (var networkInterface in nameAndMacs) {
                _logger.Log(String.Format("{0} ({1})", networkInterface.Key, networkInterface.Value));
            } 
        }

        private void SetupInterface(string interfaceName, NetworkInterface networkInterface) {
            var primaryIpHasBeenAssigned = false;
            for (var i = 0; i != networkInterface.ips.Length; i++) {
                if (networkInterface.ips[i].enabled != "1") continue;
                if (!string.IsNullOrEmpty(networkInterface.gateway) && !primaryIpHasBeenAssigned) {
                    _executableProcessQueue.Enqueue("netsh",
                                                    String.Format(
                                                        "interface ip add address name=\"{0}\" addr={1} mask={2} gateway={3} gwmetric=2",
                                                        interfaceName, networkInterface.ips[i].ip, networkInterface.ips[i].netmask, networkInterface.gateway));
                    primaryIpHasBeenAssigned = true; 
                    continue;
                }

                _executableProcessQueue.Enqueue("netsh", String.Format("interface ip add address name=\"{0}\" addr={1} mask={2}",
                                                                       interfaceName, networkInterface.ips[i].ip, networkInterface.ips[i].netmask));
            }
        }

        private void SetupDns(string interfaceName, NetworkInterface networkInterface) {
            for (var i = 0; i != networkInterface.dns.Length; i++) {
                _executableProcessQueue.Enqueue("netsh", String.Format("interface ip add dns name=\"{0}\" addr={1} index={2}",
                                                                       interfaceName, networkInterface.dns[i], i + 1));
            }
        }

        private void CleanseInterfaceForSetup(string interfaceName) {
            _executableProcessQueue.Enqueue("netsh", string.Format("interface ip set address name=\"{0}\" source=dhcp", interfaceName), new[] { "0", "1" });
        }

        private void CleanseDnsForSetup(string interfaceName) {
            _executableProcessQueue.Enqueue("netsh", string.Format("interface ip set dns name=\"{0}\" source=dhcp", interfaceName), new[] { "0", "1" });
        }

        private bool WereInterfacesEnabled(IEnumerable<KeyValuePair<string, string>> nameAndMacs) {
            var wereMacsEnabled = false;
            foreach (var nameAndMac in nameAndMacs) {
                if (nameAndMac.Value != string.Empty) continue;
                _executableProcessQueue.Enqueue("netsh", String.Format("interface set interface name=\"{0}\" admin=ENABLED", nameAndMac.Key));
                _executableProcessQueue.Go();
                wereMacsEnabled = true;
            }

            return wereMacsEnabled;
        }
    }
}