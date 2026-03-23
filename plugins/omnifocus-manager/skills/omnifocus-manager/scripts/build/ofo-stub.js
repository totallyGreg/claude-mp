// ofo-stub.js — Stable stub script for omnijs-run URL invocation.
// This file NEVER changes — it's approved once via "Automatically run" checkbox.
// All variable data comes via &arg= parameter.
var args = argument;
try {
  var p = PlugIn.find("com.totallytools.omnifocus.attache");
  if (!p) {
    Pasteboard.general.string = JSON.stringify({ success: false, error: "Attache plugin not installed. Run: npm run deploy" });
  } else {
    var lib = p.library("ofoCore");
    var result = lib.dispatch(args);
    Pasteboard.general.string = JSON.stringify(result);
  }
} catch (e) {
  Pasteboard.general.string = JSON.stringify({ success: false, error: e.toString() });
}
