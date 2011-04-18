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
using Rackspace.Cloud.Server.Agent.Utilities;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IInjectFileMessageHandler
    {
        FileInfo Handle(string message);
    }

    public class InjectFileMessageHandler : IInjectFileMessageHandler
    {
        private FileInfo _fileInfo;

        public FileInfo Handle(string message)
        {
            var decodedMessage = "";
            try
            {
                @decodedMessage = System.Text.Encoding.ASCII.GetString(Convert.FromBase64String(message));
            }
            catch
            {
                ThrowErrorMessage("");
            }

            if (!IsValid(@decodedMessage)) ThrowErrorMessage(@decodedMessage);

            try
            {

		var splitPoint = @decodedMessage.IndexOf(',');

		var @path = @decodedMessage.Substring(0, splitPoint);
		var content = @decodedMessage.Substring(splitPoint+1);

                if (!@path.IsValidFilePath()) ThrowErrorMessage(@decodedMessage);
                _fileInfo = new FileInfo { Path = @path, Content = content };
            }
            catch
            {
                ThrowErrorMessage(@message);
            }

            return _fileInfo;
        }

        private void ThrowErrorMessage(string @message)
        {
            throw new InvalidCommandException(
                    "File inject message: " + @message + 
                    " is incorrect format. Needs to be something like " +
                    @"C:\somefile.txt,my file content");
        }

        private bool IsValid(string @message)
        {
            return @message.IndexOf(",") > 0;
        }
    }
}
