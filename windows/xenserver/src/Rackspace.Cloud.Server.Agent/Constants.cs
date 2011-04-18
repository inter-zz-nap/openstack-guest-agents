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

using System.Text;
using Rackspace.Cloud.Server.Common.Configuration;

namespace Rackspace.Cloud.Server.Agent {
    public static class Constants {
        public const string XenToolsPath = @"C:\Program Files\Citrix\XenTools";
        public const string XenClientPath = XenToolsPath + @"\xenstore_client.exe";
        public const string KmsActivationVbsPath = @"c:\windows\system32\slmgr.vbs";

        public const string ReadOnlyDataConfigBase = "vm-data";
        public const string WritableDataHostBase = "data/host";
        public const string WritableDataGuestBase = "data/guest";
        public const string NetworkingBase = "networking";

        public const string SuccessfulKeyInit = "D0";

        public const string DiffieHellmanPrime = "162259276829213363391578010288127";
        public const string DiffieHellanGenerator = "5";

        public static string Combine(params string[] paths) {
            var stringBuilder = new StringBuilder();
            for (var i = 0; i < paths.Length; i++) {
                stringBuilder.Append(paths[i]);
                if (i != paths.Length - 1)
                    stringBuilder.Append("/");
            }

            return stringBuilder.ToString();
        }

        public static readonly string XenToolsReleasePackage = SvcConfiguration.AgentVersionUpdatesPath + "xensetup.exe.zip";
        public static readonly string XenToolsUnzipPath = SvcConfiguration.AgentVersionUpdatesPath + "xentools";
        public static readonly string XenToolsSetupExecutablePath = XenToolsUnzipPath + @"\xensetup.exe";

        public static readonly string UpdaterReleasePackage = SvcConfiguration.AgentVersionUpdatesPath + "UpdateService.zip";
        public static readonly string UpdaterUnzipPath = SvcConfiguration.AgentVersionUpdatesPath + "updater";
        public static readonly string UpdaterPath = @"C:\Program Files\Rackspace\Cloud Servers\AgentUpdater";
    }
}
