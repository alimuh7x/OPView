/**
 * Manual sessionStorage persistence for comparison stores.
 *
 * Dash's storage_type='session' doesn't restore data for stores that are
 * destroyed and recreated by callbacks. This script manually handles
 * loading persisted data from sessionStorage when stores are recreated.
 */

window.dash_clientside = Object.assign({}, window.dash_clientside, {
    comparison_persistence: {
        /**
         * Restore selected files from sessionStorage when store is recreated
         */
        restore_selected_files: function(store_data, store_id) {
            // Get the store ID string for sessionStorage key
            if (!store_id || !store_id.group) {
                return window.dash_clientside.no_update;
            }

            const key = `comparison-selected-files-${store_id.group}`;

            // If store already has data, update sessionStorage and return it
            if (store_data && store_data.length > 0) {
                sessionStorage.setItem(key, JSON.stringify(store_data));
                return store_data;
            }

            // Try to load from sessionStorage
            const stored = sessionStorage.getItem(key);
            if (stored) {
                try {
                    const parsed = JSON.parse(stored);
                    if (Array.isArray(parsed) && parsed.length > 0) {
                        console.log(`[PERSISTENCE] Restored ${parsed.length} files for group ${store_id.group}`);
                        return parsed;
                    }
                } catch (e) {
                    console.error('[PERSISTENCE] Error parsing stored data:', e);
                }
            }

            // No persisted data found
            return [];
        },

        /**
         * Restore control settings from sessionStorage when store is recreated
         */
        restore_controls: function(store_data, store_id) {
            // Get the store ID string for sessionStorage key
            if (!store_id || !store_id.group) {
                return window.dash_clientside.no_update;
            }

            const key = `comparison-controls-${store_id.group}`;

            // If store already has data, update sessionStorage and return it
            if (store_data && Object.keys(store_data).length > 0) {
                sessionStorage.setItem(key, JSON.stringify(store_data));
                return store_data;
            }

            // Try to load from sessionStorage
            const stored = sessionStorage.getItem(key);
            if (stored) {
                try {
                    const parsed = JSON.parse(stored);
                    if (parsed && typeof parsed === 'object') {
                        console.log(`[PERSISTENCE] Restored controls for group ${store_id.group}`);
                        return parsed;
                    }
                } catch (e) {
                    console.error('[PERSISTENCE] Error parsing stored controls:', e);
                }
            }

            // No persisted data found
            return window.dash_clientside.no_update;
        }
    }
});
