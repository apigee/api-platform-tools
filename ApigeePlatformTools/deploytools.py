import json
import urlparse

from ApigeePlatformTools import httptools

def getBaseUrl(org, env, name, basePath, revision):
  response = httptools.httpCall('GET',
      '/v1/o/%s/apis/%s/revisions/%i/proxies' % (org, name, revision))
  proxies = json.load(response)
  if len(proxies) < 1:
    # No proxies
    return '(unknown)'
    
  response = httptools.httpCall('GET',
      '/v1/o/%s/apis/%s/revisions/%i/proxies/%s' % (org, name, revision, proxies[0]))
  proxy = json.load(response)
  if len(proxy['connection']['virtualHost']) < 1:
    # No virtual hosts
    return '(unknown)'
  vhName = proxy['connection']['virtualHost'][0]
  
  response = httptools.httpCall('GET',
      '/v1/o/%s/e/%s/virtualhosts/%s' % (org, env, vhName))
  vh = json.load(response)
  if len(vh['hostAliases']) < 1:
    # No aliases
    alias = ''
  else:
    alias = vh['hostAliases'][0]
  
  ret = 'http://%s:%s/' % (alias, vh['port'])
  if len(basePath) > 0:
    ret = urlparse.urljoin(ret, basePath)
  proxyBasePath = proxy['connection']['basePath']
  if len(proxyBasePath) > 0:
    ret = urlparse.urljoin(ret, proxyBasePath)
  return ret

def parseEnvDeployments(org, resp, env):
  ret = []
  deployments = json.load(resp)
  for proxyDep in deployments['aPIProxy']:
    name = proxyDep['name']
    for revision in proxyDep['revision']:
      revNum = int(revision['name'])
      basePath = revision['configuration']['basePath']
      ri = { 
        'name': name, 
        'basePath': basePath,
        'state': revision['state'],
        'revision': revNum,
        'environment': env,
        'baseUrl': getBaseUrl(org, env, name, basePath, revNum)
      }      
      ret.append(ri)
  return ret
  

def parseAppDeployments(org, resp, name):
  ret = []
  deployments = json.load(resp)
  if not 'environment' in deployments:
    return ret
  for envDep in deployments['environment']:
    env = envDep['name']
    for revision in envDep['revision']:
      revNum = int(revision['name'])
      basePath = revision['configuration']['basePath']
      ri = { 
        'name': name, 
        'basePath': basePath,
        'state': revision['state'],
        'revision': revNum,
        'environment': env,
        'baseUrl': getBaseUrl(org, env, name, basePath, revNum)
      }      
      ret.append(ri)
  return ret
  
def cmpDeployment(d1, d2):
  c = cmp(d1['name'], d2['name'])
  if (c == 0):
    return d1['revision'] - d2['revision']
  return c
  
def printDeployments(deployments):
  deployments.sort(cmpDeployment)
  for d in deployments:
    print 'Proxy: "%s" Revision %i' % (d['name'], d['revision'])
    print '  Environment: %s BasePath: %s' % (d['environment'], d['basePath'])
    print '  Status: %s' % (d['state'])
    print '  Base URL: %s' % (d['baseUrl'])
    
def getAndParseDeployments(org, name):
  response = httptools.httpCall('GET', 
      '/v1/o/%s/apis/%s/deployments' % (org, name))
  return parseAppDeployments(org, response, name)  
    
def getAndPrintDeployments(org, name):
  printDeployments(getAndParseDeployments(org, name))
  
def getAndParseEnvDeployments(org, env):
  response = httptools.httpCall('GET', 
      '/v1/o/%s/e/%s/deployments' % (org, env))
  return parseEnvDeployments(org, response, env)   
  
def getAndPrintEnvDeployments(org, env):
  printDeployments(getAndParseEnvDeployments(org, env))
    
def importBundle(org, name, data):
  hdrs = { 'Content-Type' : 'application/octet-stream' }
  uri =  '/v1/organizations/%s/apis?action=import&name=%s' \
             % (org, name)
  print 'Importing new application %s' % name
  resp = httptools.httpCall('POST', uri, hdrs, data)

  if resp.status != 200 and resp.status != 201:
    print 'Import failed to %s with status %i:\n%s' % (uri, resp.status, resp.read())
    return -1

  deployment = json.load(resp)
  revision = int(deployment['revision'])
  return revision
    
def deployWithoutConflict(org, env, name, basePath, revision):
  response = httptools.httpCall('GET', 
    '/v1/o/%s/apis/%s/deployments' % (org, name))
  
  hdrs = { 'Content-Type': 'application/x-www-form-urlencoded' }
  deps = parseAppDeployments(org, response, name)
  for d in deps:
    if d['environment'] == env and \
      d['basePath'] == basePath and \
      d['revision'] != revision:
      print 'Undeploying revision %i in same environment and path:' % d['revision']
      resp = httptools.httpCall('POST', 
                     '/v1/organizations/%s/apis/%s/deployments' % (org, name),
                     hdrs, 
                     'action=undeploy&env=%s&revision=%i' % (env, d['revision']))
      if resp.status != 200 and resp.status != 204:
        print 'Error %i on undeployment:\n%s' % (resp.status, resp.read())
        return False

  # Deploy the bundle
  print 'Deploying revision %i' % revision
  resp = httptools.httpCall('POST',
                 '/v1/organizations/%s/apis/%s/deployments' \
                  % (org, name),
                  hdrs,
                  'action=deploy&env=%s&revision=%s&basepath=%s' \
                  % (env, revision, basePath))

  if resp.status != 200 and resp.status != 201:
    print 'Deploy failed with status %i:\n%s' % (resp.status, resp.read())
    return False
  print '  Deployed.'
  return True
  
def undeploy(org, env, name, revision):
  print 'Undeploying proxy %s revision %i' % (name, revision)
  hdrs = { 'Content-Type': 'application/x-www-form-urlencoded' }
  resp = httptools.httpCall('POST',
    '/v1/organizations/%s/apis/%s/deployments' % (org, name),
    hdrs,
    'action=undeploy&env=%s&revision=%i' % (env, revision))
  if resp.status != 200 and resp.status != 204:
        print 'Error %i on undeployment:\n%s' % (resp.status, resp.read())
        return False
  return True

