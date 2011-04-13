using System.IO;

namespace Rackspace.Cloud.Server.Agent.Interfaces
{
    public interface IProcessWrapper
    {
        string FileName { get; set; }
        string Arguments { get; set; }
        bool CreateNoWindow { get; }
        bool UseShellExecute { get; }
        bool RedirectStandardOutput { get; }
        bool RedirectStandardError { get; }
        int ExitCode { get; }
        StreamReader StandardError { get; }
        StreamReader StandardOutput { get; }
        bool Start();
        void WaitForExit();
    }
}