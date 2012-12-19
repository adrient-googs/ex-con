"""
Contains all request handlers for chat.
"""

import datetime
import logging

from datatypes import Category, Client, User, AreaOfExpertise
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import xmpp_handlers

MUTE_MSG = "You have muted ExpertConnect for one hour."
REQUEST_MSG = "Your expertise is needed! Please click on the following link: %s"
FACILITATOR_MSG = "A hangout is in progress. Watch the hangout via the following link: %s"
HELP_MSG = "Manage your account at %s/manageAccount"

class XmppHandler(xmpp_handlers.CommandHandler):
  """Handler class for all XMPP activity."""

  def unhandled_command(self, message=None):
    # Show help text
    message.reply(HELP_MSG % (self.request.host_url,))

  # def mute_command(self, message=None):
  #   u = User.get_or_insert(message.sender)
  #   u.mute_time = datetime.datetime.now()
  #   u.put()
  #   message.reply(MUTE_MSG)

  def text_message(self, message=None):
    # Show help text
    message.reply(HELP_MSG % (self.request.host_url,))

class XmppSubscribeHandler(webapp.RequestHandler):
  """Handles a user subscription."""

  def post(self):
    sender = self.request.get('from').split('/')[0]
    logging.info('User subscribe ' + sender)
    logging.info('stanza ' + self.request.get('stanza'))
    
class XmppUnsubscribeHandler(webapp.RequestHandler):
  """Handles a user unsubscription."""

  def post(self):
    sender = self.request.get('from').split('/')[0]
    logging.info('User unsubscribe ' + sender)
    logging.info('stanza ' + self.request.get('stanza'))

class XmppSubscribedHandler(webapp.RequestHandler):
  """Handles a user subscription."""

  def post(self):
    sender = self.request.get('from').split('/')[0]
    u = User.get_by_key_name(sender)
    if u == None:
      u = User(email=sender)
    u.is_subscribed = True
    u.put()
    logging.info('User subscribed ' + sender)
    logging.info('stanza ' + self.request.get('stanza'))
    
class XmppUnsubscribedHandler(webapp.RequestHandler):
  """Handles a user unsubscription."""

  def post(self):
    sender = self.request.get('from').split('/')[0]
    logging.info('User unsubscribed ' + sender)
    logging.info('stanza ' + self.request.get('stanza'))

class XmppAvailableHandler(webapp.RequestHandler):
  """Handles if a user is available."""

  def post(self):
    sender = self.request.get('from').split('/')[0]
    u = User.get_by_key_name(sender)
    if u == None:
      u = User(email=sender)
    previously_available = u.is_available
    u.show = self.request.get('show')
    u.show_time = datetime.datetime.now()
    u.is_available = True
    u.put()
    if not previously_available:
      Client.send_global_refresh()
    logging.info('User available ' + sender)
    logging.info('stanza ' + self.request.get('stanza'))
    logging.info('show ' + self.request.get('show'))

class XmppUnavailableHandler(webapp.RequestHandler):
  """Handles if a user is unavailable."""

  def post(self):
    sender = self.request.get('from').split('/')[0]
    u = User.get_by_key_name(sender)
    if u == None:
      u = User(email=sender)
    previously_available = u.is_available
    u.is_available = False
    u.put()
    if previously_available:
      Client.send_global_refresh()
    logging.info('User unavailable ' + sender)
    logging.info('stanza ' + self.request.get('stanza'))

class XmppProbeHandler(webapp.RequestHandler):
  """Handles if a user is probing the appengine."""

  def post(self):
    sender = self.request.get('from').split('/')[0]
    logging.info('User probe ' + sender)
    logging.info('stanza ' + self.request.get('stanza'))

class XmppErrorHandler(webapp.RequestHandler):
  """Handles xmpp errors."""

  def post(self):
    error_sender = self.request.get('from')
    error_stanza = self.request.get('stanza')
    logging.error('XMPP error received from %s (%s)', error_sender, error_stanza)

def getHandlers():
  """Returns the handlers defined in this module."""
  return [
    ('/_ah/xmpp/error/', XmppErrorHandler),
    ('/_ah/xmpp/message/chat/', XmppHandler),
    ('/_ah/xmpp/subscription/subscribe/', XmppSubscribeHandler),
    ('/_ah/xmpp/subscription/subscribed/', XmppSubscribedHandler),
    ('/_ah/xmpp/subscription/unsubscribe/', XmppUnsubscribeHandler), # unused
    ('/_ah/xmpp/subscription/unsubscribed/', XmppUnsubscribedHandler), # unused
    ('/_ah/xmpp/presence/available/', XmppAvailableHandler),
    ('/_ah/xmpp/presence/unavailable/', XmppUnavailableHandler),
    ('/_ah/xmpp/presence/probe/', XmppProbeHandler),
  ]
