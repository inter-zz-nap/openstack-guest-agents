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
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Security;
using Rackspace.Cloud.Server.Agent.Utilities;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface ISetPassword {
        void Execute(string user, string encryptedPassword);
    }

    public class SetPassword : ISetPassword {
        private readonly IExecutableProcessQueue _executableProcessQueue;
        private readonly IDiffieHellmanPrerequisitesChecker _prerequisitesChecker;

        public SetPassword(IExecutableProcessQueue executableProcessQueue, IDiffieHellmanPrerequisitesChecker prerequisitesChecker) {
            _executableProcessQueue = executableProcessQueue;
            _prerequisitesChecker = prerequisitesChecker;
        }

        public void Execute(string user, string encryptedPassword) {
            if(!_prerequisitesChecker.ArePresent) throw new UnsuccessfulCommandExecutionException("Key init was not called prior to Set Password command", new ExecutableResult {ExitCode = "1"});

            var decryptionKey = Statics.DiffieHellman.DecryptKeyExchange(Statics.DiffieHellmanCollaboratorKey);

            var password = Encryption.Decrypt(Convert.FromBase64String(encryptedPassword), decryptionKey, new byte[0]);
            _executableProcessQueue.Enqueue("net", "user " + user + " " + password).Go();
            
            Statics.DiffieHellman = null;
            Statics.DiffieHellmanCollaboratorKey = null;
        }
    }
}