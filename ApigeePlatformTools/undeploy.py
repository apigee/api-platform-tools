import getopt
import sys

from ApigeePlatformTools import httptools, deploytools

def printUsage():
  print 'Usage: undeploy -o [organization] -n [proxy name]'
  print '                -r [revision] -e [environment]'
  print '                -u [username] -p [password] '
  print '                -l [Apigee URL]'
  print ''
  print '-o Apigee organization name'
  print '-n Apigee proxy name'
  print '-e Apigee environment name (optional, see below)'
  print '-r Revision to undeploy (optional, see below)'
  print '-u Apigee user name'
  print '-p Apigee password'
  print '-l Apigee API URL (optional, defaults to https://api.enterprise.apigee.com)'
  print '-h Print this message'
  print ''
  print 'To undeploy all revisions of the proxy in all environments, use -n'
  print 'To undeploy a specific revision in all environments, use -r and -n'
  print 'To undeploy all revisions in a specific environment, use -n and -e'
  print 'Use all three to undeploy a specific revision in a specific environment'

def run():  
  ApigeeURL = 'https://api.enterprise.apigee.com'
  Username = None
  Password = None
  Organization = None
  Environment = None
  Name = None
  Revision = None
  Options = 'o:n:r:e:u:p:l:h'
  
  opts = getopt.getopt(sys.argv[2:], Options)[0]
  
  for o in opts:
    if o[0] == '-n':
      Name = o[1]
    elif o[0] == '-o':
      Organization = o[1]
    elif o[0] == '-e':
      Environment = o[1]
    elif o[0] == '-r':
      Revision = o[1]
    elif o[0] == '-u':
      Username = o[1]
    elif o[0] == '-p':
      Password = o[1]
    elif o[0] == '-l':
      ApigeeURL = o[1]
    elif o[0] == '-h':
      printUsage()
      sys.exit(1)
      
    
  if Username == None or Password == None or Organization == None or Name == None:
    printUsage();
    sys.exit(1)
  
  
  httptools.setup(ApigeeURL, Username, Password)
      
  if ((Environment == None) and (Revision == None)):
    deployments = deploytools.getAndParseDeployments(Organization, Name)
    for dep in deployments:
      deploytools.undeploy(Organization, dep['environment'],
                           Name, dep['revision'])
    deploytools.getAndPrintDeployments(Organization, Name)

  elif (Environment == None):
    deployments = deploytools.getAndParseDeployments(Organization, Name)
    for dep in deployments:
      if (dep['revision'] == Revision):
        deploytools.undeploy(Organization, dep['environment'],
                             Name, dep['revision'])
    deploytools.getAndPrintDeployments(Organization, Name)
  
  else:
    deployments = deploytools.getAndParseEnvDeployments(Organization, Environment)
    for dep in deployments:
      if (dep['name'] == Name):
        deploytools.undeploy(Organization, Environment,
                             Name, dep['revision'])
    deploytools.getAndPrintEnvDeployments(Organization, Environment)








