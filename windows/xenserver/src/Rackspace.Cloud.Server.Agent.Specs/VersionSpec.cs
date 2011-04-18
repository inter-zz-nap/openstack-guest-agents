using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Commands;
using Rackspace.Cloud.Server.Agent.Utilities;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs.VersionSpec
{
    [TestFixture]
    public class when_checking_the_version_of_the_agent
    {
        private IVersionChecker versionChecker;

        [Test]
        public void should_use_the_path_of_the_agent_dll()
        {
            versionChecker = MockRepository.GenerateMock<IVersionChecker>();
            versionChecker.Expect(x => x.Check(Version.AGENT_PATH)).Return("1.1.1.1");

            var version = new Version(versionChecker);
            var result = version.Execute(Version.AGENT);
            Assert.That(result.Output.Value(), Is.EqualTo("1.1.1.1\r\n"));
        }
    }

    [TestFixture]
    public class when_checking_the_version_of_xentools
    {
        private IVersionChecker versionChecker;

        [Test]
        public void should_use_the_path_of_the_agent_dll()
        {
            versionChecker = MockRepository.GenerateMock<IVersionChecker>();
            versionChecker.Expect(x => x.Check(Version.XENTOOLS_PATH)).Return("2.2.2.2");

            var version = new Version(versionChecker);
            var result = version.Execute(Version.XENTOOLS);
            Assert.That(result.Output.Value(), Is.EqualTo("2.2.2.2\r\n"));
        }
    }

    [TestFixture]
    public class when_checking_the_version_of_agent_updater
    {
        private IVersionChecker versionChecker;

        [Test]
        public void should_use_the_path_of_the_agent_dll()
        {
            versionChecker = MockRepository.GenerateMock<IVersionChecker>();
            versionChecker.Expect(x => x.Check(Version.AGENT_UPDATER_PATH)).Return("3.3.3.3");

            var version = new Version(versionChecker);
            var result = version.Execute(Version.AGENT_UPDATER);
            Assert.That(result.Output.Value(), Is.EqualTo("3.3.3.3\r\n"));
        }
    }
}