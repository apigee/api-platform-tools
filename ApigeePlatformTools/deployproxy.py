import base64
import getopt
import httplib
import json
import re
import os
import sys
import StringIO
import urlparse
import xml.dom.minidom
import zipfile
import getpass

from ApigeePlatformTools import httptools, deploytools



def printUsage():
  print 'Usage: deployproxy -n [name] -o [organization] -e [environment]'
  print '         -d [directory name]'
  print '         -u [username] -p [password]'
  print '         -b [base path] -l [apigee API url] -z [zip file] -i -h'
  print ''
  print '-o Apigee organization name'
  print '-e Apigee environment name'
  print '-n Apigee proxy name'
  print '-d Apigee proxy directory'
  print '-u Apigee user name'
  print '-p Apigee password (optional, will prompt if not supplied)'
  print '-b Base path (optional, defaults to /)'
  print '-l Apigee API URL (optional, defaults to https://api.enterprise.apigee.com)'
  print '-z ZIP file to save (optional for debugging)'
  print '-i import only, do not deploy'
  print '-h Print this message'

def run():
  ApigeeURL = 'https://api.enterprise.apigee.com'
  Username = None
  Password = None
  Directory = None
  Organization = None
  Environment = None
  Name = None
  BasePath = '/'
  ShouldDeploy = True
  ZipFile = None

  Options = 'o:e:n:d:u:p:b:l:z:ih'

  opts = getopt.getopt(sys.argv[2:], Options)[0]

  for o in opts:
    if o[0] == '-n':
      Name = o[1]
    elif o[0] == '-o':
      Organization = o[1]
    elif o[0] == '-d':
      Directory =o[1]
    elif o[0] == '-e':
      Environment =o[1]
    elif o[0] == '-b':
      BasePath = o[1]
    elif o[0] == '-u':
      Username = o[1]
    elif o[0] == '-p':
      Password = o[1]
    elif o[0] == '-l':
      ApigeeURL = o[1]
    elif o[0] == '-z':
      ZipFile = o[1]
    elif o[0] == '-i':
      ShouldDeploy = False
    elif o[0] == '-h':
      printUsage()
      sys.exit(0)

  if not Password:
    Password = getpass.getpass()

  if not Username or not Password or not Directory or \
     not Environment or not Name or not Organization:
    printUsage()
    sys.exit(1)

  httptools.setup(ApigeeURL, Username, Password)

  # Return TRUE if any component of the file path contains a directory name that
  # starts with a "." like '.svn', but not '.' or '..'
  def pathContainsDot(p):
    c = re.compile('\.\w+')
    for pc in p.split('/'):
      if c.match(pc) != None:
        return True
    return False

  # Construct a ZIPped copy of the bundle in memory
  tf = StringIO.StringIO()
  zipout = zipfile.ZipFile(tf, 'w')

  dirList = os.walk(Directory)
  for dirEntry in dirList:
    if not pathContainsDot(dirEntry[0]):
      for fileEntry in dirEntry[2]:
        if not fileEntry.endswith('~'):
          fn = os.path.join(dirEntry[0], fileEntry)
          en = os.path.join(os.path.relpath(dirEntry[0], Directory), fileEntry)
          zipout.write(fn, en)
  zipout.close()

  if (ZipFile != None):
    tzf = open(ZipFile, 'w')
    tzf.write(tf.getvalue())
    tzf.close()

  revision = deploytools.importBundle(Organization, Name, tf.getvalue())
  if (revision < 0):
    sys.exit(2)

  print 'Imported new proxy revision %i' % revision

  if ShouldDeploy:
    status = deploytools.deployWithoutConflict(Organization, Environment, Name, BasePath, revision)
    if status == False:
      sys.exit(2)

  response = httptools.httpCall('GET',
      '/v1/o/%s/apis/%s/deployments' % (Organization, Name))
  deps = deploytools.parseAppDeployments(Organization, response, Name)
  deploytools.printDeployments(deps)

