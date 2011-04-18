using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Utilities;

namespace Rackspace.Cloud.Server.Agent.Specs {
    [TestFixture]
    public class ExtensionsSpec {
        [Test]
        public void should_return_valid_guids_when_calling_the_extension_method_and_checks_for_Value_extension_method() {
            IList<string> guids = new List<string> {"A"};
            var guid1 = Guid.NewGuid().ToString();
            guids.Add(guid1);
            guids.Add("Hello this is not a GUID, duh!");
            var guid2 = Guid.NewGuid().ToString();
            guids.Add(guid2);
            guids.Add("C");

            var validGuids = guids.ValidateAndClean();

            Assert.AreEqual(2, validGuids.ToArray().Count());
            Assert.AreEqual(guid1 + "\r\n" + guid2 + "\r\n", validGuids.Value());
        }

        [Test]
        public void temp()
        {
            IList<string> guids = new List<string> {"00ACDDF1-C646-4BE8-B3EA-9CD3C265B52E"};

            var validGuids = guids.ValidateAndClean();

            Assert.AreEqual(1, validGuids.ToArray().Count());
        }

        [Test]
        public void should_subsitutite_values_correctly_according_to_search_string_for_user_with_administrator_username()
        {
            var subsitutions = new ExecutableProcessCommandPatternSubsitution().GetSubsitutions();

            var string1 = "net user administrator password";
            
            Assert.AreEqual("net user administrator *****", string1.DoCommandTextSubsitutions(subsitutions));

            string1 = "some string that should be kept intact";
            Assert.AreEqual(string1, string1.DoCommandTextSubsitutions(subsitutions));
        }

        [Test]
        public void should_subsitutite_values_correctly_according_to_search_string_for_user_with_renamed_administrator_username() {
            var subsitutions = new ExecutableProcessCommandPatternSubsitution().GetSubsitutions();

            var string1 = "net user Admin-12345 password";

            Assert.AreEqual("net user Admin-12345 *****", string1.DoCommandTextSubsitutions(subsitutions));

            string1 = "some string that should be kept intact";
            Assert.AreEqual(string1, string1.DoCommandTextSubsitutions(subsitutions));
        }

        [Test]
        public void should_format_executable_result_correctly_when_tostring_gets_called()
        {
            var result = new ExecutableResult
                             {
                                 ExitCode = "1",
                                 Output = "Command Executed Successfully\nPlease consult your administrator".SplitOnNewLine(),
                                 Error = "Stuff happened, do something\nwell what!".SplitOnNewLine().ToList()
                             };

            Assert.AreEqual("ExitCode=1\r\nOutput=Command Executed Successfully\r\nPlease consult your administrator\r\n\r\nError=Stuff happened, do something\r\nwell what!\r\n", result.ToString());
        }

        [Test]
        public void should_convert_string_to_hex_string() {
            Assert.AreEqual("66-61-6B-65-70-61-73-73", "fakepass".ToHexString());
        }

        [Test]
        public void should_consider_single_slash_path_as_valid()
        {
            Assert.That(@"C:\testinjectionfile.txt".IsValidFilePath(), Is.True);
            Assert.That(@"C:\\testinjectionfile.txt".IsValidFilePath(), Is.True);
            Assert.That(@"C:\testinjectionfile.txt.".IsValidFilePath(), Is.False);
            Assert.That(@"C:\testinjectionfile.txt.".IsValidFilePath(), Is.False);
        }
    }
}
