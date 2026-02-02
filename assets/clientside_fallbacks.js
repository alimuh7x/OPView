/**
 * Fallback stubs for clientside callbacks.
 * Prevents "undefined apply" errors if an asset fails to load.
 */
window.dash_clientside = window.dash_clientside || {};

window.dash_clientside.comparison_persistence = window.dash_clientside.comparison_persistence || {};
if (typeof window.dash_clientside.comparison_persistence.restore_selected_files !== 'function') {
    window.dash_clientside.comparison_persistence.restore_selected_files = function() {
        return window.dash_clientside.no_update;
    };
}
if (typeof window.dash_clientside.comparison_persistence.restore_controls !== 'function') {
    window.dash_clientside.comparison_persistence.restore_controls = function() {
        return window.dash_clientside.no_update;
    };
}

window.dash_clientside.session_checker = window.dash_clientside.session_checker || {};
if (typeof window.dash_clientside.session_checker.check_session !== 'function') {
    window.dash_clientside.session_checker.check_session = function() {
        return window.dash_clientside.no_update;
    };
}

window.dash_clientside.comparison = window.dash_clientside.comparison || {};
if (typeof window.dash_clientside.comparison.export_png !== 'function') {
    window.dash_clientside.comparison.export_png = function() {
        return window.dash_clientside.no_update;
    };
}
