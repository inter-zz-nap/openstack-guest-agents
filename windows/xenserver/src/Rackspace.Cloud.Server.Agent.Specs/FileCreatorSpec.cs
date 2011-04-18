using System;
using System.IO;
using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs.FileCreatorSpec
{
    [TestFixture]
    public class when_creating_file
    {
        private const string FILE_PATH = @"c:\userdata.txt";
        private const string FILE_CONTENT = @"RS_server=my.rightscale.com <http://my.rightscale.com/> |RS_api_url=https://my.rightscale.com/api/inst/instances/aa80a5a0e8cce93614247706a4c0fed8d4df5555|RS_sketchy=sketchy1-11.rightscale.com <http://sketchy1-11.rightscale.com/> |RS_token=41b19556f0efc07069dc9aee5b370255";
        private ILogger logger;
        private FileCreator fileCreator;
        private FileInfo fileInfo;
        private string testGuid;

        [SetUp]
        public void Setup()
        {
            testGuid = Guid.NewGuid().ToString();

            Cleanup();
            logger = MockRepository.GenerateMock<ILogger>();

            fileCreator = new FileCreator(logger);
            fileInfo = new FileInfo { Path = FILE_PATH, Content = FILE_CONTENT };

            Assert.That(File.Exists(FILE_PATH), Is.False);
            var files = Directory.GetFiles(Path.GetDirectoryName(FILE_PATH), Path.GetFileName(FILE_PATH) + ".bak.*");
            Assert.That(files.Length, Is.EqualTo(0));
        }

        private void Cleanup()
        {
            var files = Directory.GetFiles(Path.GetDirectoryName(FILE_PATH), Path.GetFileName(FILE_PATH) + ".bak.*");
            foreach (var file in files)
            {
                File.Delete(file);
            }

            if (Directory.Exists("C:\\"+testGuid))
                Directory.Delete("C:\\"+testGuid, true);

            if (File.Exists(FILE_PATH))
                File.Delete(FILE_PATH);
            
        }

        [TearDown]
        public void Teardown()
        {
            Cleanup();
        }

        [Test]
        public void should_not_throw_exception_when_folders_in_path_to_not_exist()
        {
            new FileCreator(logger).CreateFile(new FileInfo{Path = @"C:\" + testGuid + @"\" + testGuid + @"\test.txt", Content = "test"});    
        }

        [Test]
        [ExpectedException(typeof(Exception))]
        public void should_throw_exception_when_drive_does_not_exist()
        {
            new FileCreator(logger).CreateFile(new FileInfo{Path = @"V:\test.txt", Content = "test"});    
        }

        [Test]      
        public void should_create_file_with_specific_content()
        {
            fileCreator.CreateFile(fileInfo);

            Assert.That(File.Exists(FILE_PATH), Is.True);
            var files = Directory.GetFiles(Path.GetDirectoryName(FILE_PATH), Path.GetFileName(FILE_PATH) + ".bak.*");
            Assert.That(files.Length, Is.EqualTo(0));

            using(TextReader tr = new StreamReader(FILE_PATH))
            {
                var line = tr.ReadLine();
                Assert.That(line, Is.EqualTo(FILE_CONTENT));
            }
        }

        [Test] public void should_create_backup_file_if_file_already_exists()
        {
            fileCreator.CreateFile(fileInfo);
            fileCreator.CreateFile(fileInfo);

            Assert.That(File.Exists(FILE_PATH), Is.True);
            var files = Directory.GetFiles(Path.GetDirectoryName(FILE_PATH), Path.GetFileName(FILE_PATH) + ".bak.*");
            Assert.That(files.Length, Is.EqualTo(1));

            using (TextReader tr = new StreamReader(FILE_PATH))
            {
                var line = tr.ReadLine();
                Assert.That(line, Is.EqualTo(FILE_CONTENT));
            }

            using (TextReader tr = new StreamReader(files[0]))
            {
                var line = tr.ReadLine();
                Assert.That(line, Is.EqualTo(FILE_CONTENT));
            }
        }
    }
}
