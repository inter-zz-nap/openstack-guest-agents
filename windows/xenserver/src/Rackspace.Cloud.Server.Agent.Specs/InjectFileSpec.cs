using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Commands;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs.InjectFileSpec
{
    [TestFixture]
    public class when_injecting_file_into_guest
    {
        private ILogger logger;
        private IFileCreator fileCreator;
        private InjectFile _injectFile;
        private IInjectFileMessageHandler injectFileMessageHandler;

        [SetUp]
        public void Setup()
        {
            fileCreator = MockRepository.GenerateMock<IFileCreator>();
            logger = MockRepository.GenerateMock<ILogger>();
            injectFileMessageHandler = MockRepository.GenerateMock<IInjectFileMessageHandler>();

            _injectFile = new InjectFile(injectFileMessageHandler, fileCreator, logger);
        }

        [Test]
        public void should_create_file_and_copy_to_location_designated_by_user()
        {
            var fileInfo = new FileInfo{Path = "C:\testfile.txt", Content = "Hello world"};
            injectFileMessageHandler.Expect(x => x.Handle(Arg<string>.Is.Anything)).Return(fileInfo);
            fileCreator.Expect(x => x.CreateFile(fileInfo));
            _injectFile.Execute("{\"file_path\":\"C:\testfile.txt\",\"file_content\":\"Hello World\"}");
        }
        
    }
}