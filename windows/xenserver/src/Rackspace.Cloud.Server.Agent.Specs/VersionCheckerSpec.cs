using System;
using System.Text.RegularExpressions;
using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs.VersionCheckerSpec
{
    [TestFixture]
    public class when_checking_file_version
    {
        private ILogger logger;
        private VersionChecker versionChecker;

        [SetUp]
        public void Setup()
        {
            logger = MockRepository.GenerateMock<ILogger>();
            versionChecker = new VersionChecker(logger);
        }

        [Test]
        public void should_return_file_version()
        {
            var version = versionChecker.Check("C:\\Program Files\\Internet Explorer\\iexplore.exe");
            const string pattern = @"(\d+\.){3}\d+";
            Assert.That(Regex.Match(version, pattern).Success, Is.True);
        }

        [Test]
        public void should_throw_exception_when_file_not_found()
        {
            var version = versionChecker.Check("C:\\filethatdoesnotexist.txt");
            Assert.That(version, Is.EqualTo("File C:\\filethatdoesnotexist.txt not found"));
        }
    }
}