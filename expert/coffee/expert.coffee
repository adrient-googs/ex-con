# main function - execution starts here
$ ->
  # move the contents out of the holding pen so the user can see it
  move_out_of_holding_pen()
  
  # uncomment this line to show debug colors
  # show_debug_colors()
  
# this function moves the contents of the holding pen into the appropriate
# container div
move_out_of_holding_pen = ->
  $("div#holding-pen").children('div').each ->
    new_parent = $("div##{$(@).attr 'id'}-parent")
    $(@).detach().appendTo new_parent
      
# this debug function draws a background behind every visible element
# so that they can be laid out
show_debug_colors = ->
  colors = ['blue', 'green', 'red', 'yellow', 'purple', 'orange']
  for color in colors
    $(".test-#{color}").css
      backgroundColor: color
      
# this function is called when a category is checked
@category_checked = (category_id) ->
  # figure out if the checkbox is checked
  checkbox = $("input##{category_id}-checkbox")
  checked = checkbox.attr 'checked'

  # display the description based on whether the checkbox is checked
  description = $("div##{category_id}-description")
  display_attr = if checked then 'block' else 'none'
  description.css display: display_attr

  # move the focus to the description input
  description.children('input').focus() if checked
  
# this function is called when a category is removed
@category_removed = (category_id) ->
  # checkbox = $("input##{category_id}-checkbox")
  # checkbox.get(0).removeAttribute 'checked'
  # 
  category = $("div##{category_id}")[0]
  category.parentNode.removeChild(category);
  return true
  
# this function is called when the submit expertise form is called
@validate_expertise_form = ->
  box_value = $("input#search}")[0].value
  if box_value != "" && box_value.match(/\s::\s/) == null
    alert "Please provide your expertise in the following \"<category> :: <subcategory>\" format"
    return false
  return true
  # check to make sure that all the expertise works
  # for div in $('form#manage-expertise').children('div.sub-category')
  #   if $(div).css('display') is 'none'
  #     continue 
  #   input = $(div).children('input')
  #   input_name = (input.attr 'name').replace(' description', '')
  #   input_value = util.trim input.attr 'value'
  #   if input_value is ''
  #     alert "Please provide a subcategory for '#{input_name}.'"
  #     return false
  # return false