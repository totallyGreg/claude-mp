// REGRESSION FIXTURE — references `flattenedTaks` (typo of flattenedTasks)
// at top level. The D8.6 smoke-load gate's stub sandbox does NOT define
// flattenedTaks, so vm.runInContext should throw ReferenceError when
// evaluating this file.
(() => {
  var action = new PlugIn.Action(function(selection, sender) {
    try {
      return undefined;
    } catch (e) {
      return undefined;
    }
  });
  // Top-level reference to a typo'd global — this is what should crash on load.
  var typoCount = flattenedTaks.length;
  return action;
})();
