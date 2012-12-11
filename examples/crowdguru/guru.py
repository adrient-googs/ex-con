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
from datatypes import Category, User, UserToCategory

class LatestHandler(webapp.RequestHandler):
  """Displays the most recently answered questions."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), 'templates', template_file)
    self.response.out.write(template.render(path, template_values))

  def get(self):
    self.Render("latest.html", {})

class ManageAccountHandler(webapp.RequestHandler):
  """Presents a page for the user to sign up for expert categories."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), 'templates', template_file)
    self.response.out.write(template.render(path, template_values))

  def get(self):
    c = Category.all()
    template_values = {
      'categories': c.fetch(100)
    }
    self.Render("manage_account.html", template_values)

class ConnectHandler(webapp.RequestHandler):
  """Connects the user in the webapp to expert."""

  def get(self):
    user = self.request.get('user')
    u = User.get_by_key_name(user)
    if u == None:
        self.response.out.write("<html><body><p>No such user</p></body></html>")
        logging.error('Connect request to invalid user ' + user)
    url = 'https://plus.google.com/hangouts/_/2e3e57ff748dd2c7c79e1c40c274cca933a8d984?authuser=0&hl=en-US'
    xmpp.send_message(u.user, REQUEST_MSG % (url,))
    self.redirect(url)

def main():
  handlers = [
      ('/', LatestHandler),
      ('/manageAccount', ManageAccountHandler),
      ('/connect', ConnectHandler),
  ]
  for module in (admin, chat):
    handlers += module.getHandlers()
  app = webapp.WSGIApplication(handlers, debug=True)
  wsgiref.handlers.CGIHandler().run(app)

if __name__ == '__main__':
  main()
