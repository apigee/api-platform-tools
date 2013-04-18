import base64;
import httplib;
import urlparse;

opts = {}

def setup(u, username, password):
  url = urlparse.urlparse(u) 
  opts['httpScheme'] = url[0]
  opts['httpHost'] = url[1]
  opts['userPW'] = base64.b64encode('%s:%s' % (username, password))

def httpCall(verb, uri, headers = None, body = None):
  if opts['httpScheme'] == 'https':
    conn = httplib.HTTPSConnection(opts['httpHost'])
  else:
    conn = httplib.HTTPConnection(opts['httpHost'])
  if headers == None:
    hdrs = dict()
  else:
    hdrs = headers
  hdrs['Authorization'] = 'Basic %s' % opts['userPW']
  hdrs['Accept'] = 'application/json'
  conn.request(verb, uri, body, hdrs)
  return conn.getresponse()
  
