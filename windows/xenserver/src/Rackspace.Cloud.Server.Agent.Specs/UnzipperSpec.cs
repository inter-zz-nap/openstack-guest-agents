using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs.UnzipperSpec
{
    [TestFixture]
    public class when_unzipping_a_download
    {
        private ILogger logger;
        private IUnzipper unzipper;

//        [Test]
//        public void should_unzip_successfully()
//        {
//            logger = MockRepository.GenerateMock<ILogger>();
//            unzipper = new Unzipper(logger);
//
//            logger.Stub(x => x.Log(Arg<string>.Is.Anything));
//
//        }
    }
}