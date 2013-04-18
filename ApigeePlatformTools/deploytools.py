import json

from ApigeePlatformTools import httptools

def parseEnvDeployments(resp, env):
  ret = []
  deployments = json.load(resp)
  for proxyDep in deployments['aPIProxy']:
    name = proxyDep['name']
    for revision in proxyDep['revision']:
      ri = { 
        'name': name, 
        'basePath': revision['configuration']['basePath'],
        'state': revision['state'],
        'revision': int(revision['name']),
        'environment': env
      }      
      ret.append(ri)
  return ret
  

def parseAppDeployments(resp, name):
  ret = []
  deployments = json.load(resp)
  for envDep in deployments['environment']:
    env = envDep['name']
    for revision in envDep['revision']:
      ri = { 
        'name': name, 
        'basePath': revision['configuration']['basePath'],
        'state': revision['state'],
        'revision': int(revision['name']),
        'environment': env
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
    
def importBundle(org, name, data):
  hdrs = { 'Content-Type' : 'application/octet-stream' }
  uri =  '/v1/organizations/%s/apis?action=import&name=%s' \
             % (org, name)
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
  deps = parseAppDeployments(response, name)
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
  resp = httptools.httpCall('POST',
                 '/v1/organizations/%s/apis/%s/deployments' \
                  % (org, name),
                  hdrs,
                  'action=deploy&env=%s&revision=%s&basepath=%s' \
                  % (env, revision, basePath))

  if resp.status != 200 and resp.status != 201:
    print 'Deploy failed with status %i:\n%s' % (resp.status, resp.read())
    return False
  return True

