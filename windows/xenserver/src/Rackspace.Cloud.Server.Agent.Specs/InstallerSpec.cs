using System.Collections.Generic;
using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs.InstallerSpec
{
    [TestFixture]
    public class when_installing_something
    {
        private ILogger logger;
        private IExecutableProcessQueue exec;
        private IInstaller installer;

        [SetUp]
        public void Setup()
        {
            logger = MockRepository.GenerateMock<ILogger>();
            exec = MockRepository.GenerateMock<IExecutableProcessQueue>();

            installer = new Installer(exec, logger);
        }

        [Test]
        public void should_execute_the_commands_passed_in()
        {
            logger.Stub(x => x.Log(Arg<string>.Is.Anything));
            exec.Expect(x => x.Enqueue(Arg<string>.Is.Anything, Arg<string>.Is.Anything))
                .Return(exec);
            exec.Expect(x => x.Go()).Repeat.Once();

            installer.Install(new Dictionary<string, string>
                                  {
                                      { Constants.XenToolsUnzipPath, "/S /norestart /D=" + Constants.XenToolsPath }
                                  });

            exec.AssertWasCalled(x => x.Enqueue(Constants.XenToolsUnzipPath, "/S /norestart /D=" + Constants.XenToolsPath));
        }
    }
}