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
from google.appengine.dist import use_library
use_library('django', '1.2')

import datetime
import logging
import os
import re
import sys
import wsgiref.handlers

from datetime import datetime, timedelta
from django.utils import simplejson as json
from google.appengine.api import channel
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import xmpp
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.ereporter import report_generator
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required

# include our own libraries from the 'python' path
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))
import admin
import chat
import client
import httplib2
from apiclient.discovery import build
from apiclient.discovery import build_from_document
from datatypes import Category, Client, HangoutStats, User, AreaOfExpertise
from oauth2client.appengine import oauth2decorator_from_clientsecrets, CredentialsModel, StorageByKeyName
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
calendar_service = build("calendar", "v3", http=http)
# service = build("plus", "dogfood", http=http, discoveryServiceUrl='https://www-googleapis-staging.sandbox.google.com/discovery/v1/apis/plus/dogfood/rest')
decorator = oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/plus.profiles.read https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.readonly',
    message=MISSING_CLIENT_SECRETS_MESSAGE)

def user_required(method):
  """Decorator for making sure the User entity is created for the user"""

  def _user_required(request_handler):
    user = users.get_current_user()
    u = User.get_by_key_name(user.email())
    if not u:
      u = User(email=user.email(),user_id=user.user_id())
      u.put()
    method(request_handler)
  
  return _user_required

class MainHandler(webapp.RequestHandler):
  """Main landing page that shows available experts/categories."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), 'templates', template_file)
    logging.info(path)
    logging.info(template_values)
    # self.render_template(path, template_values)
    self.response.out.write(template.render(path, template_values))

  @login_required
  @user_required
  def get(self):
    user = users.get_current_user()
    u = User.get_by_key_name(user.email())
    categories = []
    suggestions = set()
    for category in Category.all():
      areas = category.get_areas_of_expertise()
      if areas:
        area_data = [{
          'user_name' : area.user.get_name(),
          'user_email' : area.user.email,
          'user_profile_pic' : area.user.profile_pic,
          'user_available' : area.user.is_available_for_hangout(),
          'description' : area.description.title(),
        } for area in areas if area.user.is_expert]
        for area in areas:
          suggestions.add(category.name.title() + ' :: ' + area.description.title())
        if area_data:
          categories.append({'name':category.name, 'areas':area_data})
    self.Render("main.html", {
      'user': u,
      'validate': u.validate(),
      'contents': 'expert_list.html',
      'token': channel.create_channel(user.user_id()),
      'is_expert': u.is_expert,
      'categories': categories,
      'suggestions': [suggestion for suggestion in suggestions],
      'login': users.create_login_url("/"),
      'logout': users.create_logout_url("/"),
      'is_admin': users.is_current_user_admin(),
    })

class AddExpertiseHandler(webapp.RequestHandler):
  """Presents a page for the user to sign up for expert categories."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), 'templates', template_file)    
    self.response.out.write(template.render(path, template_values))

  @decorator.oauth_required
  @user_required
  def get(self):
    user = users.get_current_user()
    u = User.get_by_key_name(user.email())
    if not u.is_expert and not u.convert_to_expert(service, calendar_service, decorator):
      # Token access error. Go back to sign up page and restart flow
      self.redirect('/signUp')
      return
        
    # get the areas of expertise for this user
    user_areas = u.get_areas_of_expertise()
    # user_areas_dict = dict((area.category.name, area) for area in user_areas)
    # 
    # # construct a data structure of all categories
    # all_categories = []
    # for category in Category.all():
    #   category_data = {
    #     'checked': False,
    #     'name': category.name,
    #     'description': category.name,      
    #   }
    #   if category.name in user_areas_dict:
    #     category_data['checked'] = True
    #     category_data['description'] = \
    #       user_areas_dict[category.name].description
    #   all_categories.append(category_data)
      
    suggestions = set()
    for category in Category.all():
      for area in category.get_areas_of_expertise():
        suggestions.add(category.name.title() + ' :: ' + area.description.title())

    # this is what we pass to the templating engine
    template_values = {
      # 'all_categories': all_categories,
      'suggestions': [suggestion for suggestion in suggestions],
      'user_categories': [(area.category.name.title(), area.category.name.title() + ' :: ' + area.description.title()) for area in user_areas],
      'user': u,
      'validate': u.validate(),
      'logout': users.create_logout_url("/"),
      'contents': 'add_expertise.html',
      'is_expert': u.is_expert,
      'is_admin': users.is_current_user_admin(),
    }
    self.Render('main.html', template_values)
    
  def post(self):
    # figure out the current user
    user = users.get_current_user()
    if user == None:
      self.redirect(users.create_login_url("/manageAccount"))
      return
    u = User.get_by_key_name(user.email())
    if u == None:
      self.redirect(users.create_login_url("/signUp"))
      return
      
    # add all the existing categories
    area = AreaOfExpertise.all()
    area.filter("user =", u)
    for existing_area in area.fetch(100):
      existing_area.delete()

    u.expert_opt_out = self.request.get("expertoptout") != "true"
    u.put()
    
    for category_subcategory in self.request.get_all("usercategory"):
      if category_subcategory and category_subcategory != "" and re.search("\s::\s", category_subcategory):
        match = re.search("\s::\s", category_subcategory)
        category_name = category_subcategory[0:match.start(0)].lower()
        subcategory = category_subcategory[match.end(0):].lower()
        if not Category.get_by_key_name(category_name):
          category = Category(name=category_name)
          category.put()
        u.add_category(category_name, subcategory)
      
        
    # for param in self.request.arguments():
    #   value = self.request.get(param)
    #   if param == "expertoptout":
    #     u.expert_opt_out = self.request.get("expertoptout") != "true"
    #     u.put()
    #   elif not re.search(" description$", param) and value == "true":
    #     if not Category.get_by_key_name(param):
    #       c = Category(name=param)
    #       c.put()
    #     description = self.request.get('%s description' % param)
    #     logging.error(param + " :: " + description)
    #     u.add_category(param, description)

    # for category in Category.all().fetch(100):
    #    if self.request.get(category.name) == 'true':
    #      description = self.request.get('%s description' % category.name)
    #      u.add_category(category.name, description)
         
    # # add the other category
    # other_category = self.request.get("other").lower()
    # if other_category and other_category != "" and other_category != "other":
    #   # Disallow empty category names and the "other" category name
    #   if not Category.get_by_key_name(other_category):
    #     category = Category(name=other_category)
    #     category.put()
    #   u.add_category(other_category, other_category)
    
    # add_category = self.request.get("addcategory").lower()
    # if add_category and add_category != "" and re.search("\s::\s", add_category):
    #   match = re.search("\s::\s", add_category)
    #   category_name = add_category[0:match.start(0)]
    #   subcategory = add_category[match.end(0):]
    #   if not Category.get_by_key_name(category_name):
    #     category = Category(name=category_name)
    #     category.put()
    #   u.add_category(category_name, subcategory)
    
    # do the opt out stuff
    self.redirect("/")

