"""
Contains all the request handlers for administrative control of the
app.
"""

import csv
import logging
import os

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import handlers
from datatypes import Category, User, AreaOfExpertise

class AdminHandler(webapp.RequestHandler):
  """Show the user a bunch of admin options."""

  def Render(self, template_file, template_values):
    path = os.path.join(os.path.dirname(__file__), '../templates', template_file)
    self.response.out.write(template.render(path, template_values))

  def get(self):
    template_values = {
      'contents': 'admin.html',
      'adminFuncs' : ADMIN_FUNCS,
    }
    self.Render('main.html', template_values)

@handlers.text_handler
def addDefaultCategories(out):
  """Adds default categories for the appengine datastore."""
  DEFAULT_CATEGORIES = [
    'computer help', 'cooking', 'homework', 'romance', 'appliance repair',
    'fitness', 'games', 'beauty and fashion', 'arts and crafts', 'handyman',
    'employment', 'finance', 'translate', 'programming', 'pets', 'household',
    'gardening', 'cars', 'religion', 'parenting', 'outdoors', 'legal', 'hardware']

  # existing_categories = {category.name for category in Category.all().fetch(limit=100)}
  for category_name in DEFAULT_CATEGORIES:
     # if category_name in existing_categories:
     #   out.write('% 20s - already exists\n' % category_name)
     # else:
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
    
  def putNewWithName():
    """Puts in a new category with name = category_name"""
    new_category = Category(name=category_name)
    new_category.put()
    out.write('Put new category name=%s key=%s.\n' % (new_category.name, new_category.key()))

  # add two wtih the same name
  printAllWithName()  
  putNewWithName()
  putNewWithName()
  printAllWithName()

  # make sure that they're not separately in the datastore
  if len(Category.all().filter('name =', category_name).fetch(limit=100)) == 1:
    out.write('TEST PASSED\n')
  else:
    out.write('TEST FAILED\n')
     
@handlers.text_handler
def addDefaultUsers(out):
  """Adds a bunch of users to the system."""
  new_users = [
    ('charleschen@google.com', "https://teams.googleplex.com/_servlet/data/person_photo?personId=P791347397"),
    ('karishmashah@google.com', 'https://teams.googleplex.com/_servlet/data/person_photo?personId=P1064040024'),
    ('adrient@google.com', 'https://teams.googleplex.com/_servlet/data/person_photo?personId=P1004388490'),
  ]
  for new_email, profile_pic in new_users:
    new_user = User.get_or_insert(new_email, email=new_email)
    out.write('adding new user: %s / %s\n' % (new_email, profile_pic))
    new_user.profile_pic = profile_pic
    new_user.is_available = True
    new_user.busy_time = '[]'
    new_user.put()
    # out.write('Got user "%s"\n' % new_user.email)
    # out.write('Added profile pic: "%s"\n' % new_user.profile_pic)
    new_user.add_category('cooking', 'fake cooking description')
    # for category in new_user.get_categories():
    #   out.write(' - %s\n' % category.name)

@handlers.text_handler
def addSourcedExperts(out):
  """Adds a bunch of experts to the system."""
  with open(os.path.join(os.path.dirname(__file__), 'sourced_experts.csv'), 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        logging.error(row)

@handlers.text_handler
def quickDisplayCategories(out):
  """Displays all the categories."""
  for category in Category.all():
    out.write('- %s\n' % category.name)
    for user in category.get_experts():
      out.write('  - %s\n' % user.email)
      
@handlers.text_handler
def removeAllAreasOfExpertise(out):
  """Removes all the areas of expertise."""
  for area in AreaOfExpertise.all():
    out.write('deleting:\n')
    out.write('  key : %s' % area.key)
    # out.write('  user: %s')
     

# This is is a list of functions which the administrator can call.
ADMIN_FUNCS = (
  ('addDefaultCategories',          'Add some default categories'),
  ('tryAddingTwoOfTheSameCategory', 'Run a test to verify that catgories are unique'),
  ('addDefaultUsers',               'Add Karishma, Charles, and Adrien as users'),
  ('addSourcedExperts',             'Add sourced experts as users'),
  ('quickDisplayCategories',        'Displays all categories'),
  ('removeAllAreasOfExpertise',     'Remove all areas of expertise (CAUTION)'),
)
        
def getHandlers():
  """Returns the handlers defined in this module."""
  handlers = [('/admin', AdminHandler)]
  for name, description in ADMIN_FUNCS:
    handlers.append(('/admin/%s' % name, globals()[name]))
  return handlers
  