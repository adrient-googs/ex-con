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