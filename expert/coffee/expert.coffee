# main function - execution starts here
$ ->
  # test to make sure that we got here
  console.log 'We got here. Yeah baby! YEAH!'
  
  # uncomment this line to show debug colors
  # showDebugColors()
      
# this debug function draws a background behind every visible element
# so that they can be laid out
showDebugColors = ->
  colors = ['blue', 'green', 'red', 'yellow', 'purple', 'orange']
  for color in colors
    $(".test-#{color}").css
      backgroundColor: color