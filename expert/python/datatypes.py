from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

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
  name = db.StringProperty()
  show = db.StringProperty()
  show_time = db.DateTimeProperty()
  is_available = db.BooleanProperty()
  mute_time = db.DateTimeProperty()
  profile_pic = db.LinkProperty(default='https://teams.googleplex.com/_servlet/data/person_photo?personId=P1004388490')
  plus_page = db.LinkProperty()
  is_subscribed = db.BooleanProperty()
  is_expert = db.BooleanProperty()
  
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
  