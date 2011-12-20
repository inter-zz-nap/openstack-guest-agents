using System;
using System.Collections.Generic;
using System.Linq;
using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.WMI;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs {
    public class SetNetworkInterfaceSpecBase {
        protected NetworkInterface NetworkInterface;
        protected SetNetworkInterface SetNetworkInterface;
        protected IExecutableProcessQueue ExecutableProcessQueue;
        protected IWmiMacNetworkNameGetter WmiMacNetworkNameGetter;
        protected ILogger Logger;

        internal void Setup(string macAddress) {
            Setup(macAddress, false);
        }

        internal void Setup(string macAddress, bool multipleIps) {
            Setup(macAddress, multipleIps, false, false);
        }

        internal void Setup(string macAddress, bool multipleIps, bool oneDisabledIp, bool noDns) {
            Logger = MockRepository.GenerateMock<ILogger>();

            ExecutableProcessQueue = MockRepository.GenerateMock<IExecutableProcessQueue>();
            ExecutableProcessQueue.Stub(x => x.Enqueue(Arg<string>.Is.Anything, Arg<string>.Is.Anything)).Return(
                ExecutableProcessQueue);

            WmiMacNetworkNameGetter = MockRepository.GenerateMock<IWmiMacNetworkNameGetter>();

            WmiMacNetworkNameGetter.Stub(x => x.Get()).Return(new Dictionary<string, string>
                                                                  {{"Lan1", "FAKEMAC"}, {"Lan2", ""}}).Repeat.Once();
            WmiMacNetworkNameGetter.Stub(x => x.Get()).Return(new Dictionary<string, string>
                                                                  {{"Lan1", "FAKEMAC"}, {"Lan2", "FAKEMAC2"}});

            NetworkInterface = multipleIps
                                   ? GetMeANetworkInterfaceWithAPrimaryAndSecondaryIp(macAddress)
                                   : GetMeANetworkInterface(macAddress);

            if (noDns) NetworkInterface.dns = null;
            if (oneDisabledIp) NetworkInterface.ips[1].enabled = "0";

            new MockRepository().Ordered();
            ExecutableProcessQueue.Replay();
        }

        internal void SetupRoutesOnInterface(NetworkRoute[] routes)
        {
            NetworkInterface.routes = routes;
        }

        private NetworkInterface GetMeANetworkInterfaceWithAPrimaryAndSecondaryIp(string macAddress) {
            var networkInterface = GetMeANetworkInterface(macAddress);

            var ipList = networkInterface.ips.ToList();
            ipList.Add(new IpTuple {ip = "1.2.2.2", netmask = "255.255.0.0"});

            networkInterface.ips = ipList.ToArray();
            return networkInterface;
        }

        private NetworkInterface GetMeANetworkInterface(string macAddress) {
            return new NetworkInterface
                       {
                           ips = new[] {new IpTuple {ip = "192.168.1.110", netmask = "255.255.255.0"}},
                           dns = new[] {"192.168.1.3", "192.168.1.4"},
                           label = "Front End",
                           gateway = "192.168.1.1",
                           mac = macAddress
                       };
        }
    }

    [TestFixture]
    public class SetNetworkInterfaceSpec_When_It_Goes_The_Happy_Path : SetNetworkInterfaceSpecBase {
        [SetUp]
        public void Setup() {
            Setup("fakemac");
            ExecutableProcessQueue.Expect(x => x.Go()).Repeat.Twice();

            SetNetworkInterface = new SetNetworkInterface(ExecutableProcessQueue, WmiMacNetworkNameGetter, Logger);
            SetNetworkInterface.Execute(new List<NetworkInterface>{NetworkInterface});
        }

        [Test]
        public void should_call_enable_on_disabled_interfaces_whose_macs_are_absent() {
            ExecutableProcessQueue.AssertWasCalled(
                x => x.Enqueue("netsh", "interface set interface name=\"Lan2\" admin=ENABLED"));
//            ExecutableProcessQueue.AssertWasCalled(x => x.Go());
        }

        [Test]
        public void should_set_the_interface_for_dhcp_first_before_configuring_it() {
            ExecutableProcessQueue.AssertWasCalled(
                x => x.Enqueue("netsh", "interface ip set address name=\"Lan1\" source=dhcp", new[] {"0", "1"}));
        }

        [Test]
        public void should_configure_the_interface_correctly_with_the_gateway() {
            ExecutableProcessQueue.AssertWasCalled(
                x =>
                x.Enqueue("netsh",
                          "interface ip add address name=\"Lan1\" addr=192.168.1.110 mask=255.255.255.0 gateway=192.168.1.1 gwmetric=2"));
        }

        [Test]
        public void should_configure_interface_with_the_dns_servers_as_dhcp() {
            ExecutableProcessQueue.AssertWasCalled(
                x => x.Enqueue("netsh", "interface ip set dns name=\"Lan1\" source=dhcp", new[] {"0", "1"}));
        }

        [Test]
        public void should_configure_interface_with_all_the_present_dns_servers() {
            ExecutableProcessQueue.AssertWasCalled(
                x => x.Enqueue("netsh", "interface ip add dns name=\"Lan1\" addr=192.168.1.3 index=1"));
            ExecutableProcessQueue.AssertWasCalled(
                x => x.Enqueue("netsh", "interface ip add dns name=\"Lan1\" addr=192.168.1.4 index=2"));
        }

        [Test]
        public void should_set_interface_name() {
            ExecutableProcessQueue.AssertWasCalled(
                x => x.Enqueue("netsh", "interface set interface name=\"Lan1\" newname=\"Front End\""));
        }

        [TearDown]
        public void Teardown() {
            ExecutableProcessQueue.VerifyAllExpectations();
        }
    }

    [TestFixture]
    public class SetNetworkInterfaceSpec_When_The_Label_Is_The_same_As_the_old_one : SetNetworkInterfaceSpecBase {
        [SetUp]
        public void Setup() {
            Setup("fakemac");
            ExecutableProcessQueue.Expect(x => x.Go()).Repeat.Once();

            SetNetworkInterface = new SetNetworkInterface(ExecutableProcessQueue, WmiMacNetworkNameGetter, Logger);
        }

        [Test]
        public void should_not_set_the_same_label_again() {
            NetworkInterface.label = "Lan1";
            SetNetworkInterface.Execute(new List<NetworkInterface> { NetworkInterface });

            ExecutableProcessQueue.AssertWasNotCalled(x => x.Enqueue("netsh", "interface set interface name=\"Lan1\" newname=\"Lan1\""));
        }
    }


    [TestFixture]
    public class SetNetworkInterfaceSpec_When_Working_With_Multiple_Ips_In_An_Interface : SetNetworkInterfaceSpecBase {
        [SetUp]
        public void Setup() {
            Setup("fakemac", true);
            ExecutableProcessQueue.Expect(x => x.Go()).Repeat.Once();

            SetNetworkInterface = new SetNetworkInterface(ExecutableProcessQueue, WmiMacNetworkNameGetter, Logger);
        }

        [Test]
        public void should_configure_the_interface_correctly_for_both_ips_with_the_gateway() {
            SetNetworkInterface.Execute(new List<NetworkInterface> { NetworkInterface });
            ExecutableProcessQueue.AssertWasCalled(
                x =>
                x.Enqueue("netsh",
                          "interface ip add address name=\"Lan1\" addr=192.168.1.110 mask=255.255.255.0 gateway=192.168.1.1 gwmetric=2"));
            ExecutableProcessQueue.AssertWasCalled(
                x =>
                x.Enqueue("netsh",
                "interface ip add address name=\"Lan1\" addr=1.2.2.2 mask=255.255.0.0")); 
        }

        [Test]
        public void should_configure_the_interface_correctly_for_both_ips_without_the_gateway() {
            NetworkInterface.gateway = null;
            SetNetworkInterface.Execute(new List<NetworkInterface> { NetworkInterface });
            ExecutableProcessQueue.AssertWasCalled(
                x =>x.Enqueue("netsh","interface ip add address name=\"Lan1\" addr=192.168.1.110 mask=255.255.255.0")); 
            ExecutableProcessQueue.AssertWasCalled(
                x => x.Enqueue("netsh", "interface ip add address name=\"Lan1\" addr=1.2.2.2 mask=255.255.0.0"));
        }
    }

    [TestFixture]
    public class SetNetworkInterfaceSpec_When_Configuring_A_Secondary_Interface_With_No_Dns :
        SetNetworkInterfaceSpecBase {
        [SetUp]
        public void Setup() {
            Setup("fakemac", false, false, true);
            ExecutableProcessQueue.Expect(x => x.Go()).Repeat.Once();

            SetNetworkInterface = new SetNetworkInterface(ExecutableProcessQueue, WmiMacNetworkNameGetter, Logger);
            SetNetworkInterface.Execute(new List<NetworkInterface> { NetworkInterface });
        }

        [Test]
        public void should_not_call_the_dns_configuration() {
            ExecutableProcessQueue.AssertWasNotCalled(
                x => x.Enqueue("netsh", "interface ip set dns name=\"Lan1\" source=dhcp"));
        }
        }

    [TestFixture]
    public class SetNetworkInterfaceSpec_When_Exception_Gets_Thrown_For_A_Bad_Mac : SetNetworkInterfaceSpecBase {
        [SetUp]
        public void Setup() {
            Setup("some_mac_not_found");
            ExecutableProcessQueue.Expect(x => x.Go()).Repeat.Once();
            SetNetworkInterface = new SetNetworkInterface(ExecutableProcessQueue, WmiMacNetworkNameGetter, Logger);
        }

        [Test]
        [ExpectedException(typeof (ApplicationException))]
        public void ApplicationException_should_be_thrown() {
            SetNetworkInterface.Execute(new List<NetworkInterface> { NetworkInterface });
        }
    }

    [TestFixture]
    public class SetNetworkInterfaceSpec_When_Configuring_the_interface_with_A_disabled_ip : SetNetworkInterfaceSpecBase {
        [SetUp]
        public void Setup() {
            Setup("fakemac", true, true, false);
            ExecutableProcessQueue.Expect(x => x.Go()).Repeat.Once();
            SetNetworkInterface = new SetNetworkInterface(ExecutableProcessQueue, WmiMacNetworkNameGetter, Logger);
        }

        [Test]
        public void should_configure_the_interface_correctly_for_one_ip_with_the_gateway() {
            SetNetworkInterface.Execute(new List<NetworkInterface> { NetworkInterface });
            ExecutableProcessQueue.AssertWasCalled(
                x =>
                x.Enqueue("netsh",
                          "interface ip add address name=\"Lan1\" addr=192.168.1.110 mask=255.255.255.0 gateway=192.168.1.1 gwmetric=2"));
            ExecutableProcessQueue.AssertWasNotCalled(
                x =>
                x.Enqueue("netsh",
                          "interface ip add address name=\"Lan1\" addr=1.2.2.2 mask=255.255.0.0 gateway=192.168.1.1 gwmetric=2"));
            ExecutableProcessQueue.AssertWasNotCalled(
                x =>
                x.Enqueue("netsh",
                          "interface ip add address name=\"Lan1\" addr=1.2.2.2 mask=255.255.0.0")); 
        }
    }
}