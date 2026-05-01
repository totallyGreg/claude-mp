(() => {
	const action = new PlugIn.Action(function(selection, sender){
		let lib = this.plugIn.library("allDateLibrary")
		lib.info()
		new Alert("LIB INFO", "Library info has been logged to the console.").show()
	});

	// result determines if the action menu item is enabled
	action.validate = function(selection, sender){
		return true
	};

	return action;
})();