#!/usr/bin/env bash
# build-attache.sh — Compile ofoCore + Attache TypeScript libraries and package
# into a single consolidated Attache.omnifocusjs bundle.
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# ofoCore lives in omnifocus-core/scripts/src/ (consolidated layout).
# Attache libraries live in attache-analyst/scripts/src/attache/.
OFOCORE_SRC_DIR="${SCRIPTS_DIR}/../../omnifocus-core/scripts/src"
SRC_DIR="${SCRIPTS_DIR}/src"  # Attache libraries source
BUILD_DIR="${SCRIPTS_DIR}/build"
ASSETS_DIR="${SCRIPTS_DIR}/../assets/Attache.omnifocusjs"
BUNDLE_DIR="${BUILD_DIR}/Attache.omnifocusjs"
INTERMEDIATE_DIR="${BUILD_DIR}/intermediate"

# Find tsc reliably: prefer a local install (npm install typescript in this
# scripts dir, or sibling skill node_modules), then global, then npx.
if [ -x "${SCRIPTS_DIR}/node_modules/.bin/tsc" ]; then
  TSC="${SCRIPTS_DIR}/node_modules/.bin/tsc"
elif [ -x "${SCRIPTS_DIR}/../../omnifocus-core/scripts/node_modules/.bin/tsc" ]; then
  TSC="${SCRIPTS_DIR}/../../omnifocus-core/scripts/node_modules/.bin/tsc"
elif command -v tsc >/dev/null 2>&1; then
  TSC="tsc"
else
  TSC="npx --yes -p typescript tsc"
fi

echo "Building consolidated Attache plugin..."

# 1. Clean previous plugin build (preserve CLI output)
rm -rf "${BUNDLE_DIR}" "${INTERMEDIATE_DIR}"
mkdir -p "${BUNDLE_DIR}/Resources/en.lproj" "${INTERMEDIATE_DIR}"

# 2. Compile ofoCore TypeScript to intermediate JS
echo "  Compiling ofoCore TypeScript..."
# tsc outputs to ../build/intermediate/ relative to OFOCORE_SRC_DIR per tsconfig.plugin.json.
# We need the output in OUR INTERMEDIATE_DIR — override via --outDir.
$TSC --project "${OFOCORE_SRC_DIR}/tsconfig.plugin.json" --outDir "${INTERMEDIATE_DIR}"

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
  // D6.2 — GTD-essential queries (System Map convention-dependent)
  lib.listWaitingFor = listWaitingFor;
  lib.listSomedayMaybe = listSomedayMaybe;
  lib.listNeglectedProjects = listNeglectedProjects;
  lib.listRecentlyCompleted = listRecentlyCompleted;
  lib.listProjectsForReview = listProjectsForReview;
  // D6.2 — Project lifecycle
  lib.markProjectReviewed = markProjectReviewed;
  lib.listFolders = listFolders;
  lib.createProject = createProject;
  lib.updateProject = updateProject;
  lib.dispatch = dispatch;
  return lib;
})();
IIFE_FOOTER

# 4. Compile Attache TypeScript libraries (tsconfig lives alongside ofoCore's)
echo "  Compiling Attache TypeScript libraries..."
$TSC --project "${OFOCORE_SRC_DIR}/tsconfig.attache-libs.json" --outDir "${INTERMEDIATE_DIR}/attache"

ATTACHE_LIBS=(
  taskMetrics exportUtils foundationModelsUtils folderParser
  projectParser taskParser hierarchicalBatcher insightPatterns
  systemDiscovery preferencesManager applyForm
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
  healthCheck dailyReview whatNow weeklyReview monthlyReview processInbox
  analyzeSelected analyzeHierarchy quickOrganize completedSummary
  systemSetup discoverSystem
)
for act in "${ATTACHE_ACTIONS[@]}"; do
  cp "${ASSETS_DIR}/Resources/${act}.js" "${BUNDLE_DIR}/Resources/${act}.js"
done

# 6. Copy manifest and localization (manifest.strings + per-action .strings)
cp "${ASSETS_DIR}/manifest.json" "${BUNDLE_DIR}/manifest.json"
cp "${ASSETS_DIR}/Resources/en.lproj/"*.strings "${BUNDLE_DIR}/Resources/en.lproj/"

# 7. Copy stub script
cp "${OFOCORE_SRC_DIR}/ofo-stub.js" "${BUILD_DIR}/ofo-stub.js"

# 8. Assert every IIFE-exported function exists in the compiled ofoCore
echo "  Verifying ofoCore IIFE exports..."
BUILT_JS="${BUNDLE_DIR}/Resources/ofoCore.js"
# D6.2 additions: listWaitingFor, listSomedayMaybe, listNeglectedProjects,
# listRecentlyCompleted, listProjectsForReview, markProjectReviewed,
# listFolders, createProject, updateProject (+ deriveDurationModel,
# resolveConventions as helpers if added).
EXPECTED_FNS=(
  normalizeTask getTask completeTask dropTask createTask updateTask searchTasks listTasks
  getPerspective configurePerspective tagTask getTags createBatch
  getPerspectiveRules dumpDatabase getStats assessClarity stalledProjects getHealth
  listWaitingFor listSomedayMaybe listNeglectedProjects listRecentlyCompleted
  listProjectsForReview markProjectReviewed listFolders createProject updateProject
  dispatch
)
for fn in "${EXPECTED_FNS[@]}"; do
  grep -q "^function ${fn}(" "${BUILT_JS}" || \
    { echo "ERROR: '${fn}' missing from compiled ofoCore.js — update IIFE footer or fix rename"; exit 1; }
done
echo "  ofoCore IIFE exports OK (${#EXPECTED_FNS[@]} functions)"

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
# generate-ambient.js lives in omnifocus-generator/scripts/ (consolidated layout)
AMBIENT_GEN="${SCRIPTS_DIR}/../../omnifocus-generator/scripts/generate-ambient.js"
if [ -f "$AMBIENT_GEN" ]; then
  node "$AMBIENT_GEN"
  echo "  ofo-core-ambient.d.ts regenerated"
else
  echo "  WARNING: generate-ambient.js not found at ${AMBIENT_GEN} — ofo-core-ambient.d.ts may be stale"
fi

# 11. Clean intermediate files
rm -rf "${INTERMEDIATE_DIR}"

echo "  Plugin bundle: ${BUNDLE_DIR}"
echo "  Stub script:   ${BUILD_DIR}/ofo-stub.js"
echo "Done."
