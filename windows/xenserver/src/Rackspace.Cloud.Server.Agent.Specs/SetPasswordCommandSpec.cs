using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Utilities;
using Rackspace.Cloud.Server.DiffieHellman;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs
{
    [TestFixture]
    public class SetPasswordCommandSpec
    {
        private IExecutableProcessQueue exec;
        private IDiffieHellmanPrerequisitesChecker _checker;
        [SetUp]
        public void Setup() {
            exec = MockRepository.GenerateMock<IExecutableProcessQueue>();
            exec.Stub(x => x.Enqueue(Arg<string>.Is.Anything, Arg<string>.Is.Anything)).Return(exec);
            _checker = MockRepository.GenerateMock<IDiffieHellmanPrerequisitesChecker>();    
        }

        [Test]
        public void should_execute_set_password_when_diffiehellman_statics_set()
        {
            exec.Expect(x => x.Go()).Repeat.Once();

            var diffieHellman = MockRepository.GenerateMock<IDiffieHellman>();
            diffieHellman.Stub(x => x.DecryptKeyExchange("8")).Return("secret");

            Statics.DiffieHellmanCollaboratorKey = "8";
            Statics.DiffieHellman = diffieHellman;

            const string encryptedPassword = "OTfAog/nwyzIcYOhvCBL0w==";

            new SetPassword(exec, new DiffieHellmanPrerequisitesChecker()).Execute("administrator", encryptedPassword);

            exec.Replay();

            exec.AssertWasCalled(x=>x.Enqueue("net", "user administrator rackspace"));
        }

        [Test]
        [ExpectedException(typeof(UnsuccessfulCommandExecutionException))]
        public void should_not_execute_set_password_when_diffiehellman_statics_not_set()
        {
            _checker.Stub(x => x.ArePresent).Return(false);
            new SetPassword(exec, _checker).Execute("administrator", "fakepass");
        }

        [TearDown]
        public void Teardown()
        {
            exec.VerifyAllExpectations();
        }
        
    }
}