# Copyright 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import logging
import os
import re
import sys
import wsgiref.handlers

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import xmpp
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.ereporter import report_generator
from google.appengine.ext.webapp import template

# include our own libraries from the 'python' path
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))
import admin
import chat
import httplib2
from apiclient.discovery import build
from apiclient.discovery import build_from_document
from datatypes import Category, User, UserToCategory
from oauth2client.appengine import oauth2decorator_from_clientsecrets
from oauth2client.client import AccessTokenRefreshError

DEV_SERVER = os.environ['SERVER_SOFTWARE'].find('Development') >= 0

# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets_installed.json' if DEV_SERVER else 'client_secrets.json')

# Helpful message to display in the browser if the CLIENT_SECRETS file
# is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
<h1>Warning: Please configure OAuth 2.0</h1>
<p>
To make this sample run you will need to populate the client_secrets.json file
found at:
</p>
<p>
<code>%s</code>.
</p>
<p>with information found on the <a
href="https://code.google.com/apis/console">APIs Console</a>.
</p>
""" % CLIENT_SECRETS


http = httplib2.Http(memcache)
# Load the local copy of the discovery document
f = file(os.path.join(os.path.dirname(__file__), "plus.v1whitelisted.rest.json"), "r")
discovery_doc = f.read()
f.close()

service = build_from_document(discovery_doc, base="https://www.googleapis.com/", http=http)
# service = build("plus", "v1", http=http)
# service = build("plus", "dogfood", http=http, discoveryServiceUrl='https://www-googleapis-staging.sandbox.google.com/discovery/v1/apis/plus/dogfood/rest')
decorator = oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/plus.profiles.read https://www.googleapis.com/auth/userinfo.profile',
    message=MISSING_CLIENT_SECRETS_MESSAGE)

class MainHandler(webapp.RequestHandler):
  """Main landing page that shows available experts/categories."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), 'templates', template_file)
    self.response.out.write(template.render(path, template_values))

  def get(self):
    is_expert = False
    user = users.get_current_user()
    if user != None:
      u = User.get_by_key_name(user.email())
      if u != None:
        is_expert = u.is_expert
    categories = []
    for category in Category.all():
      experts = tuple(category.get_experts())
      if experts:
        categories.append((category, experts))
    self.Render("main.html", {
      'column_1': 'expert_list_column_1.html',
      'column_2': 'expert_list_column_2.html',

      'is_expert': is_expert,
      'categories': tuple(categories),
      'login': users.create_login_url("/"),
      'logout': users.create_logout_url("/"),
    })

class ManageAccountHandler(webapp.RequestHandler):
  """Presents an account summary page."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), 'templates', template_file)
    self.response.out.write(template.render(path, template_values))

  @decorator.oauth_required
  def get(self):
    user = users.get_current_user()
    if user == None:
      self.redirect(users.create_login_url("/manageAccount"))
      return
    u = User.get_by_key_name(user.email())
    if u == None:
      self.redirect('/signUp')
    if not u.is_expert:
      try:
        http = decorator.http()
        me = service.people().get(userId='me').execute(http=http)
        logging.error(me)
        if me.get('image') and me['image'].get('url'):          
          u.profile_pic = me['image']['url']
        if me.get('displayName'):
          u.name = me['displayName']
        if me.get('url'):
          u.plus_page = me['url']
        u.is_expert = True
        u.put()
      except AccessTokenRefreshError:
        self.redirect('/manageAccount')
    user_listed_categories = [category.key().name() for category in u.get_categories()]
    template_values = {
      'empty_list': len(user_listed_categories) == 0,
      'user_listed_categories': user_listed_categories,
      'email': user.email(),
      'profile_pic': u.profile_pic,
      'name': u.name,
      'logout': users.create_logout_url("/"),
      'subscribed': u.is_subscribed,
    }
    self.Render("manage_account.html", template_values)

class AddExpertiseHandler(webapp.RequestHandler):
  """Presents a page for the user to sign up for expert categories."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), 'templates', template_file)
    self.response.out.write(template.render(path, template_values))

  @decorator.oauth_required
  def get(self):
    user = users.get_current_user()
    if user == None:
      self.redirect(users.create_login_url("/manageAccount"))
      return
    u = User.get_by_key_name(user.email())
    if u == None:
      self.redirect(users.create_login_url("/manageAccount"))
      return
    user_listed_categories = [category.key().name() for category in u.get_categories()]
    all_categories = [{'checked': category.key().name() in user_listed_categories, 'name': category.name} for category in Category.all().fetch(100)]
    template_values = {
      'all_categories': all_categories,
      'email': user.email(),
      'profile_pic': u.profile_pic,
      'name': u.name,
      'logout': users.create_logout_url("/"),
      'subscribed': u.is_subscribed,
    }
    self.Render("add_expertise.html", template_values)
    
  def post(self):
    user = users.get_current_user()
    if user == None:
      self.redirect(users.create_login_url("/manageAccount"))
      return
    u = User.get_by_key_name(user.email())
    if u == None:
      u = User(email=user.email())
      u.put()
    utoc = UserToCategory.all()
    utoc.filter("user =", u)
    for existing_utoc in utoc.fetch(100):
      existing_utoc.delete()
    for category in Category.all().fetch(100):
      if self.request.get(category.name) == 'true':
        u.add_category(category.name)
    self.redirect("/manageAccount")

class ConnectHandler(webapp.RequestHandler):
  """Connects the user in the webapp to expert."""

  def get(self):
    user = self.request.get('user')
    u = User.get_by_key_name(user)
    if u == None or not u.is_expert:
        self.response.out.write("<html><body><p>No such user</p></body></html>")
        logging.error('Connect request to invalid user/expert ' + user)
    url = 'https://plus.google.com/hangouts/_/2e3e57ff748dd2c7c79e1c40c274cca933a8d984?authuser=0&hl=en-US'
    xmpp.send_message(u.email, chat.REQUEST_MSG % (url,))
    self.redirect(url)

class SignUpHandler(webapp.RequestHandler):
  """Sign up page for users to become an expert."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), 'templates', template_file)
    self.response.out.write(template.render(path, template_values))

  @decorator.oauth_aware
  def get(self):
    user = users.get_current_user()
    if user == None:
      self.redirect(users.create_login_url("/signUp"))
      return
    u = User.get_by_key_name(user.email())
    if u == None:
      u = User(email=user.email())
      u.put()
    template_values = {
      'url': decorator.authorize_url(),
      'has_credentials': decorator.has_credentials()
    }
    self.Render("sign_up.html", template_values)

class SendInviteHandler(webapp.RequestHandler):
  """Sends an invite to the user account."""

  def get(self):
    user = users.get_current_user()
    if user == None:
      self.redirect(users.create_login_url("/signUp"))
      return
    xmpp.send_invite(user.email())
    self.redirect("/signUp")

def main():
  handlers = [
      ('/', MainHandler),
      ('/connect', ConnectHandler),
      ('/manageAccount', ManageAccountHandler),
      ('/manageAccount/addExpertise', AddExpertiseHandler),
      ('/sendInvite', SendInviteHandler),
      ('/signUp', SignUpHandler),
      (decorator.callback_path, decorator.callback_handler()),
  ]
  for module in (admin, chat):
    handlers += module.getHandlers()
  app = webapp.WSGIApplication(handlers, debug=True)
  wsgiref.handlers.CGIHandler().run(app)

if __name__ == '__main__':
  main()
