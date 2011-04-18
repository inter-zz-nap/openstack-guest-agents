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
using System.Diagnostics;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Utilities;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent {
    public class ExecutableProcess : IExecutableProcess {
        private readonly ILogger _logger;
        private readonly IExecutableProcessCommandPatternSubsitution _executableProcessCommandPatternSubsitution;

        public ExecutableProcess(ILogger logger, IExecutableProcessCommandPatternSubsitution executableProcessCommandPatternSubsitution)
        {
            _logger = logger;
            _executableProcessCommandPatternSubsitution = executableProcessCommandPatternSubsitution;
        }

        private readonly IList<string> _errorData = new List<string>();

        public ExecutableResult Run(string fileName, string arguments) {
            var process = new Process
                              {
                                  StartInfo =
                                      {
                                          CreateNoWindow = true,
                                          UseShellExecute = false,
                                          RedirectStandardOutput = true,
                                          RedirectStandardError = true,
                                          FileName = fileName,
                                          Arguments = arguments
                                      }
                              };

            process.ErrorDataReceived += ProcessErrorDataReceived;
            process.Start();

            _logger.Log(("Processing Command: " + fileName + " " + arguments).DoCommandTextSubsitutions(_executableProcessCommandPatternSubsitution.GetSubsitutions()));

            process.BeginErrorReadLine();

            var executableResult = new ExecutableResult
                                       {
                                           Output = process.StandardOutput.ReadToEnd().SplitOnNewLine()
                                       };

            process.WaitForExit();

            executableResult.ExitCode = process.ExitCode.ToString();
            executableResult.Error = _errorData;

            _logger.Log("Command Result:\n" + executableResult);

            return executableResult;
        }

        private void ProcessErrorDataReceived(object sender, DataReceivedEventArgs e) {
            if (!String.IsNullOrEmpty(e.Data)) {
                _errorData.Add(e.Data);
            }
        }
    }
}
