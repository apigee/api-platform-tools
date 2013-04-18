#!/usr/bin/env python

import getopt
import sys

from ApigeePlatformTools import httptools, deploytools

ApigeeURL = 'https://api.enterprise.apigee.com'
Username = None
Password = None
Organization = None
Environment = None
Name = None

def printUsage():
  print 'Usage: listdeployments -o [organization] -n [proxy name] -e [environment]'
  print '                       -u [username] -p [password] '
  print '                       -l [Apigee URL]'
  print ''
  print '-o Apigee organization name'
  print '-e Apigee environment name (optional, see below)'
  print '-n Apigee proxy name (optional, see below)'
  print '-u Apigee user name'
  print '-p Apigee password'
  print '-l Apigee API URL (optional, defaults to https://api.enterprise.apigee.com)'
  print '-h Print this message'
  print ''
  print 'To show all deployments in one environment, use -o and -e.'
  print 'To show deployments of an API in one environment, use -o and -n.'

Options = 'o:n:e:u:p:l:h'

opts = getopt.getopt(sys.argv[1:], Options)[0]

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
    ApigeeUrl = o[1]
  elif o[0] == '-h':
    printUsage()
    sys.exit(1)
    
  
if Username == None or Password == None or Organization == None:
  printUsage();
  sys.exit(1)


httptools.setup(ApigeeURL, Username, Password)
    
    
if ((Environment == None) and (Name != None)):
  response = httptools.httpCall('GET', 
    '/v1/o/%s/apis/%s/deployments' % (Organization, Name))
  deployments = deploytools.parseAppDeployments(response, Name)
    
elif ((Environment != None) and (Name == None)):
  response = httptools.httpCall('GET', 
    '/v1/o/%s/e/%s/deployments' % (Organization, Environment))
  deployments = deploytools.parseEnvDeployments(response, Environment)
    
else:
  printUsage()
  sys.exit(1)
  
deploytools.printDeployments(deployments)







