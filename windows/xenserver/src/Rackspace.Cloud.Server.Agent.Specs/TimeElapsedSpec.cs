using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Utilities;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs
{
    [TestFixture]
    public class TimeElapsedSpec
    {

        [Test]
        public void should_disable_and_reenable_timer_when_polling_enabled()
        {

            ITimer timer = MockRepository.GenerateMock<ITimer>();
            timer.GetMockRepository().Ordered();
            ICommandQueue proc = MockRepository.GenerateStub<ICommandQueue>();

            Statics.ShouldPollXenStore = true;

            ServiceWork elapsed = new ServiceWork(timer, proc);
            elapsed.Do();
            timer.AssertWasCalled(x => x.Enabled = false);
            timer.AssertWasCalled(x => x.Enabled = true);
        }

        [Test]
        public void should_disable_and_not_reenable_timer_when_polling_disabled()
        {

            ITimer timer = MockRepository.GenerateMock<ITimer>();
            timer.GetMockRepository().Ordered();
            ICommandQueue proc = MockRepository.GenerateStub<ICommandQueue>();

            Statics.ShouldPollXenStore = false;

            ServiceWork elapsed = new ServiceWork(timer, proc);
            elapsed.Do();
            timer.AssertWasCalled(x => x.Enabled = false);
            timer.AssertWasNotCalled(x => x.Enabled = true);
        }
    }
}