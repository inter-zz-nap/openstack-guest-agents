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

using System.Text.RegularExpressions;
using Rackspace.Cloud.Server.Common.AgentUpdate;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IAgentUpdateMessageHandler
    {
        AgentUpdateInfo Handle(string message);
    }

    public class AgentUpdateMessageHandler : IAgentUpdateMessageHandler {

        public AgentUpdateInfo Handle(string message)
        {
            if (!IsValid(message))
            {
                throw new InvalidCommandException(
                    string.Format(
                        "Update message: {0}, is incorrect format.  Need 'http://tempuri/file.zip,md5valueOfzipfile'",
                        message));    
            }
            var info = message.Split(new[] { ',' });
            return new AgentUpdateInfo { url = info[0], signature = info[1] };
        }

        private bool IsValid(string message)
        {
            const string pattern = @"^http:\/\/(.*),[a-zA-Z0-9]+$";
            return Regex.IsMatch(message, pattern);
        }
    }
}