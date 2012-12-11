from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class Category(db.Model):
  """Represents an expertise category. Name is unique."""
  name = db.TextProperty(required=True)
  
  def __init__(self, *args, **kwargs):
    """Constructor."""
    db.Model.__init__(self, key_name=kwargs['name'], **kwargs)
    
class User(db.Model):
  user = db.TextProperty(required=True)
  show = db.TextProperty()
  show_time = db.DateTimeProperty()
  available = db.BooleanProperty()
  mute_time = db.DateTimeProperty()

class UserToCategory(db.Model):
  user = db.TextProperty(required=True)
  category = db.TextProperty(required=True)