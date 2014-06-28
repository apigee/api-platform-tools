import json
import traceback
import urlparse

from ApigeePlatformTools import httptools

IOError_messages = {
  32: 'Check that the zipped file size is not >10MB and verify that your Apigee credentials are correct.',
  8: 'Check the specified value for "apigee_url"',
  61: 'Connection refused. Check the specified value for "apigee_url"'
}

HTTP_messages = {
  400: '400 Bad Request.  The syntax of the command is incorrect',
  401: '401 Unauthorized.  Verify your Apigee Credentials are correct',
  403: '403 Forbidden.  Verify that the specified Organization name is correct and that you have appropriate permissions',
  404: '404 Not Found.  Verify the Organization name is correct',
  407: '407 Proxy Authentication Required.  Verify your network configuration is correct if using an HTTP Proxy',
  500: '500 Internal Server Error.  Something went wrong processing your bundle',
  503: '503 Service Unavailable.  Please try your request again after a few minutes'
}


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

  if vhName == 'secure':
    httpScheme = 'https'
  else:
    httpScheme = 'http'

  ret = httpScheme + '://%s:%s/' % (alias, vh['port'])
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
  hdrs = { 'Content-Type': 'application/octet-stream' }
  uri = '/v1/organizations/%s/apis?action=import&name=%s' \
        % (org, name)
  print 'Importing new application %s' % name

  resp = None

  try:
    resp = httptools.httpCall('POST', uri, hdrs, data)

  except IOError, e:
    print traceback.format_exc()

    err_message = IOError_messages.get(e.errno)

    if err_message:
      print '%s uploading API Bundle!\nHINT: %s' % (e, err_message)

    return -1

  except Exception, e:
    print traceback.format_exc()
    print e

    return -1

  if resp.status != 200 and resp.status != 201:
    message = HTTP_messages.get(resp.status)

    if not message:
      message = resp.read()

    print 'Import failed to %s with status %i:\nHINT: %s' % (uri, resp.status, message)
    return -1

  deployment = json.load(resp)
  revision = int(deployment['revision'])
  return revision


def deployWithoutConflict(org, env, name, basePath, revision):
  # Deploy the bundle using: seamless_deployments
  print 'Deploying revision %i' % revision
  hdrs = {
    'Accept': 'application/json',
    'Content-type': 'application/x-www-form-urlencoded'
  }
  resp = httptools.httpCall('POST',
    ('/v1/o/%s/environments/%s/apis/%s/revisions/%s/deployments' +
     '?override=true') % \
    (org, env, name, revision), hdrs)

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

