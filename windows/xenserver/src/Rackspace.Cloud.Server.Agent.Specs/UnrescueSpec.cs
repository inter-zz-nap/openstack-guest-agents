using System.Collections.Generic;
using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Commands;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Utilities;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs
{
    [TestFixture]
    public class UnrescueSpec
    {
        private IExecutableProcessQueue _exec;
        private IOperatingSystemChecker _operatingSystemChecker;
        private ISystemInformation _systemInformation;

        [SetUp]
        public void Setup()
        {
            _exec = MockRepository.GenerateMock<IExecutableProcessQueue>();
            _operatingSystemChecker = MockRepository.GenerateMock<IOperatingSystemChecker>();
            _systemInformation = MockRepository.GenerateMock<ISystemInformation>();
        }

        [Test]
        public void should_run_bcd_edit_scripts_excluding_ntldr_call_when_windows_2008_r2()
        {

            var bcdDataStore = new Dictionary<string, string>
                                   {
                                       {SystemInformation.DRIVE_KEY, @"F:\"}, 
                                       {SystemInformation.UNIQUE_IDENTIFIER_KEY, 
                                           "{my unique identifier}"}
                                   };

            _exec.Stub(x => x.Enqueue(Arg<string>.Is.Anything, Arg<string>.Is.Anything)).Return(_exec);
            _exec.Stub(x => x.Enqueue(Arg<string>.Is.Anything, Arg<string>.Is.Anything, Arg<bool>.Is.Anything)).Return(_exec);
            _exec.Expect(x => x.Go()).Repeat.Once();
            _operatingSystemChecker.Stub(x => x.IsWindows2008).Return(true);
            _systemInformation.Stub(x => x.getDriveWithBootConfigurationDataStore())
                .Return(bcdDataStore);
            _systemInformation.Stub(x => x.getDriveLetterWithOriginalWindowsFolder()).Return("E:");
            

            new Unrescue(_exec, _operatingSystemChecker, _systemInformation).Execute(null);

            _exec.Replay();

            _exec.AssertWasCalled(x => x.Enqueue("bcdedit", @"/store F:\boot\bcd /set {my unique identifier} osdevice partition=E:"));
            _exec.AssertWasCalled(x => x.Enqueue("bcdedit", @"/store F:\boot\bcd /set {my unique identifier} device partition=E:"));
            _exec.AssertWasCalled(x => x.Enqueue("bcdedit", @"/store F:\boot\bcd /set {bootmgr} device partition=E:"));
            _exec.AssertWasCalled(x => x.Enqueue("bcdedit", @"/store F:\boot\bcd /set {memdiag} device partition=E:"));
            _exec.AssertWasCalled(x => x.Enqueue("bcdedit", @"/store F:\boot\bcd /set {ntldr} device partition=E:", false));
            _exec.AssertWasCalled(x => x.Go());
        }

        [Test]
        public void should_run_bcd_edit_scripts_including_ntldr_call_when_windows_2008_but_not_r2()
        {

            var bcdDataStore = new Dictionary<string, string>
                                   {
                                       {SystemInformation.DRIVE_KEY, @"F:\"}, 
                                       {SystemInformation.UNIQUE_IDENTIFIER_KEY, 
                                           "{my unique identifier}"}
                                   };

            _exec.Stub(x => x.Enqueue(Arg<string>.Is.Anything, Arg<string>.Is.Anything)).Return(_exec);
            _exec.Stub(x => x.Enqueue(Arg<string>.Is.Anything, Arg<string>.Is.Anything, Arg<bool>.Is.Anything)).Return(_exec);
            _exec.Expect(x => x.Go()).Repeat.Once();
            _operatingSystemChecker.Stub(x => x.IsWindows2008).Return(true);
            _operatingSystemChecker.Stub(x => x.IsWindows2008SP2).Return(true);
            _systemInformation.Stub(x => x.getDriveWithBootConfigurationDataStore())
                .Return(bcdDataStore);
            _systemInformation.Stub(x => x.getDriveLetterWithOriginalWindowsFolder()).Return("E:");


            new Unrescue(_exec, _operatingSystemChecker, _systemInformation).Execute(null);

            _exec.Replay();

            _exec.AssertWasCalled(x => x.Enqueue("bcdedit", @"/store F:\boot\bcd /set {my unique identifier} osdevice partition=E:"));
            _exec.AssertWasCalled(x => x.Enqueue("bcdedit", @"/store F:\boot\bcd /set {my unique identifier} device partition=E:"));
            _exec.AssertWasCalled(x => x.Enqueue("bcdedit", @"/store F:\boot\bcd /set {bootmgr} device partition=E:"));
            _exec.AssertWasCalled(x => x.Enqueue("bcdedit", @"/store F:\boot\bcd /set {memdiag} device partition=E:"));
            _exec.AssertWasCalled(x => x.Enqueue("bcdedit", @"/store F:\boot\bcd /set {ntldr} device partition=E:", true));
            _exec.AssertWasCalled(x => x.Go());
        }

        [Test]
        public void should_not_run_when_windows_2003()
        {
            _operatingSystemChecker.Stub(x => x.IsWindows2008).Return(false);

            _exec.AssertWasNotCalled(x => x.Enqueue(Arg<string>.Is.Anything, Arg<string>.Is.Anything));
            _exec.AssertWasNotCalled(x => x.Go());
        }

        [TearDown]
        public void Teardown()
        {
            _exec.VerifyAllExpectations();
        }

    }
}