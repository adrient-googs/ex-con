
"""
Contains all request handlers for the channel client.
"""

import datetime
import logging

from datatypes import Client
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import xmpp_handlers

class ConnectedHandler(webapp.RequestHandler):
  """Handles a client connecting."""

  def post(self):
    c = Client.get_or_insert(self.request.get('from'), id=self.request.get('from'))

class DisconnectedHandler(webapp.RequestHandler):
  """Handles a client disconnecting."""

  def post(self):
    c = Client.get_by_key_name(self.request.get('from'))
    if c:
      c.delete()

def getHandlers():
  """Returns the handlers defined in this module."""
  return [
    ('/_ah/channel/connected/', ConnectedHandler),
    ('/_ah/channel/disconnected/', DisconnectedHandler),
  ]