class ConnectHandler(webapp.RequestHandler):
  """Connects the user in the self.response.write to expert."""

  @login_required
  def get(self):
    user = self.request.get('user')
    category = self.request.get('category')
    u = User.get_by_key_name(user)
    if u == None or not u.validate() or not u.is_available_for_hangout():
      logging.error('Connect request to invalid and/or unavailable user/expert ' + user)
      self.redirect('/')
      return
    c = Category.get_by_key_name(category.lower())
    if not c:
      logging.error('Connect request with invalid category key: ' + category.lower())
      self.redirect('/')
      return
    url = HangoutStats.get_hangout_url()
    logging.info('Hangout url: %s in category %s' % (url, category))
    xmpp.send_message(u.email, chat.REQUEST_MSG % (category, url))
    for email in ['karishmashah@google.com', 'charleschen@google.com', 'adrient@google.com']:
      u = User.get_by_key_name(email)
      if u and u.is_subscribed:
        xmpp.send_message(email, chat.FACILITATOR_MSG % (category, url))
    self.redirect(url)

class SignUpHandler(webapp.RequestHandler):
  """Sign up page for users to become an expert."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), 'templates', template_file)
    self.response.out.write(template.render(path, template_values))

  @decorator.oauth_aware
  @user_required
  def get(self):
    user = users.get_current_user()
    u = User.get_by_key_name(user.email())
    template_values = {
      'user': u,
      'validate': u.validate(),
      'url': decorator.authorize_url(),
      'has_credentials': decorator.has_credentials(),
      'contents': 'sign_up.html',
    }
    self.Render('main.html', template_values)

class SendInviteHandler(webapp.RequestHandler):
  """Sends an invite to the user account."""

  @login_required
  @user_required
  def get(self):
    user = users.get_current_user()
    xmpp.send_invite(user.email())
    self.redirect("/signUp")

class CalendarCronHandler(webapp.RequestHandler):
  """For each expert, refresh calendar busy_time."""

  def get(self):
    for u in User.all().fetch(1000):
      u.update_calendar(calendar_service)

def main():
  handlers = [
      ('/', MainHandler),
      ('/admin/calendarCron', CalendarCronHandler),
      ('/connect', ConnectHandler),
      ('/manageAccount', AddExpertiseHandler),
      ('/sendInvite', SendInviteHandler),
      ('/signUp', SignUpHandler),
      (decorator.callback_path, decorator.callback_handler()),
  ]
  for module in (admin, chat, client):
    handlers += module.getHandlers()
  app = webapp.WSGIApplication(handlers, debug=True)
  wsgiref.handlers.CGIHandler().run(app)

if __name__ == '__main__':
  main()
