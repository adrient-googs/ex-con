from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class Category(db.Model):
  name = db.TextProperty(required=True)

class User(db.Model):
  user = db.TextProperty(required=True)
  show = db.TextProperty()
  show_time = db.DateTimeProperty()
  available = db.BooleanProperty()
  mute_time = db.DateTimeProperty()

class UserToCategory(db.Model):
  user = db.TextProperty(required=True)
  category = db.TextProperty(required=True)