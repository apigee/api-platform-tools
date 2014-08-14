import getopt
import sys
import getpass

from ApigeePlatformTools import httptools, deploytools

def printUsage():
  print 'Usage: listdeployments -o [organization] -n [proxy name] -e [environment]'
  print '                       -u [username] -p [password] '
  print '                       -l [Apigee URL]'
  print ''
  print '-o Apigee organization name'
  print '-e Apigee environment name (optional, see below)'
  print '-n Apigee proxy name (optional, see below)'
  print '-u Apigee user name'
  print '-p Apigee password (optional, will prompt if not supplied)'
  print '-l Apigee API URL (optional, defaults to https://api.enterprise.apigee.com)'
  print '-h Print this message'
  print ''
  print 'To show all deployments in one environment, use -o and -e.'
  print 'To show deployments of an API in one environment, use -o and -n.'

def run():
  ApigeeURL = 'https://api.enterprise.apigee.com'
  Username = None
  Password = None
  Organization = None
  Environment = None
  Name = None
  Options = 'o:n:e:u:p:l:h'

  opts = getopt.getopt(sys.argv[2:], Options)[0]

  for o in opts:
    if o[0] == '-n':
      Name = o[1]
    elif o[0] == '-o':
      Organization = o[1]
    elif o[0] == '-e':
      Environment = o[1]
    elif o[0] == '-u':
      Username = o[1]
    elif o[0] == '-p':
      Password = o[1]
    elif o[0] == '-l':
      ApigeeURL = o[1]
    elif o[0] == '-h':
      printUsage()
      sys.exit(0)

  if not Password:
    Password = getpass.getpass()

  if not Username or not Password or not Organization:
    printUsage();
    sys.exit(1)

  httptools.setup(ApigeeURL, Username, Password)


  if ((Environment == None) and (Name != None)):
    deploytools.getAndPrintDeployments(Organization, Name)

  elif ((Environment != None) and (Name == None)):
    deploytools.getAndPrintEnvDeployments(Organization, Environment)

  else:
    printUsage()
    sys.exit(1)








