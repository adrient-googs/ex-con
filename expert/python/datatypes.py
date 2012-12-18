from datetime import datetime
from django.utils import simplejson as json
from google.appengine.api import channel
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class Client(db.Model):
  """Client ids that are connected via Channel."""
  id = db.StringProperty(required=True)

  @staticmethod
  def send_global_refresh():
    for client in Client.all():
      channel.send_message(client.id, "refresh")

class Category(db.Model):
  """Represents an expertise category. Name is unique."""
  name = db.StringProperty(required=True)
  
  def __init__(self, *args, **kwargs):
    """Constructor."""
    db.Model.__init__(self, key_name=kwargs['name'], **kwargs)
    
  def get_experts(self):
    """Returns all users associated with this Category."""
    return [pair.user
      for pair in UserToCategory.all().filter('category =', self)]
    
class User(db.Model):
  email = db.StringProperty(required=True)
  user_id = db.StringProperty()
  name = db.StringProperty()
  show = db.StringProperty()
  show_time = db.DateTimeProperty()
  is_available = db.BooleanProperty()
  mute_time = db.DateTimeProperty()
  profile_pic = db.LinkProperty(default='https://teams.googleplex.com/_servlet/data/person_photo?personId=P1004388490')
  plus_page = db.LinkProperty()
  is_subscribed = db.BooleanProperty()
  is_expert = db.BooleanProperty()
  busy_time = db.StringProperty()
  
  def __init__(self, *args, **kwargs):
    """Constructor."""
    key_name = kwargs['email']
    if 'key_name' in kwargs:
      assert kwargs['key_name'] == key_name      
      db.Model.__init__(self, **kwargs)
    else:
      db.Model.__init__(self, key_name=key_name, **kwargs)
    
  def get_categories(self):
    """Returns a list of categories associated with this user."""
    return [pair.category
      for pair in UserToCategory.all().filter('user =', self)]
    
  def add_category(self, category_name):
    """Associates this user with a new category."""
    category = Category.all().filter('name =', category_name).get()
    assert category
    key_name = UserToCategory.get_key_name(self.email, category.name)
    pair = UserToCategory.get_or_insert(key_name, user=self, category=category)
  
  def is_available_for_hangout(self):
    """Returns if the user is available for hangout. Checks if the user is available in chat and is not busy (schedule-wise)."""
    if not self.is_available or not self.busy_time:
      return False
    now = datetime.utcnow().replace(microsecond=0)
    for event in json.loads(self.busy_time):
      if datetime.strptime(event['start'], "%Y-%m-%dT%H:%M:%SZ") < now and datetime.strptime(event['end'], "%Y-%m-%dT%H:%M:%SZ") > now:
        return False
    return True

class UserToCategory(db.Model):
  user = db.ReferenceProperty(User, required=True)
  category = db.ReferenceProperty(Category, required=True)
  detail = db.StringProperty()
  
  def __init__(self, *args, **kwargs):
    """Constructor."""
    # make the user/category pair unique
    user = kwargs['user'] 
    if type(user) == db.Key:
      user = db.get(user)
    assert type(user) == User

    category = kwargs['category']
    if type(category) == db.Key:
      category = db.get(category)
    assert type(category) == Category

    key_name = self.get_key_name(user.email, category.name)
    if 'key_name' in kwargs:
      assert kwargs['key_name'] == key_name
      db.Model.__init__(self, **kwargs)
    else:
      db.Model.__init__(self, key_name=key_name, **kwargs)
    
  @classmethod
  def get_key_name(cls, user_email, category_name):
    return '%s//%s' % (user_email, category_name)
  