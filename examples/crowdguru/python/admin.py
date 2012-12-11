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
    template_values = {
      'adminFuncs' : ADMIN_FUNCS,
    }
    self.Render('admin.html', template_values)

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
def tryAddingTwoOfTheSameCategory(out):
  """Test out adding two of the same category to make sure that it's unique."""
  category_name = 'cooking'

  def printAllWithName():
    """Prints all categoires with name category_name."""
    out.write('Getting all categories with name "%s."\n' % category_name)
    categories = Category.all().filter('name =', category_name).fetch(limit=100)
    # categories = Category.all().fetch(limit=100)
    for ii, category in enumerate(categories):
      if ii % 222 == 1:
        continue
      out.write(' %.2i - "%s"\n' % (ii, category.name))
    out.write('Found %i categories.\n' % len(categories))    
  
  printAllWithName()  
  for ii in xrange(10):
    new_category = Category(name=category_name)
    new_category.put()
    out.write('Put new category name=%s key=%s.\n' % (new_category.name, new_category.key()))
  printAllWithName()
  if len(Category.all().filter('name =', category_name).fetch(limit=100)) == 1:
    out.write('TEST PASSED\n')
  else:
    out.write('TEST FAILED\n')
     
@handlers.text_handler
def addDefaultUsers(out):
  """Adds a bunch of users to the system."""
  pass

# This is is a list of functions which the administrator can call.
ADMIN_FUNCS = (
  ('addDefaultCategories',          'Add some default categories'),
  ('tryAddingTwoOfTheSameCategory', 'Run a test to verify that catgories are unique'),
  ('addDefaultUsers',               'Adds Karishma, Charles, and Adrien as users'),
)
        
def getHandlers():
  """Returns the handlers defined in this module."""
  handlers = [('/admin', AdminHandler)]
  for name, description in ADMIN_FUNCS:
    handlers.append(('/admin/%s' % name, globals()[name]))
  return handlers
  