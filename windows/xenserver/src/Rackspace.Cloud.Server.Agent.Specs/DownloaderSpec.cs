using System;
using System.IO;
using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs.DownloaderSpec
{
    [TestFixture]
    public class when_finalizing_a_process
    {
        private ILogger logger;
        private IDownloader downloader;

        [SetUp]
        public void Setup()
        {
            logger = MockRepository.GenerateMock<ILogger>();
            downloader = new Downloader(logger);
        }

        [Test]
        public void should_download_file()
        {

        }
    }
}