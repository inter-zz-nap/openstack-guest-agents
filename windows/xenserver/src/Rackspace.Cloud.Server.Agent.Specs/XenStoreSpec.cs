using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs {
    [TestFixture]
    public class XenStoreSpec {

        private IXenStore xenStore;
        private IExecutableProcess executable;

        [SetUp]
        public void Setup()
        {
            executable = MockRepository.GenerateMock<IExecutableProcess>();
            xenStore = new XenStore(executable);
        }

        [Test]
        public void should_call_executable_implementation_with_the_right_parameters_when_writing_to_xenstore()
        {
            
            xenStore.Write("name1", "value1");

            executable.AssertWasCalled(x => x.Run(Constants.XenClientPath, "write data/guest/name1 value1"));
        }
    }
}
