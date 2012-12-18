// Generated by CoffeeScript 1.4.0
(function() {
  var move_out_of_holding_pen, show_debug_colors;

  $(function() {
    return move_out_of_holding_pen();
  });

  move_out_of_holding_pen = function() {
    return $("div#holding-pen").children('div').each(function() {
      var new_parent;
      new_parent = $("div#" + ($(this).attr('id')) + "-parent");
      return $(this).detach().appendTo(new_parent);
    });
  };

  show_debug_colors = function() {
    var color, colors, _i, _len, _results;
    colors = ['blue', 'green', 'red', 'yellow', 'purple', 'orange'];
    _results = [];
    for (_i = 0, _len = colors.length; _i < _len; _i++) {
      color = colors[_i];
      _results.push($(".test-" + color).css({
        backgroundColor: color
      }));
    }
    return _results;
  };

}).call(this);
