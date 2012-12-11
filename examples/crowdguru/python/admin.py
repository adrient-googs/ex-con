"""
Contains all the request handlers for administrative control of the
app.
"""

import os

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import handlers
from datatypes import Category, User, UserToCategory

class AdminHandler(webapp.RequestHandler):
  """Show the user a bunch of admin options."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), '../templates', template_file)
    self.response.out.write(template.render(path, template_values))

  def get(self):
    self.Render('admin.html', ())

@handlers.text_handler
def addDefaultCategories(out):
 DEFAULT_CATEGORIES = [
   'computer help', 'cooking', 'homework', 'romance', 'appliance repair',
   'fitness', 'games', 'beauty and fashion', 'arts and crafts', 'handyman',
   'employment', 'finance', 'translate', 'programming', 'pets', 'household',
   'gardening', 'cars', 'religion', 'parenting', 'outdoors', 'legal', 'hardware']
 existing_categories = {category.name for category in Category.all()}
 for category_name in DEFAULT_CATEGORIES:
   if category_name in existing_categories:
     out.write('% 20s - already exists\n' % category_name)
   else:
     category = Category(name=category_name)
     category.put()
     out.write('% 20s - created!\n' % category_name)
     
@handlers.text_handler
def addDefaultUsers(out):
  """Adds a bunch of users to the system."""


        
def getHandlers():
  """Returns the handlers defined in this module."""
  return [
    ('/admin/admin', AdminHandler),
    ('/admin/addDefaultCategories', addDefaultCategories),
    ('/admin/addDefaultUsers', addDefaultUsers),
  ]
  