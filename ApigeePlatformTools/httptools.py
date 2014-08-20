import base64
import httplib
import urlparse
import os

opts = {}


def setup(u, username, password):
  url = urlparse.urlparse(u) 
  opts['httpScheme'] = url[0]
  opts['httpHost'] = url[1]
  opts['userPW'] = base64.b64encode('%s:%s' % (username, password))


def httpCall(verb, uri, headers = None, body = None):
  conn = _connect()
  if headers == None:
    hdrs = dict()
  else:
    hdrs = headers
  hdrs['Authorization'] = 'Basic %s' % opts['userPW']
  hdrs['Accept'] = 'application/json'
  url = "%(httpScheme)s://%(httpHost)s%(path)s" % dict(opts, path=uri)
  conn.request(verb, url, body, hdrs)
  return conn.getresponse()


def _connect():
  proxy = _getProxy(opts['httpScheme'])
  host = (opts['httpHost'],)
  if proxy:
    real_host = host
    host = proxy
  if opts['httpScheme'] == 'https':
    conn = httplib.HTTPSConnection(*host)
  else:
    conn = httplib.HTTPConnection(*host)
  if proxy:
    conn.set_tunnel(*real_host)
  return conn


def _getProxy(scheme):
  """Reads proxy from environment"""
  try:
    proxy = os.environ[scheme + "_proxy"]
    parts = proxy.split(":")
    port = int(parts[-1]) if parts[-1].isdigit() else None
    host = (parts[-2] if port else parts[-1]).strip("/")
    return host, port
  except KeyError:
    return ()
