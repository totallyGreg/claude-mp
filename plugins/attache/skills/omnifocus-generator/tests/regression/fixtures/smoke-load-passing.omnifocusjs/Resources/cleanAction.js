// REGRESSION FIXTURE — positive control. Clean action with no errors;
// should pass D8.4 coherence (has PlugIn.Action) and D8.6 smoke-load
// (only references defined globals).
(() => {
  var action = new PlugIn.Action(function(selection, sender) {
    try {
      var count = flattenedTasks.length;
      var t = new Task("test", inbox.ending);
      return undefined;
    } catch (e) {
      return undefined;
    }
  });
  return action;
})();
