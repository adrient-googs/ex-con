"""Two simple decorator functions which make it possible to write
handlers as functions instead of classes. For example:

@hanler.text_hander
def example_text_handler(out):
  out.write('This is a text-only webpage.')
  
@handler.template_hander('template_file.html')
def example_template_handler():
  a_template_value = None # for example
  return {
    'template_value_name' : a_template_value
  }
"""

def text_handler(func):
  """Returns a handler"""
  