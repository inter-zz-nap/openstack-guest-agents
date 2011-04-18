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
using System.Linq;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent {
    public class ExecutableProcessQueue : IExecutableProcessQueue {

        private readonly ILogger _logger;
        private readonly IExecutableProcessCommandPatternSubsitution _commandPatternCommandPatternSubsitution;
        private readonly Queue<ExecutableOperation> _processQueue = new Queue<ExecutableOperation>();

        public ExecutableProcessQueue(ILogger logger, IExecutableProcessCommandPatternSubsitution commandPatternCommandPatternSubsitution)
        {
            _logger = logger;
            _commandPatternCommandPatternSubsitution = commandPatternCommandPatternSubsitution;
        }

        public IExecutableProcessQueue Enqueue(string command, string arguments, string[] acceptableExitCodes)
        {
            _processQueue.Enqueue(new ExecutableOperation { Command = command, Arguments = arguments, AcceptableReturnCodes = acceptableExitCodes});
            return this;
        }

        public IExecutableProcessQueue Enqueue(string command, string arguments, bool conditionalToPass)
        {
            return conditionalToPass ? Enqueue(command, arguments) : this;
        }

        public IExecutableProcessQueue Enqueue(string command, string arguments) {
            return Enqueue(command, arguments, new[] {"0"});
        }

        public void Go() {
            while (_processQueue.Count > 0) {
                var operation = _processQueue.Dequeue();
                var executableResult = new ExecutableProcess(_logger, _commandPatternCommandPatternSubsitution).Run(operation.Command, operation.Arguments);

                if (!operation.AcceptableReturnCodes.ToList().Contains(executableResult.ExitCode)) {
                    throw new UnsuccessfulCommandExecutionException("Command Failed. ", executableResult);
                }
            }
        }
    }

    public class ExecutableOperation
    {
        public string Command { get; set; }
        public string Arguments { get; set; }
        public string[] AcceptableReturnCodes { get; set; }
    }
}
