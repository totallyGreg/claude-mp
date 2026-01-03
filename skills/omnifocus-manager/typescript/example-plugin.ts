/*{
	"type": "action",
	"targets": ["omnifocus", "omnigraffle", "omniplan", "omnioutliner"],
	"author": "Otto Automator",
	"identifier": "com.omni-automation.all.ts-sample-plug-in",
	"version": "1.0",
	"description": "An example plug-in for working with TypeScript Server in BBEdit.",
	"label": "Typescript Plug-In",
	"shortLabel": "TypeScript Plug-In",
	"paletteLabel": "TypeScript Plug-In",
	"image": "gearshape"
}*/
(() => {
	const action = new PlugIn.Action(function(selection, sender){
		// action code
				
		new Alert("GREETING", "Hello World!").show()
	});

	action.validate = function(selection, sender){
		// validation code
		return true
	};
	
	return action;
})();