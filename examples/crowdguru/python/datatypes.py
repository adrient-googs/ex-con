from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class Category(db.Model):
  """Represents an expertise category. Name is unique."""
  name = db.StringProperty(required=True)
  
  def __init__(self, *args, **kwargs):
    """Constructor."""
    db.Model.__init__(self, key_name=kwargs['name'], **kwargs)
    
class User(db.Model):
  email = db.StringProperty(required=True)
  show = db.StringProperty()
  show_time = db.DateTimeProperty()
  available = db.BooleanProperty()
  mute_time = db.DateTimeProperty()
  
  def __init__(self, *args, **kwargs):
    """Constructor."""
    db.Model.__init__(self, key_name=kwargs['email'], **kwargs)

class UserToCategory(db.Model):
  user = db.ReferenceProperty(User, required=True)
  category = db.ReferenceProperty(Category, required=True)  
  
  def __init__(self, *args, **kwargs):
    """Constructor."""
    # make the user/category pair unique
    key_name = '%s//%s' % (kwargs['user'].key(), kwargs['category'].key())
    
    db.Model.__init__(self, key_name=key_name, **kwargs)
  