sc stop RackspaceCloudServersAgent
sc delete RackspaceCloudServersAgent
sc create RackspaceCloudServersAgent binpath= "%CD%\Rackspace.Cloud.Server.Agent.Service.exe" start= auto
sc start RackspaceCloudServersAgent