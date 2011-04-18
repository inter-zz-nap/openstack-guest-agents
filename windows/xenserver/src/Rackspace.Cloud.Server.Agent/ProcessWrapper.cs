using System;
using System.Diagnostics;
using System.IO;
using Rackspace.Cloud.Server.Agent.Interfaces;

namespace Rackspace.Cloud.Server.Agent
{
    public class ProcessWrapper : IProcessWrapper
    {
        private Process process;

        public ProcessWrapper() : this(true, false, true, true) { }

        public ProcessWrapper(bool createNoWindow, bool useShellExecute, bool redirectStandardOutput, bool redirectStandardError)
        {
            process = new Process();
            process.StartInfo.CreateNoWindow = createNoWindow;
            process.StartInfo.UseShellExecute = useShellExecute;
            process.StartInfo.RedirectStandardOutput = redirectStandardOutput;
            process.StartInfo.RedirectStandardError = redirectStandardError;
        }

        public string FileName
        {
            get { return process.StartInfo.FileName; }
            set { process.StartInfo.FileName = value; }
        }
        public string Arguments
        {
            get { return process.StartInfo.Arguments; }
            set { process.StartInfo.Arguments = value; }
        }
        public bool CreateNoWindow
        {
            get { return process.StartInfo.CreateNoWindow; }
        }

        public bool UseShellExecute
        {
            get { return process.StartInfo.UseShellExecute; }
        }

        public bool RedirectStandardOutput
        {
            get { return process.StartInfo.RedirectStandardOutput; }
        }

        public bool RedirectStandardError
        {
            get { return process.StartInfo.RedirectStandardError; }
        }

        public int ExitCode
        {
            get { return process.ExitCode; }
        }

        public bool Start()
        {
            return process.Start();
        }

        public void WaitForExit()
        {
            process.WaitForExit();
        }

        public StreamReader StandardError
        {
            get { return process.StandardError; }
        }
        public StreamReader StandardOutput
        {
            get { return process.StandardOutput; }
        }
    }
}