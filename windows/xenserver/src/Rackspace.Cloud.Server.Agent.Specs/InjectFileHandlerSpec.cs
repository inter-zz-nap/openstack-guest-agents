using System;
using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Actions;

namespace Rackspace.Cloud.Server.Agent.Specs.InjectFileHandlerSpec
{
    [TestFixture]
    public class when_handling_inject_file_message
    {
        private InjectFileMessageHandler injectFileHandler;

        [SetUp]
        public void Setup()
        {
            injectFileHandler = new InjectFileMessageHandler();
        }

        [Test]
        public void should_validate_if_message_is_in_correct_format()
        {
            var injectFileInfo = injectFileHandler.Handle("QzpcdGVzdGZpbGUudHh0LEhlbGxvIFdvcmxk");
            Assert.That(injectFileInfo.Path, Is.EqualTo(@"C:\testfile.txt"));
            Assert.That(injectFileInfo.Content, Is.EqualTo("Hello World"));
        }

        [Test]
        public void should_validate_if_message_is_in_correct_format_capitalized()
        {
            var injectFileInfo = injectFileHandler.Handle("QzpcdGVzdGZpbGUudHh0LEhlbGxvIFdvcmxk");
            Assert.That(injectFileInfo.Path, Is.EqualTo(@"C:\testfile.txt"));
            Assert.That(injectFileInfo.Content, Is.EqualTo("Hello World"));
        }

        [Test]
        [ExpectedException(typeof(InvalidCommandException))]
        public void should_invalidate_if_message_is_not_in_correct_format()
        {
            injectFileHandler.Handle("jibberish");
        }
    }
}