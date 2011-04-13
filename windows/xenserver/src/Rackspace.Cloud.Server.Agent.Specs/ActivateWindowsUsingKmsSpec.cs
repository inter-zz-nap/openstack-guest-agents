using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs
{
    [TestFixture]
    public class ActivateWindowsUsingKmsSpec
    {
        private IExecutableProcessQueue exec;
        private IOperatingSystemChecker _operatingSystemChecker;

        [Test]
        public void should_run_vbs_licensing_script_with_kms_server_and_port_when_windows_2008()
        {
            exec = MockRepository.GenerateMock<IExecutableProcessQueue>();
            exec.Stub(x => x.Enqueue(Arg<string>.Is.Anything, Arg<string>.Is.Anything)).Return(exec);
            exec.Expect(x => x.Go()).Repeat.Once();
            _operatingSystemChecker = MockRepository.GenerateMock<IOperatingSystemChecker>();
            _operatingSystemChecker.Stub(x => x.IsWindows2008).Return(true);

            new ActivateWindowsUsingKms(exec, _operatingSystemChecker).Execute("server:port");

            exec.Replay();

            exec.AssertWasCalled(x => x.Enqueue("cscript", "c:\\windows\\system32\\slmgr.vbs /skms " + "server:port"));
            exec.AssertWasCalled(x => x.Enqueue("cscript", "c:\\windows\\system32\\slmgr.vbs /ato"));
        }

        [Test]
        public void should_not_run_vbs_script_when_windows_2003()
        {
            exec = MockRepository.GenerateMock<IExecutableProcessQueue>();
            exec.Expect(x => x.Enqueue(Arg<string>.Is.Anything, Arg<string>.Is.Anything)).Repeat.Never();
            exec.Expect(x => x.Go()).Repeat.Never();
            _operatingSystemChecker = MockRepository.GenerateMock<IOperatingSystemChecker>();
            _operatingSystemChecker.Stub(x => x.IsWindows2008).Return(false);

            new ActivateWindowsUsingKms(exec, _operatingSystemChecker).Execute("server:port");

            exec.AssertWasNotCalled(x => x.Enqueue("cscript", "c:\\windows\\system32\\slmgr.vbs /skms " + "server:port"));
            exec.AssertWasNotCalled(x => x.Enqueue("cscript", "c:\\windows\\system32\\slmgr.vbs /ato"));
        }

        [TearDown]
        public void Teardown()
        {
            exec.VerifyAllExpectations();
        }
        
    }
}