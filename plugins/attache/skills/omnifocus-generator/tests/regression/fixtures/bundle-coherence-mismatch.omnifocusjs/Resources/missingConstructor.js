// REGRESSION FIXTURE — this file deliberately does NOT contain the
// action constructor that the manifest expects. The D8.4 bundle-coherence
// check should reject this bundle because the manifest declares
// "missingConstructor" as an action but the implementation file doesn't
// register one. (We avoid quoting the constructor pattern here to keep
// the regex check honest — a grep-based coherence check would match
// the comment otherwise.)
(() => {
  console.log("This file is missing the required action constructor");
})();
