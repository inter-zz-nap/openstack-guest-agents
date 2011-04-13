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
using System.Text;
using Rackspace.Cloud.Server.Agent.Utilities;

namespace Rackspace.Cloud.Server.Agent.Configuration {
    [Serializable]
    public class ExecutableResult {
        public ExecutableResult() {
            ExitCode = "0";
            Error = new List<string>();
            Output = new List<string>();
        }

        public IEnumerable<string> Output { set; get; }
        public IList<string> Error { set; get; }
        public string ExitCode { set; get; }

        public override string ToString()
        {
            var stringBuilder = new StringBuilder();
            stringBuilder.AppendLine(String.Format("ExitCode={0}", ExitCode));
            stringBuilder.AppendLine(String.Format("Output={0}", Output.Value()));
            stringBuilder.Append(String.Format("Error={0}", Error.Value()));

            return stringBuilder.ToString();
        }
    }
}