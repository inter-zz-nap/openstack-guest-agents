sc stop RackspaceCloudServersAgentUpdater
sc delete RackspaceCloudServersAgentUpdater
sc create RackspaceCloudServersAgentUpdater binpath= "%CD%\Rackspace.Cloud.Server.Agent.UpdaterService.exe" start= auto
sc start RackspaceCloudServersAgentUpdater