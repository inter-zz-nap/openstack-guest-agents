using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs.ChecksumValidatorSpec
{
    [TestFixture]
    public class when_finalizing_a_process
    {
        private ILogger logger;
        private IChecksumValidator checksumValidator;

        [SetUp]
        public void Setup()
        {
            logger = MockRepository.GenerateMock<ILogger>();
            checksumValidator = new ChecksumValidator(logger);
        }

        [Test]
        public void should_validate_checksum()
        {

        }
    }
}