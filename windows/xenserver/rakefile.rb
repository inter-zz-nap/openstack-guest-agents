require 'rubygems'
require 'albacore'
require './Properties.rb'
require 'fileutils'

desc "compiles, runs tests and creates zip file"
task :all => [:default]

desc "compiles, runs tests and creates zip file"
task :default => [:compile, :tests, :package]

desc "Versioning"
task :version do
  puts "The build number is #{RELEASE_BUILD_NUMBER}"
  Rake::Task["agent:assemblyinfo"].execute
  Rake::Task["agent_service:assemblyinfo"].execute
  Rake::Task["update_service:assemblyinfo"].execute
  Rake::Task["common:assemblyinfo"].execute
  Rake::Task["diffie_hellman:assemblyinfo"].execute
end

namespace :agent do
  desc "Update the version information for agent library"
  assemblyinfo :assemblyinfo do |asm|
    asm.version = RELEASE_BUILD_NUMBER
    asm.company_name = COMPANY
    asm.product_name = PRODUCT
    asm.description = DESCRIPTION
    asm.copyright = COPYRIGHT
    asm.output_file = File.join(ABSOLUTE_PATH,'src','Rackspace.Cloud.Server.Agent','Properties','AssemblyInfo.cs')
  end
end

namespace :common do
  desc "Update the version information for common library"
  assemblyinfo :assemblyinfo do |asm|
    asm.version = RELEASE_BUILD_NUMBER
    asm.company_name = COMPANY
    asm.product_name = PRODUCT
    asm.description = DESCRIPTION
    asm.copyright = COPYRIGHT
    asm.output_file = File.join(ABSOLUTE_PATH,'src','Rackspace.Cloud.Server.Agent','Properties','AssemblyInfo.cs')
  end
end

namespace :diffie_hellman do
  desc "Update the version information for diffie hellman library"
  assemblyinfo :assemblyinfo do |asm|
    asm.version = RELEASE_BUILD_NUMBER
    asm.company_name = COMPANY
    asm.product_name = PRODUCT
    asm.description = DESCRIPTION
    asm.copyright = COPYRIGHT
    asm.output_file = File.join(ABSOLUTE_PATH,'src','Rackspace.Cloud.Server.Agent','Properties','AssemblyInfo.cs')
  end
end

desc "Compile the solution"
msbuild :compile => :version do |msb|
  msb.command = MSBUILD_EXE
  msb.properties :configuration => COMPILE_TARGET
  msb.targets :Rebuild
  msb.verbosity = 'minimal'
  msb.solution = SLN_FILE
end

desc "Run unit tests"
task :tests => [:agent_specs, :diffiehellman_specs]

desc "Run agent unit tests"
nunit :agent_specs => :compile do |nunit|
  nunit.command = NUNIT_CMD_EXE
  nunit.assemblies AGENT_UNIT_TEST_DLL
  nunit.options '/xml=agent-unit-tests-results.xml'
end

desc "Run diffiehellman unit tests"
nunit :diffiehellman_specs => :compile do |nunit|
  nunit.command = NUNIT_CMD_EXE
  nunit.assemblies DIFFIEHELLMAN_UNIT_TEST_DLL
  nunit.options '/xml=diffiehellman-unit-tests-results.xml'
end

desc "Packaging"
task :package do
  Dir.mkdir BUILDS_DIR if !File.directory?(BUILDS_DIR)
  Rake::Task["agent_service:zip"].execute
  Rake::Task["update_service:zip"].execute
end

namespace :agent_service do
  desc "Update the version information for agent service library"
  assemblyinfo :assemblyinfo do |asm|
    asm.version = RELEASE_BUILD_NUMBER
    asm.company_name = COMPANY
    asm.product_name = PRODUCT
    asm.description = DESCRIPTION
    asm.copyright = COPYRIGHT
    asm.output_file = File.join(ABSOLUTE_PATH,'src','Rackspace.Cloud.Server.Agent.Service','Properties','AssemblyInfo.cs')
  end
  
  desc "Create zip for agent service"
  zip do |zip|
    file = 'AgentService.zip'
    File.delete(file) if File.exists?(file)
    zip.output_path = BUILDS_DIR
    zip.directories_to_zip AGENT_SERVICE_DIR
    zip.additional_files = ["installagentservice.bat"]
    zip.output_file = file
    puts "Agent Service zip file created"
  end
end

namespace :update_service do
  desc "Update the version information for udpate service library"
  assemblyinfo :assemblyinfo do |asm|
    asm.version = RELEASE_BUILD_NUMBER
    asm.company_name = COMPANY
    asm.product_name = PRODUCT
    asm.description = DESCRIPTION
    asm.copyright = COPYRIGHT
    asm.output_file = File.join(ABSOLUTE_PATH,'src','Rackspace.Cloud.Server.Agent.UpdaterService','Properties','AssemblyInfo.cs')
  end
  
  desc "Create zip for update service"
  zip do |zip|
    file = 'UpdateService.zip'
    File.delete(file) if File.exists?(file)
    zip.output_path = BUILDS_DIR
    zip.directories_to_zip UPDATE_SERVICE_DIR
    zip.additional_files = ["installupdateservice.bat"]
    zip.output_file = file
    puts "Update Service zip file created"
  end
end