using System;
using System.Collections.Generic;
using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Utilities;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs
{
    [TestFixture]
    public class SystemInformationSpec
    {
        private SystemInformation systemInformation;
        private IExecutableProcess execProcess;
        private ILogger logger;
        private string input;

        [SetUp]
        public void Setup()
        {
            execProcess = MockRepository.GenerateMock<IExecutableProcess>();
            logger = MockRepository.GenerateMock<ILogger>();
            logger.Stub(x => x.Log(Arg<string>.Is.Anything));

            systemInformation = new SystemInformation(execProcess, logger);

            input = new String('x', 200) + @"Windows Boot Loader\n\n\n\n"
                        + new String('y', 200) + " {my unique identifier} "
                        + new string('z', 302);
        }

        [Test]
        public void should_not_include_c_drive_in_bcd_store_drive_search()
        {
            systemInformation.LogicalDrives = new List<string> {@"C:\", @"D:\", @"E:\"};
            Assert.That(systemInformation.GetLogicalDrives().Contains(@"C:\"), Is.False);
        }

        [Test]
        public void should_get_the_unique_identifier_of_the_windows_boot_loader()
        {
            Assert.That(systemInformation.getWindowsBootLoaderUniqueIdentifer(input), Is.EqualTo("{my unique identifier}"));
        }

        [Test]
        public void should_give_bcd_store_drive_and_unique_identifier()
        {
            systemInformation.LogicalDrives = new List<string> {@"E:\", @"F:\"};
            execProcess.Stub(x => x.Run("bcdedit", @"/store E:\boot\bcd"))
                .Return(new ExecutableResult 
                {Output = new List<string> {"These are not the droids you are looking for"}});
            execProcess.Stub(x => x.Run("bcdedit", @"/store F:\boot\bcd"))
                .Return(new ExecutableResult 
                { Output = new List<string> { input } });
            var result = systemInformation
                .getDriveWithBootConfigurationDataStore();
            Assert.That(result[SystemInformation.DRIVE_KEY], Is.EqualTo(@"F:\"));
            Assert.That(result[SystemInformation.UNIQUE_IDENTIFIER_KEY], 
                Is.EqualTo("{my unique identifier}"));
        }

        [Test]
        public void should_list_another_bcd_store_drive_besides_the_c_drive()
        {
            systemInformation.LogicalDrives = new List<string> { @"C:\", @"D:\" };
            execProcess.Stub(x => x.Run("bcdedit", @"/store C:\boot\bcd"))
                .Return(new ExecutableResult { Output = new List<string> { input } });
            execProcess.Stub(x => x.Run("bcdedit", @"/store D:\boot\bcd"))
                .Return(new ExecutableResult { Output = new List<string> { input } });
            var result = systemInformation
                .getDriveWithBootConfigurationDataStore();
            Assert.That(result[SystemInformation.DRIVE_KEY], Is.EqualTo(@"D:\"));
            Assert.That(result[SystemInformation.UNIQUE_IDENTIFIER_KEY],
                Is.EqualTo("{my unique identifier}"));
        }

        [Test]
        [ExpectedException(typeof(UnsuccessfulCommandExecutionException))]
        public void should_throw_exception_if_no_bcd_data_store_drive_found()
        {
            systemInformation.LogicalDrives = new List<string> { @"E:\", @"F:\" };
            execProcess.Stub(x => x.Run("bcdedit", @"/store E:\boot\bcd"))
                .Return(new ExecutableResult { Output = new List<string> 
                { "These are not the droids you are looking for" } });
            execProcess.Stub(x => x.Run("bcdedit", @"/store F:\boot\bcd"))
                .Return(new ExecutableResult { Output = new List<string> 
                { "I told you, these are not the droids you are looking for" } });
            systemInformation.getDriveWithBootConfigurationDataStore();
        }

        [Test]
        [ExpectedException(typeof(UnsuccessfulCommandExecutionException))]
        public void should_throw_exception_if_bcd_data_store_output_does_not_have_boot_loader_info()
        {
            systemInformation.getWindowsBootLoaderUniqueIdentifer("HI");
        }

        [Test]
        [ExpectedException(typeof(UnsuccessfulCommandExecutionException))]
        public void should_throw_exception_if_bcd_data_store_output_does_not_have_boot_loader_text()
        {
            systemInformation.getWindowsBootLoaderUniqueIdentifer("{hi}");
        }

        [Test]
        [ExpectedException(typeof(UnsuccessfulCommandExecutionException))]
        public void should_throw_exception_if_bcd_data_store_output_does_not_have_at_least_one_left_curly_brace()
        {
            systemInformation.getWindowsBootLoaderUniqueIdentifer("Windows Boot Loader hi}");
        }

        [Test]
        [ExpectedException(typeof(UnsuccessfulCommandExecutionException))]
        public void should_throw_exception_if_bcd_data_store_output_does_not_have_at_least_one_right_curly_brace()
        {
            systemInformation.getWindowsBootLoaderUniqueIdentifer("Windows Boot Loader {hi");
        }
    }
}