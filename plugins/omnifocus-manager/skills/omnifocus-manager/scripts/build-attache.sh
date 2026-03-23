#!/usr/bin/env bash
# build-attache.sh — Compile ofoCore + Attache TypeScript libraries and package
# into a single consolidated Attache.omnifocusjs bundle.
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPTS_DIR}/src"
BUILD_DIR="${SCRIPTS_DIR}/build"
ASSETS_DIR="${SCRIPTS_DIR}/../assets/Attache.omnifocusjs"
BUNDLE_DIR="${BUILD_DIR}/Attache.omnifocusjs"
INTERMEDIATE_DIR="${BUILD_DIR}/intermediate"

echo "Building consolidated Attache plugin..."

# 1. Clean previous plugin build (preserve CLI output)
rm -rf "${BUNDLE_DIR}" "${INTERMEDIATE_DIR}"
mkdir -p "${BUNDLE_DIR}/Resources/en.lproj" "${INTERMEDIATE_DIR}"

# 2. Compile ofoCore TypeScript to intermediate JS
echo "  Compiling ofoCore TypeScript..."
npx tsc --project "${SRC_DIR}/tsconfig.plugin.json"

# 3. Wrap compiled ofoCore in PlugIn.Library IIFE
echo "  Wrapping ofoCore in PlugIn.Library IIFE..."
COMPILED="${INTERMEDIATE_DIR}/ofo-core.js"
if [ ! -f "$COMPILED" ]; then
  echo "ERROR: tsc output not found at ${COMPILED}"
  exit 1
fi

CORE_JS=$(sed '/^export /d; /^import /d' "$COMPILED")

cat > "${BUNDLE_DIR}/Resources/ofoCore.js" << 'IIFE_HEADER'
(() => {
  var lib = new PlugIn.Library(new Version("1.0"));

IIFE_HEADER

echo "$CORE_JS" >> "${BUNDLE_DIR}/Resources/ofoCore.js"

cat >> "${BUNDLE_DIR}/Resources/ofoCore.js" << 'IIFE_FOOTER'

  lib.normalizeTask = normalizeTask;
  lib.getTask = getTask;
  lib.completeTask = completeTask;
  lib.dropTask = dropTask;
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
  lib.assessClarity = assessClarity;
  lib.stalledProjects = stalledProjects;
  lib.getHealth = getHealth;
  lib.dispatch = dispatch;
  return lib;
})();
IIFE_FOOTER

# 4. Compile Attache TypeScript libraries
echo "  Compiling Attache TypeScript libraries..."
npx tsc --project "${SRC_DIR}/tsconfig.attache-libs.json"

ATTACHE_LIBS=(
  taskMetrics exportUtils foundationModelsUtils folderParser
  projectParser taskParser hierarchicalBatcher insightPatterns
  systemDiscovery preferencesManager
)
for lib in "${ATTACHE_LIBS[@]}"; do
  COMPILED_LIB="${INTERMEDIATE_DIR}/attache/${lib}.js"
  if [ ! -f "$COMPILED_LIB" ]; then
    echo "ERROR: Compiled ${lib}.js not found at ${COMPILED_LIB}"
    exit 1
  fi
  cp "${COMPILED_LIB}" "${BUNDLE_DIR}/Resources/${lib}.js"
done
echo "  Attache libraries compiled (${#ATTACHE_LIBS[@]} libraries)"

# 5. Copy Attache action scripts into bundle (actions remain JS)
echo "  Copying Attache actions..."
ATTACHE_ACTIONS=(
  dailyReview weeklyReview analyzeSelected analyzeHierarchy
  completedSummary systemSetup discoverSystem
)
for act in "${ATTACHE_ACTIONS[@]}"; do
  cp "${ASSETS_DIR}/Resources/${act}.js" "${BUNDLE_DIR}/Resources/${act}.js"
done

# 6. Copy manifest and localization (manifest.strings + per-action .strings)
cp "${ASSETS_DIR}/manifest.json" "${BUNDLE_DIR}/manifest.json"
cp "${ASSETS_DIR}/Resources/en.lproj/"*.strings "${BUNDLE_DIR}/Resources/en.lproj/"

# 7. Copy stub script
cp "${SRC_DIR}/ofo-stub.js" "${BUILD_DIR}/ofo-stub.js"

# 8. Assert every IIFE-exported function exists in the compiled ofoCore
echo "  Verifying ofoCore IIFE exports..."
BUILT_JS="${BUNDLE_DIR}/Resources/ofoCore.js"
for fn in normalizeTask getTask completeTask dropTask createTask updateTask searchTasks listTasks \
          getPerspective configurePerspective tagTask getTags createBatch \
          getPerspectiveRules dumpDatabase getStats assessClarity stalledProjects getHealth dispatch; do
  grep -q "^function ${fn}(" "${BUILT_JS}" || \
    { echo "ERROR: '${fn}' missing from compiled ofoCore.js — update IIFE footer or fix rename"; exit 1; }
done
echo "  ofoCore IIFE exports OK (20 functions)"

# 9. Verify all Attache libraries have PlugIn.Library IIFE structure
echo "  Verifying Attache library IIFE structure..."
for lib in "${ATTACHE_LIBS[@]}"; do
  LIB_JS="${BUNDLE_DIR}/Resources/${lib}.js"
  grep -q "PlugIn.Library" "${LIB_JS}" || \
    { echo "ERROR: ${lib}.js missing PlugIn.Library declaration"; exit 1; }
done
echo "  Attache library IIFEs OK (${#ATTACHE_LIBS[@]} libraries)"

# 10. Regenerate ofo-core-ambient.d.ts from ofo-types.ts
echo "  Regenerating ofo-core-ambient.d.ts..."
node "${SCRIPTS_DIR}/generate-ambient.js"
echo "  ofo-core-ambient.d.ts regenerated"

# 11. Clean intermediate files
rm -rf "${INTERMEDIATE_DIR}"

echo "  Plugin bundle: ${BUNDLE_DIR}"
echo "  Stub script:   ${BUILD_DIR}/ofo-stub.js"
echo "Done."
