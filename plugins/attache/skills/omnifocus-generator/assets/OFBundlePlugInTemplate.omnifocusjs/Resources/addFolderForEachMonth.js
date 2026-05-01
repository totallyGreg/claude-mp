(() => {
	const action = new PlugIn.Action(function(selection, sender){
		// GET LOCALIZED NAMES OF THE MONTHS
		let locale = Calendar.current.locale.identifier
		locale = locale.replace("_", "-")
		let monthNames = []
		for (i = 0; i < 12; i++) {
			var objDate = new Date()
			objDate.setMonth(i)
			let monthName = objDate.toLocaleString(locale,{month:"long"})
			monthNames.push(monthName)
		}
		// CHECK TOP-LEVEL FOLDER NAMES
		let folderNames = folders.map(fldr => fldr.name)
		monthNames.forEach(month => {
			if(!folderNames.includes(month)){new Folder(month)}
		})
	});

	// result determines if the action menu item is enabled
	action.validate = function(selection, sender){
		return true
	};

	return action;
})();