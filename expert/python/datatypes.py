import httplib2
import logging

from datetime import datetime, timedelta
from django.utils import simplejson as json
from google.appengine.api import channel
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from oauth2client.client import AccessTokenRefreshError
from oauth2client.appengine import CredentialsModel, StorageByKeyName

class HangoutStats(db.Model):
  """Keeps a summary of the hangout stats"""
  counter = db.IntegerProperty(default=0)
  
  @staticmethod
  @db.transactional
  def get_hangout_url():
      hangout_stats = HangoutStats.get_by_key_name("singleton")
      if not hangout_stats:
        hangout_stats = HangoutStats(key_name="singleton")
      hangout_stats.counter += 1
      hangout_stats.put()
      return "http://plus.google.com/hangouts/_/event/xoncall" + str(hangout_stats.counter)
  
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
    """Returns all expert users associated with this Category."""
    return [area.user
      for area in self.get_areas_of_expertise() if area.user.is_expert]

  def get_areas_of_expertise(self):
    """Returns all the areas of expertise associated with this category."""
    return [area for area in AreaOfExpertise.all().filter('category =', self)]
    
class User(db.Model):
  email = db.StringProperty(required=True)
  user_id = db.StringProperty()
  name = db.StringProperty()
  show = db.StringProperty()
  show_time = db.DateTimeProperty()
  is_available = db.BooleanProperty()
  mute_time = db.DateTimeProperty()
  profile_pic = db.LinkProperty(default='http://ssl.gstatic.com/s2/profiles/images/silhouette80.png')
  plus_page = db.LinkProperty()
  is_subscribed = db.BooleanProperty()
  is_expert = db.BooleanProperty()
  busy_time = db.StringProperty(default="[]") # Assign a default empty array which means by default they have a free schedule.
  expert_opt_out = db.BooleanProperty()
  # account_state = db.StringProperty(required=True, choices=set(["chat", "user", "expert"]))
  
  def __init__(self, *args, **kwargs):
    """Constructor."""
    key_name = kwargs['email']
    if 'key_name' in kwargs:
      assert kwargs['key_name'] == key_name      
      db.Model.__init__(self, **kwargs)
    else:
      db.Model.__init__(self, key_name=key_name, **kwargs)
    
  def get_areas_of_expertise(self):
    """Returns a list of this users areas of expertise."""
    return [area for area in AreaOfExpertise.all().filter('user =', self).fetch(100)]
  
  def get_categories(self):
    """Returns a list of categories associated with this user."""
    return [area.category for area in get_areas_of_expertise()]

  def validate(self):
    """Validates the User entity."""
    if self.user_id and self.is_expert and self.is_subscribed:
      credentials = StorageByKeyName(
        CredentialsModel, self.user_id, 'credentials').get()
      if not credentials or credentials.invalid:
        logging.error("Credentials unavailable/invalid for %s" % self.email)
        return False
      # Credentials are valid
      return True
    elif self.is_expert:
      # No user_id and isn't subscribed
      return False
    else:
      # Not an expert so account state is okay no matter what
      return True

  def convert_to_expert(self, service, calendar_service, decorator):
    """Converts this user to an expert"""
    if not self.is_expert:
      try:
        http = decorator.http()
        # Query the plus service for the user's name, profile picture, and profile url
        me = service.people().get(userId='me').execute(http=http)
        logging.info(me)
        if me.get('image') and me['image'].get('url'):          
          self.profile_pic = me['image']['url']
        if me.get('displayName'):
          self.name = me['displayName']
        if me.get('url'):
          self.plus_page = me['url']
        self.is_expert = True

        # Query the calendar service for the user's busy schedule
        email = self.email
        now = datetime.utcnow().replace(microsecond=0)
        tomorrow = now + timedelta(days=1)
        body = {}
        body['timeMax'] = tomorrow.isoformat() + 'Z'
        body['timeMin'] = now.isoformat() + 'Z'
        body['items'] = [{'id': email}]
        response = calendar_service.freebusy().query(body=body).execute(http=http)
        logging.info(response)
        if response.get('calendars') and response['calendars'].get(email) and response['calendars'][email].get('busy') and not response['calendars'][email].get('errors'):
          # Store the busy schedule
          logging.info('storing busy schedule')
          self.busy_time = json.dumps(response['calendars'][email]['busy'])
        self.put()
        return True
      except AccessTokenRefreshError:
        return False
    return False

  def update_calendar(self, calendar_service):
    """Updates the user's calendar"""
    # Check if this user is an expert and has an id
    if self.user_id and self.is_expert:
      credentials = StorageByKeyName(
        CredentialsModel, self.user_id, 'credentials').get()
      if credentials is not None:
        if credentials.invalid:
          logging.error("Credentials invalid for %s" % self.email)
          # return
        try:
          email = self.email
          # Authorize takes care of refreshing an expired token
          http = credentials.authorize(httplib2.Http())
          now = datetime.utcnow().replace(microsecond=0)
          tomorrow = now + timedelta(days=1)
          body = {}
          body['timeMax'] = tomorrow.isoformat() + 'Z'
          body['timeMin'] = now.isoformat() + 'Z'
          body['items'] = [{'id': email}]
          response = calendar_service.freebusy().query(body=body).execute(http=http)
          logging.info(response)
          if response.get('calendars') and response['calendars'].get(email) and response['calendars'][email].get('busy') and not response['calendars'][email].get('errors'):
            # Store the busy schedule
            logging.info('storing busy schedule')
            self.busy_time = json.dumps(response['calendars'][email]['busy'])
            self.put()
        except AccessTokenRefreshError:
          logging.error('AccessTokenRefreshError for user id ' + self.user_id)            

  # Transactional query so get/put operations see most recently written data
  @db.transactional(xg=True)
  def add_category(self, category_name, category_description):
    """Associates this user with a new category."""
    category = Category.get_by_key_name(category_name)
    assert category
    key_name = AreaOfExpertise.get_key_name(self.email, category.name)
    if not AreaOfExpertise.get_by_key_name(key_name):
      aoe = AreaOfExpertise(key_name=key_name, user=self,
        category=category, description=category_description)
      aoe.put()
    # pair = AreaOfExpertise.get_or_insert(key_name, user=self,
    #   category=category, description=category_description)
  
  def is_available_for_hangout(self):
    """Returns if the user is available for hangout. Checks if the user is available in chat and is not busy (schedule-wise)."""
    if not self.is_expert or not self.is_subscribed or not self.is_available or not self.busy_time or self.expert_opt_out:
      logging.info("Is not available because not expert, subscribed, available, has busy schedule, or opted out")
      return False
    now = datetime.utcnow().replace(microsecond=0)
    logging.info(now)
    for event in json.loads(self.busy_time):
      logging.info(event)
      if datetime.strptime(event['start'], "%Y-%m-%dT%H:%M:%SZ") < now and datetime.strptime(event['end'], "%Y-%m-%dT%H:%M:%SZ") > now:
        logging.info("Not showing because of conflicting event")
        return False
    return True
    
  def get_name(self):
    """Returns the user's name (falling back on e-mail if necessary.)"""
    if self.name:
      return self.name
    else:
      return self.email

class AreaOfExpertise(db.Model):
  user = db.ReferenceProperty(User, required=True)
  category = db.ReferenceProperty(Category, required=True)
  description = db.StringProperty(required=True)
  
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
  