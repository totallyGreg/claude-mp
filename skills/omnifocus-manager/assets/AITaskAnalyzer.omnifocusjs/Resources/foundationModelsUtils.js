/**
 * Foundation Models Utility Library
 *
 * Provides helpers for working with Apple Foundation Models (LanguageModel API)
 * including availability checking, error handling, and session management.
 *
 * Usage in PlugIn.Action:
 *   const fmUtils = this.plugIn.library("foundationModelsUtils");
 *   if (!fmUtils.isAvailable()) {
 *       fmUtils.showUnavailableAlert();
 *       return;
 *   }
 */
(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    /**
     * Check if Apple Foundation Models (LanguageModel API) exists.
     * Note: This only checks if the API exists, not if it's actually usable.
     * Sessions can be created but may be invalid if Apple Intelligence is unavailable.
     *
     * @returns {boolean} True if LanguageModel API exists
     */
    lib.isAvailable = function() {
        // Check if LanguageModel exists
        if (typeof LanguageModel === 'undefined') {
            return false;
        }

        // Check if LanguageModel.Session exists
        if (typeof LanguageModel.Session === 'undefined') {
            return false;
        }

        return true;
    };

    /**
     * Get detailed error message explaining why LanguageModel is unavailable.
     * Provides specific requirements and troubleshooting steps.
     *
     * @returns {string} Detailed error message
     */
    lib.getUnavailableMessage = function() {
        const reasons = [];

        if (typeof LanguageModel === 'undefined') {
            reasons.push("LanguageModel API not found in OmniFocus");
        } else if (typeof LanguageModel.Session === 'undefined') {
            reasons.push("LanguageModel.Session not available");
        } else {
            reasons.push("Language models are not available on this system");
        }

        const message = `Apple Foundation Models Not Available\n\n` +
            `This feature requires:\n` +
            `• OmniFocus 4.8 or later\n` +
            `• macOS 15.2+ or iOS 18.2+\n` +
            `• Apple Silicon (M1/M2/M3/M4) or iPhone 15 Pro+\n` +
            `• Apple Intelligence enabled in System Settings\n\n` +
            `Current issue:\n${reasons.join('\n')}\n\n` +
            `Troubleshooting:\n` +
            `1. Update OmniFocus to 4.8+ if needed\n` +
            `2. Update to macOS 15.2+ or iOS 18.2+ if needed\n` +
            `3. Verify you have Apple Silicon hardware\n` +
            `4. Enable Apple Intelligence:\n` +
            `   Settings → Apple Intelligence & Siri → Turn On`;

        return message;
    };

    /**
     * Show an alert explaining why Apple Foundation Models is unavailable.
     * Uses detailed message from getUnavailableMessage().
     */
    lib.showUnavailableAlert = function() {
        const alert = new Alert(
            "Apple Foundation Models Required",
            this.getUnavailableMessage()
        );
        alert.show();
    };

    /**
     * Create a new LanguageModel.Session with error handling.
     * Note: Session creation may succeed but the session may be invalid.
     * Always wrap session.respondWithSchema() calls in try/catch.
     *
     * @returns {LanguageModel.Session|null} Session instance or null if API unavailable
     * @throws {Error} If session creation fails
     */
    lib.createSession = function() {
        if (!this.isAvailable()) {
            throw new Error("LanguageModel API not available");
        }

        return new LanguageModel.Session();
    };

    /**
     * Validate action availability - use in action.validate function.
     * Note: This only checks if the API exists, not if Apple Intelligence is enabled.
     * Actions may still fail at runtime if Apple Intelligence is unavailable.
     *
     * We intentionally return true even if we can't fully validate, because:
     * 1. Session creation succeeds but sessions may be invalid
     * 2. We can't detect Apple Intelligence status without trying to use it
     * 3. Better to show good error messages than unpredictable graying out
     *
     * @returns {boolean} Always returns true - validation happens at runtime
     */
    lib.validateActionAvailability = function() {
        // Don't gray out actions - we can't reliably detect availability
        // Let the action run and show a good error message if it fails
        return true;
    };

    return lib;
})();
