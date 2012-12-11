"""
Contains all the request handlers for administrative control of the
app.
"""

import os

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from datatypes import Category, User, UserToCategory

class AdminHandler(webapp.RequestHandler):
  """Show the user a bunch of admin options."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), '../templates', template_file)
    self.response.out.write(template.render(path, template_values))

  def get(self):
    # c = Category.all()
    # template_values = {
    #   'categories': c.fetch(20)
    # }
    self.Render('admin.html', ())
    
class AdminAddDefaultCategories(webapp.RequestHandler):
  """Create a set of default categories."""

  def get(self):
    DEFAULT_CATEGORIES = [
      'computer help', 'cooking', 'homework', 'romance', 'appliance repair',
      'fitness', 'games', 'beauty and fashion', 'arts and crafts', 'handyman',
      'employment', 'finance', 'translate', 'programming', 'pets', 'household',
      'gardening', 'cars', 'religion', 'parenting', 'outdoors', 'legal', 'hardware']
    
    self.response.headers['Content-Type'] = 'text/plain'

    existing_categories = {category.name for category in Category.all()}
    for category_name in DEFAULT_CATEGORIES:
      if category_name in existing_categories:
        self.response.out.write('% 20s - already exists\n' % category_name)
      else:
        category = Category(name=category_name)
        category.put()
        self.response.out.write('% 20s - created!\n' % category_name)
        
def getHandlers():
  """Returns the handlers defined in this module."""
  return [
    ('/admin/admin', AdminHandler),
    ('/admin/addDefaultCategories', AdminAddDefaultCategories),
  ]
  