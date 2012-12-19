// Generated by CoffeeScript 1.4.0

/*
Useful Utilities
*/


(function() {
  var move_out_of_holding_pen, show_debug_colors, util,
    __slice = [].slice;

  util = util != null ? util : {};

  util.assertion = function(condition, err_msg) {
    if (!condition) {
      alert(err_msg);
      throw new Error(err_msg);
    }
  };

  util.flip = function(func) {
    return function() {
      var args;
      args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
      return func.apply(null, args.slice(0).reverse());
    };
  };

  util.later = function() {
    var args, func, ms, _ref, _ref1;
    args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
    if (args.length === 1) {
      _ref = [args[0], 1], func = _ref[0], ms = _ref[1];
    } else if (args.length === 2) {
      _ref1 = [args[1], args[0]], func = _ref1[0], ms = _ref1[1];
    } else {
      throw new Error('util.later takes 1 or 2 arguments only.');
    }
    return setTimeout(func, ms);
  };

  util.trim = function(str) {
    return str.replace(/^\s+|\s+$/g, '');
  };

  util.titleCase = function(str) {
    return str.replace(/\w\S*/g, function(txt) {
      return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
  };

  util.prettyUsername = function(name) {
    var at_index;
    at_index = name.indexOf('@');
    if (at_index > 0) {
      return name.slice(0, at_index);
    } else {
      return name;
    }
  };

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

  this.category_checked = function(category_id) {
    var checkbox, checked, description, display_attr;
    checkbox = $("input#" + category_id + "-checkbox");
    checked = checkbox.attr('checked');
    description = $("div#" + category_id + "-description");
    display_attr = checked ? 'block' : 'none';
    description.css({
      display: display_attr
    });
    if (checked) {
      return description.children('input').focus();
    }
  };

  this.validate_expertise_form = function() {
    var div, input, input_name, input_value, _i, _len, _ref;
    _ref = $('form#manage-expertise').children('div.sub-category');
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      div = _ref[_i];
      if ($(div).css('display') === 'none') {
        continue;
      }
      input = $(div).children('input');
      input_name = (input.attr('name')).replace(' description', '');
      input_value = util.trim(input.attr('value'));
      if (input_value === '') {
        alert("Please provde a subcategory for '" + input_name + ".'");
        return false;
      }
    }
    return true;
  };

}).call(this);
