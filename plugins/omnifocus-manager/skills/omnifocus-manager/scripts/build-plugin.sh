#!/usr/bin/env bash
# build-plugin.sh — Compile ofo-core.ts and package as OmniFocus plugin bundle.
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPTS_DIR}/src"
BUILD_DIR="${SCRIPTS_DIR}/build"
BUNDLE_DIR="${BUILD_DIR}/ofo-core.omnifocusjs"
INTERMEDIATE_DIR="${BUILD_DIR}/intermediate"

echo "Building ofo-core plugin..."

# 1. Clean previous build
rm -rf "${BUILD_DIR}"
mkdir -p "${BUNDLE_DIR}/Resources/en.lproj" "${INTERMEDIATE_DIR}"

# 2. Compile TypeScript to intermediate JS
echo "  Compiling TypeScript..."
npx tsc --project "${SRC_DIR}/tsconfig.plugin.json"

# 3. Wrap compiled output in PlugIn.Library IIFE
echo "  Wrapping in PlugIn.Library IIFE..."
COMPILED="${INTERMEDIATE_DIR}/ofo-core.js"
if [ ! -f "$COMPILED" ]; then
  echo "ERROR: tsc output not found at ${COMPILED}"
  exit 1
fi

# Strip any module-level export/import that tsc might emit
# (shouldn't exist since we have no import/export in source, but safety check)
CORE_JS=$(sed '/^export /d; /^import /d' "$COMPILED")

cat > "${BUNDLE_DIR}/Resources/ofoCore.js" << 'IIFE_HEADER'
(() => {
  var lib = new PlugIn.Library(new Version("1.0"));

IIFE_HEADER

echo "$CORE_JS" >> "${BUNDLE_DIR}/Resources/ofoCore.js"

cat >> "${BUNDLE_DIR}/Resources/ofoCore.js" << 'IIFE_FOOTER'

  lib.getTask = getTask;
  lib.completeTask = completeTask;
  lib.createTask = createTask;
  lib.updateTask = updateTask;
  lib.searchTasks = searchTasks;
  lib.listTasks = listTasks;
  lib.getPerspective = getPerspective;
  lib.configurePerspective = configurePerspective;
  lib.tagTask = tagTask;
  lib.getTags = getTags;
  lib.createBatch = createBatch;
  lib.getPerspectiveRules = getPerspectiveRules;
  lib.dumpDatabase = dumpDatabase;
  lib.getStats = getStats;
  lib.dispatch = dispatch;
  return lib;
})();
IIFE_FOOTER

# 4. Copy manifest and localization
cp "${SRC_DIR}/manifest.json" "${BUNDLE_DIR}/manifest.json"
echo '"com.totally-tools.ofo-core" = "OFO Core";' > "${BUNDLE_DIR}/Resources/en.lproj/manifest.strings"

# 5. Copy stub script
cp "${SRC_DIR}/ofo-stub.js" "${BUILD_DIR}/ofo-stub.js"

# 6. Clean intermediate files
rm -rf "${INTERMEDIATE_DIR}"

echo "  Plugin bundle: ${BUNDLE_DIR}"
echo "  Stub script:   ${BUILD_DIR}/ofo-stub.js"
echo "Done."
