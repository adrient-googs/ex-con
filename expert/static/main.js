var onOpened = function() {
	window.console.log('onOpened')
}

var onMessage = function(m) {
	window.console.log('onMessage ' + m)
	window.location.reload()
}

var onError = function() {
	// Called when the token expires
	window.console.log('onError')
}

var onClose = function() {
	window.console.log('onClose')	
}