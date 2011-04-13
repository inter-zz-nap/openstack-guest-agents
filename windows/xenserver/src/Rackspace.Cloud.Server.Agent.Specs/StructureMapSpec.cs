using System;
using NUnit.Framework;
using StructureMap;

namespace Rackspace.Cloud.Server.Agent.Specs {
    [TestFixture]
    public class StructureMapSpec {
        [SetUp]
        public void Setup() {
            Utility.ConfigureStructureMap();

        }

        [Test]
        public void Should_setup_dependencies_in_structuremap_correctly() {
            ObjectFactory.GetInstance<ServiceWork>();
        }

        [Test]
        public void should_create_a_dependency_tree_for_kmsactivate() {
            var factory = new CommandFactory();
            foreach (var name in Enum.GetNames(typeof(Utilities.Commands)))
            {
                factory.CreateCommand(name);    
            }
        }
    }
}