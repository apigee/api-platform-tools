import base64
import getopt
import httplib
import json
import re
import os
import os.path
import sys
import StringIO
import urlparse
import xml.dom.minidom
import zipfile
import getpass

from ApigeePlatformTools import httptools, deploytools

def printUsage():
  print 'Usage: deploynodeapp -n [name] -o [organization] -e [environment]'
  print '         -d [directory name] -m [main script file]'
  print '         -u [username] -p [password]'
  print '         -b [base path] -l [apigee API url] -z [zip file] -i -h'
  print ''
  print '-o Apigee organization name'
  print '-e Apigee environment name'
  print '-n Apigee proxy name'
  print '-d Apigee proxy directory'
  print '-m Main script name: Should be at the top level of the directory'
  print '-u Apigee user name'
  print '-p Apigee password (optional, will prompt if not supplied)'
  print '-b Base path (optional, defaults to /)'
  print '-l Apigee API URL (optional, defaults to https://api.enterprise.apigee.com)'
  print '-z ZIP file to save (optional for debugging)'
  print '-i import only, do not deploy'
  print '-x Virtual Host name (optional, defaults to "default")'
  print '-h Print this message'
  print ''
  print 'Typically, the "default" virtual host listens on HTTP.'
  print 'For an HTTPS-only app, use "-x secure".'

def run():
  ApigeeURL = 'https://api.enterprise.apigee.com'
  Username = None
  Password = None
  Directory = None
  MainScript = None
  Organization = None
  Environment = None
  Name = None
  BasePath = '/'
  ShouldDeploy = True
  ZipFile = None
  VirtualHost = 'default'
  Options = 'o:e:x:n:d:m:u:p:b:l:z:ih'

  opts = getopt.getopt(sys.argv[2:], Options)[0]

  for o in opts:
    if o[0] == '-o':
      Organization = o[1]
    elif o[0] == '-e':
      Environment =o[1]
    elif o[0] == '-n':
      Name = o[1]
    elif o[0] == '-d':
      Directory =o[1]
    elif o[0] == '-m':
      MainScript = o[1]
    elif o[0] == '-u':
      Username = o[1]
    elif o[0] == '-p':
      Password = o[1]
    elif o[0] == '-b':
      BasePath = o[1]
    elif o[0] == '-l':
      ApigeeURL = o[1]
    elif o[0] == '-z':
      ZipFile = o[1]
    elif o[0] == '-x':
      VirtualHost = o[1]
    elif o[0] == '-i':
      ShouldDeploy = False
    elif o[0] == '-h':
      printUsage()
      sys.exit(0)

  BadUsage = False
  if not Username:
    BadUsage = True
    print '-u is required'
  if not Directory:
    BadUsage = True
    print '-d is required'
  if not Environment:
    BadUsage = True
    print '-e is required'
  if not Name:
    BadUsage = True
    print '-n is required'
  if not Organization:
    BadUsage = True
    print '-o is required'
  if not MainScript:
    BadUsage = True
    print '-m is required'

  if not BadUsage and not Password:
    Password = getpass.getpass()
  if not BadUsage and not Password:
    BadUsage = True
    print 'Password is required'

  if BadUsage:
    printUsage()
    sys.exit(1)

  httptools.setup(ApigeeURL, Username, Password)

  def makeApplication():
    return '<APIProxy name="%s"/>' % Name

  def makeProxy():
    return '<ProxyEndpoint name="default">\
      <HTTPProxyConnection>\
      <BasePath>%s</BasePath>\
      <VirtualHost>%s</VirtualHost>\
      </HTTPProxyConnection>\
      <RouteRule name="default">\
      <TargetEndpoint>default</TargetEndpoint>\
      </RouteRule>\
      </ProxyEndpoint>' % (BasePath, VirtualHost)

  def makeTarget():
    return '<TargetEndpoint name="default">\
      <ScriptTarget>\
      <ResourceURL>node://%s</ResourceURL>\
      </ScriptTarget>\
      </TargetEndpoint>' % MainScript

  # Return TRUE if any component of the file path contains a directory name that
  # starts with a "." like '.svn', but not '.' or '..'
  def pathContainsDot(p):
    c = re.compile('\.\w+')
    for pc in p.split('/'):
      if c.match(pc) != None:
        return True
    return False

  # ZIP a whole directory into a stream and return the result so that it
  # can be nested into the top-level ZIP

  def zipDirectory(dir, pfx):
    ret = StringIO.StringIO()
    tzip = zipfile.ZipFile(ret, 'w')
    dirList = os.walk(dir)
    for dirEntry in dirList:
      for fileEntry in dirEntry[2]:
        if not fileEntry.endswith('~'):
          fn = os.path.join(dirEntry[0], fileEntry)
          en = os.path.join(pfx, os.path.relpath(dirEntry[0], dir), fileEntry)
          if (os.path.isfile(fn)):
            tzip.write(fn, en)
    tzip.close()
    return ret.getvalue()

  # Construct a ZIPped copy of the bundle in memory
  tf = StringIO.StringIO()
  zipout = zipfile.ZipFile(tf, 'w')

  zipout.writestr('apiproxy/%s.xml' % Name, makeApplication())
  zipout.writestr('apiproxy/proxies/default.xml', makeProxy())
  zipout.writestr('apiproxy/targets/default.xml', makeTarget())

  for topName in os.listdir(Directory):
    if not pathContainsDot(topName):
      fn = os.path.join(Directory, topName)
      if (os.path.isdir(fn)):
        contents = zipDirectory(fn, topName)
        en = 'apiproxy/resources/node/%s.zip' % topName
        zipout.writestr(en, contents)
      else:
        en = 'apiproxy/resources/node/%s' % topName
        zipout.write(fn, en)
  zipout.close()

  if (ZipFile != None):
    tzf = open(ZipFile, 'w')
    tzf.write(tf.getvalue())
    tzf.close()

  revision = deploytools.importBundle(Organization, Name, tf.getvalue())
  if (revision < 0):
    sys.exit(2)

  print 'Imported new app revision %i' % revision

  if ShouldDeploy:
    status = deploytools.deployWithoutConflict(Organization, Environment, Name, '/', revision)
    if status == False:
      sys.exit(2)

  response = httptools.httpCall('GET',
      '/v1/o/%s/apis/%s/deployments' % (Organization, Name))
  deps = deploytools.parseAppDeployments(Organization, response, Name)
  deploytools.printDeployments(deps)

