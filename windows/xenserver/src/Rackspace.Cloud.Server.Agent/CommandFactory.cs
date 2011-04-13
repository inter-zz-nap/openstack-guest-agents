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

using System.Linq;
using System.Reflection;
using Rackspace.Cloud.Server.Agent.Interfaces;
using StructureMap;

namespace Rackspace.Cloud.Server.Agent {
    public class CommandFactory : ICommandFactory {
        public IExecutableCommand CreateCommand(string dataValue) {
            var key = dataValue.ToLower();
            var matchingCommand = Assembly.GetExecutingAssembly().GetTypes()
                .Where(x => x.Namespace == "Rackspace.Cloud.Server.Agent.Commands")
                .SingleOrDefault(x => x.Name.ToLower() == key);

            if (matchingCommand == null) throw new InvalidCommandException(dataValue);

            return ObjectFactory.GetNamedInstance<IExecutableCommand>(key);
        }
    }
}