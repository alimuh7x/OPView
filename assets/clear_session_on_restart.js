/**
 * Clear sessionStorage when server restarts.
 *
 * Detects server restarts by comparing the current server session ID
 * with the stored session ID from the previous session.
 */

window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.session_checker = window.dash_clientside.session_checker || {};

window.dash_clientside.session_checker.check_session = function(server_session_data) {
    if (!server_session_data || !server_session_data.id) {
        return window.dash_clientside.no_update;
    }

    const current_server_id = server_session_data.id;
    const stored_server_id = sessionStorage.getItem('server-session-id');
    const reloaded_for_id = sessionStorage.getItem('server-session-reloaded');

    console.log('[SESSION] Current server ID:', current_server_id);
    console.log('[SESSION] Stored server ID:', stored_server_id);

    // First load or server restarted
    if (!stored_server_id || stored_server_id !== current_server_id) {
        console.log('[SESSION] Server restart detected - clearing all session data');

        // Clear all session storage
        sessionStorage.clear();

        // Store new session ID
        sessionStorage.setItem('server-session-id', current_server_id);
        sessionStorage.setItem('server-session-reloaded', current_server_id);

        console.log('[SESSION] Session data cleared');
        // Reload once so Dash rehydrates from a clean sessionStorage.
        // Guard against reload loops using the session id.
        if (reloaded_for_id !== current_server_id) {
            window.location.reload();
        }
    } else {
        console.log('[SESSION] Same server session - preserving data');
    }

    return window.dash_clientside.no_update;
};
