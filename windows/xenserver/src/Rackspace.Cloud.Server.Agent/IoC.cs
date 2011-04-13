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
using Rackspace.Cloud.Server.Agent.Commands;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Utilities;
using Rackspace.Cloud.Server.Agent.WMI;
using Rackspace.Cloud.Server.Common.Logging;
using Rackspace.Cloud.Server.DiffieHellman;
using StructureMap;
using StructureMap.Configuration.DSL;

namespace Rackspace.Cloud.Server.Agent {
    public class IoC {
        public static void Register() {
            StructureMapConfiguration.BuildInstancesOf<ICommandQueue>().TheDefaultIsConcreteType<CommandQueue>();
            StructureMapConfiguration.BuildInstancesOf<ICommandFactory>().TheDefaultIsConcreteType<CommandFactory>();
            StructureMapConfiguration.BuildInstancesOf<IExecutableProcess>().TheDefaultIsConcreteType<ExecutableProcess>();
            StructureMapConfiguration.BuildInstancesOf<ILogger>().TheDefaultIsConcreteType<Logger>();
            StructureMapConfiguration.BuildInstancesOf<IExecutableProcessQueue>().TheDefaultIsConcreteType<ExecutableProcessQueue>();
            StructureMapConfiguration.BuildInstancesOf<IXenStore>().TheDefaultIsConcreteType<XenStore>();
            StructureMapConfiguration.BuildInstancesOf<IExecutableProcessCommandPatternSubsitution>().TheDefaultIsConcreteType<ExecutableProcessCommandPatternSubsitution>();
            StructureMapConfiguration.BuildInstancesOf<ISetNetworkInterface>().TheDefaultIsConcreteType<SetNetworkInterface>();
            StructureMapConfiguration.BuildInstancesOf<ISetPassword>().TheDefaultIsConcreteType<SetPassword>();
            StructureMapConfiguration.BuildInstancesOf<IWmiMacNetworkNameGetter>().TheDefaultIsConcreteType<WmiMacNetworkNameGetter>();
            StructureMapConfiguration.BuildInstancesOf<IXenNetworkInformation>().TheDefaultIsConcreteType<XenNetworkInformation>();
            StructureMapConfiguration.BuildInstancesOf<IAgentUpdateMessageSender>().TheDefaultIsConcreteType<AgentUpdateMessageSender>();
            StructureMapConfiguration.BuildInstancesOf<IDiffieHellmanPrerequisitesChecker>().TheDefaultIsConcreteType<DiffieHellmanPrerequisitesChecker>();
            StructureMapConfiguration.BuildInstancesOf<IOperatingSystemChecker>().TheDefaultIsConcreteType<OperatingSystemChecker>();
            StructureMapConfiguration.BuildInstancesOf<ISetNetworkRoutes>().TheDefaultIsConcreteType<SetNetworkRoutes>();
            StructureMapConfiguration.BuildInstancesOf<IRegistryReader>().TheDefaultIsConcreteType<RegistryReader>();
            StructureMapConfiguration.BuildInstancesOf<IAdministratorAccountNameFinder>().TheDefaultIsConcreteType<AdministratorAccountNameFinder>();
            StructureMapConfiguration.BuildInstancesOf<ISystemInformation>().TheDefaultIsConcreteType<SystemInformation>();
            
            //ACTIONS
            StructureMapConfiguration.BuildInstancesOf<IActivateWindowsUsingKms>().TheDefaultIsConcreteType<ActivateWindowsUsingKms>();
            StructureMapConfiguration.BuildInstancesOf<IAgentUpdateMessageHandler>().TheDefaultIsConcreteType<AgentUpdateMessageHandler>();
            StructureMapConfiguration.BuildInstancesOf<IChecksumValidator>().TheDefaultIsConcreteType<ChecksumValidator>();
            StructureMapConfiguration.BuildInstancesOf<IConnectionChecker>().TheDefaultIsConcreteType<ConnectionChecker>();
            StructureMapConfiguration.BuildInstancesOf<IDownloader>().TheDefaultIsConcreteType<Downloader>();
            StructureMapConfiguration.BuildInstancesOf<IFileCreator>().TheDefaultIsConcreteType<FileCreator>();
            StructureMapConfiguration.BuildInstancesOf<IFinalizer>().TheDefaultIsConcreteType<Finalizer>();
            StructureMapConfiguration.BuildInstancesOf<IInjectFileMessageHandler>().TheDefaultIsConcreteType<InjectFileMessageHandler>();
            StructureMapConfiguration.BuildInstancesOf<IInstaller>().TheDefaultIsConcreteType<Installer>();
            StructureMapConfiguration.BuildInstancesOf<ISetNetworkInterface>().TheDefaultIsConcreteType<SetNetworkInterface>();
            StructureMapConfiguration.BuildInstancesOf<ISetNetworkRoutes>().TheDefaultIsConcreteType<SetNetworkRoutes>();
            StructureMapConfiguration.BuildInstancesOf<ISetPassword>().TheDefaultIsConcreteType<SetPassword>();
            StructureMapConfiguration.BuildInstancesOf<ISleeper>().TheDefaultIsConcreteType<Sleeper>();
            StructureMapConfiguration.BuildInstancesOf<IServiceRestarter>().TheDefaultIsConcreteType<ServiceRestarter>();
            StructureMapConfiguration.BuildInstancesOf<IServiceStarter>().TheDefaultIsConcreteType<ServiceStarter>();
            StructureMapConfiguration.BuildInstancesOf<IServiceStopper>().TheDefaultIsConcreteType<ServiceStopper>();
            StructureMapConfiguration.BuildInstancesOf<IVersionChecker>().TheDefaultIsConcreteType<VersionChecker>();
            StructureMapConfiguration.BuildInstancesOf<IUnzipper>().TheDefaultIsConcreteType<Unzipper>();
            StructureMapConfiguration.BuildInstancesOf<IFileCopier>().TheDefaultIsConcreteType<FileCopier>();


            StructureMapConfiguration.BuildInstancesOf<IDiffieHellman>().TheDefaultIs(
                Registry.Instance<IDiffieHellman>().UsingConcreteType<DiffieHellmanManaged>()
                    .WithProperty("prime").EqualTo(Constants.DiffieHellmanPrime)
                    .WithProperty("generator").EqualTo(Constants.DiffieHellanGenerator)
                );

            StructureMapConfiguration.BuildInstancesOf<ServiceWork>().TheDefaultIsConcreteType<ServiceWork>();

            //COMMANDS
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<Version>().WithName(Utilities.Commands.version.ToString());
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<Password>().WithName(Utilities.Commands.password.ToString());
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<Ready>().WithName(Utilities.Commands.ready.ToString());
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<ResetNetwork>().WithName(Utilities.Commands.resetnetwork.ToString());
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<AgentUpdate>().WithName(Utilities.Commands.agentupdate.ToString());
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<XentoolsUpdate>().WithName(Utilities.Commands.xentoolsupdate.ToString());
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<KmsActivate>().WithName(Utilities.Commands.kmsactivate.ToString());
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<KeyInit>().WithName(Utilities.Commands.keyinit.ToString());
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<InjectFile>().WithName(Utilities.Commands.injectfile.ToString());
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<Features>().WithName(Utilities.Commands.features.ToString());
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<Unrescue>().WithName(Utilities.Commands.unrescue.ToString());
            StructureMapConfiguration.AddInstanceOf<IExecutableCommand>().UsingConcreteType<UpdaterUpdate>().WithName(Utilities.Commands.updaterupdate.ToString());
        }
    }
}
