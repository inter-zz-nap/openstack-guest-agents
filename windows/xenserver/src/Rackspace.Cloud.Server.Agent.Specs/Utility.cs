using System;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rhino.Mocks;
using StructureMap;
using StructureMap.Configuration.DSL;

namespace Rackspace.Cloud.Server.Agent.Specs {
    public class Utility {
        [ThreadStatic] 
        private static bool _isStructureMapConfigured;

        public static void ConfigureStructureMap()
        {
            if (!_isStructureMapConfigured)
            {
                StructureMapConfiguration.UseDefaultStructureMapConfigFile = false;
                StructureMapConfiguration.BuildInstancesOf<ITimer>().TheDefaultIs(
                    Registry.Object(MockRepository.GenerateMock<ITimer>()));
                IoC.Register();

                _isStructureMapConfigured = true;
            }
        }
    }
}
