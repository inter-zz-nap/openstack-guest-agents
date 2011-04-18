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
using Rackspace.Cloud.Server.Agent.Utilities;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent {
    public interface ICommandQueue {
        void Work();
    }

    public class CommandQueue : ICommandQueue {
        private readonly IXenStore _store;
        private readonly ICommandFactory _factory;
        private readonly ILogger _logger;

        public CommandQueue(IXenStore store, ICommandFactory factory, ILogger logger) {
            _store = store;
            _factory = factory;
            _logger = logger;
        }

        public void Work() {
            var commands = _store.GetCommands();
            if (commands.Count == 0) {
                LogManager.ShouldBeLogging = false;
                return;
            }

            LogManager.ShouldBeLogging = true;
            foreach (var command in commands) {
                ProcessCommand(command);
            }
        }

        private void ProcessCommand(Command command) {
            var removeMessageFromXenStore = true;

            try {
                var executableResult = _factory.CreateCommand(command.name).Execute(command.value);
                _store.Write(command.key, new Json<object>().Serialize(new { returncode = executableResult.ExitCode, message = executableResult.Output.Value() }));
            } catch (InvalidCommandException exception) {
                _store.Write(command.key, new Json<object>().Serialize(new { returncode = "1", message = exception.Message }));
            } catch (UnsuccessfulCommandExecutionException exception) {
                var result = (ExecutableResult) exception.Data["result"];
                var output = "";
                var error = "";
                if (result.Output != null && !string.IsNullOrEmpty(result.Output.Value()))
                    output = ", Output:" + result.Output.Value();
                if (result.Error != null && !string.IsNullOrEmpty(result.Error.Value()))
                    error = ", Error:" + result.Error.Value();
                _store.Write(command.key, new Json<object>().Serialize(new
                                                                           {
                                                                               returncode = result.ExitCode, 
                                                                               message = exception.Message + 
                                                                               output + error
                                                                           }));
            } catch(Exception ex) {
                removeMessageFromXenStore = false;
                _logger.Log(String.Format("Exception was : {0}\nStackTrace Was: {1}", ex.Message, ex.StackTrace));
            } finally {
                if (removeMessageFromXenStore) _store.Remove(command.key);
            }
        }
    }
}