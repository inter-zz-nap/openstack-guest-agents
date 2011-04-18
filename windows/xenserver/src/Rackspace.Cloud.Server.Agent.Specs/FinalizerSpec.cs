using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs.FinalizerSpec
{
    //Unit tests shouldn't hit the file system....
    //YADDA YADDA

    [TestFixture]
    public class when_finalizing_a_process
    {
        private ILogger logger;
        private IFinalizer finalizer;

        [SetUp]
        public void Setup()
        {
            logger = MockRepository.GenerateMock<ILogger>();
            finalizer = new Finalizer(logger);

            logger.Stub(x => x.Log(Arg<string>.Is.Anything));

            CreateFile("test.txt");
            Directory.CreateDirectory("test_directory");
            for (var i = 10; i < 10; i++)
            {
                CreateFile("test_directory\\test" + i + ".txt");
            }
        }

        [Test]
        public void should_delete_temp_file_and_folders()
        {
            finalizer.Finalize(new List<string>{"test.txt", "test_directory"});
            Assert.That(File.Exists("test.txt"), Is.False);
            Assert.That(Directory.Exists("test_directory"), Is.False);
            Assert.That(File.Exists("test_directory\\test4.txt"), Is.False);
        }

        private void CreateFile(string path)
        {
            using (var fs = File.Create(path, 1024))
            {
                var info = new UTF8Encoding(true).GetBytes("This is some text in the file.");
                // Add some information to the file.
                fs.Write(info, 0, info.Length);
            }
        }
    }
}