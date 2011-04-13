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

using Rackspace.Cloud.Server.Agent.UpdaterService.Commands;
using Rackspace.Cloud.Server.Common.Logging;
using StructureMap;

namespace Rackspace.Cloud.Server.Agent.UpdaterService {
    public static class IoC {
        public static void Register() {
            StructureMapConfiguration.BuildInstancesOf<ILogger>().TheDefaultIsConcreteType<Logger>();
            StructureMapConfiguration.BuildInstancesOf<IBackupAgent>().TheDefaultIsConcreteType<BackupAgent>();
            StructureMapConfiguration.BuildInstancesOf<IAgentDownload>().TheDefaultIsConcreteType<AgentDownload>();
            StructureMapConfiguration.BuildInstancesOf<ICheckSumCheck>().TheDefaultIsConcreteType<CheckSumCheck>();
            StructureMapConfiguration.BuildInstancesOf<IStopAgentService>().TheDefaultIsConcreteType<StopAgentService>();
            StructureMapConfiguration.BuildInstancesOf<IStartAgentService>().TheDefaultIsConcreteType<StartAgentService>();
            StructureMapConfiguration.BuildInstancesOf<IInstallAgentService>().TheDefaultIsConcreteType<InstallAgentService>();
            StructureMapConfiguration.BuildInstancesOf<IFinalize>().TheDefaultIsConcreteType<Finalize>();
        }
    }
}