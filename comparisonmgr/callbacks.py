"""
Comparison feature callbacks.

Extracted from OPView.py Phase 10.3 - provides callback functions for:
- File selection and removal
- Heatmap updates
- Control synchronization
- Range selection and updates
- Control persistence
"""

import time
from dash import Output, Input, State, MATCH, ALL, ctx, html, dcc, no_update, ClientsideFunction
from dash.exceptions import PreventUpdate

# Import helper functions from same package
from .helpers import (
    _comparison_entries_from_selected,
    get_comparison_panels,
    _comparison_settings,
    _comparison_range_defaults,
    _comparison_entries,
    list_vtk_files,
    _group_comparison_entries,
)
from .ui_builders import build_comparison_heatmap_row


def _make_comparison_cache_key(files, field, range_min, range_max, palette, full_scale, slider_range):
    """Deprecated: cache key helper (unused)."""
    files_tuple = tuple(sorted(files)) if files else ()
    slider_tuple = tuple(slider_range) if slider_range else ()
    return (files_tuple, field, range_min, range_max, palette, full_scale, slider_tuple)


# Removed: _comparison_upload() - Upload feature removed per user request


def register_comparison_callbacks(app):
    """Register all comparison feature callbacks.

    Args:
        app: Dash application instance
    """

    # PNG Export: Server-side callback to catch button clicks (pattern-matching works here)
    @app.callback(
        Output('comparison-png-export-trigger', 'data'),
        Input({'type': 'comparison-download', 'group': ALL}, 'n_clicks'),
        State({'type': 'comparison-download', 'group': ALL}, 'id'),
        prevent_initial_call=True
    )
    def _trigger_png_export(n_clicks_list, button_ids):
        """Catch PNG button clicks and trigger export via Store."""
        if not ctx.triggered_id:
            raise PreventUpdate

        if not isinstance(ctx.triggered_id, dict):
            raise PreventUpdate

        # Check the actual click value - must be > 0 (actual click, not initialization)
        triggered_value = ctx.triggered[0]['value'] if ctx.triggered else None

        if not triggered_value or triggered_value == 0:
            raise PreventUpdate

        group = ctx.triggered_id.get('group')

        if not group:
            raise PreventUpdate

        # Return group name to trigger clientside export
        return {'group': group, 'timestamp': time.time()}

    # PNG Export: Universal clientside callback that handles all groups
    # JavaScript code is in assets/comparison_png_export.js
    app.clientside_callback(
        ClientsideFunction(
            namespace='comparison',
            function_name='export_png'
        ),
        Output('comparison-png-export-dummy', 'children'),
        Input('comparison-png-export-trigger', 'data'),
        prevent_initial_call=True
    )

    print("[PNG Export] Clientside callback registered")

    # SessionStorage Persistence: Restore selected files when stores are recreated
    app.clientside_callback(
        ClientsideFunction(
            namespace='comparison_persistence',
            function_name='restore_selected_files'
        ),
        Output({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data', allow_duplicate=True),
        Input({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
        State({'type': 'comparison-selected-files-store', 'group': MATCH}, 'id'),
        prevent_initial_call='initial_duplicate'  # Fire on initial creation to restore from sessionStorage
    )

    # SessionStorage Persistence: Restore control settings when stores are recreated
    app.clientside_callback(
        ClientsideFunction(
            namespace='comparison_persistence',
            function_name='restore_controls'
        ),
        Output({'type': 'comparison-controls-store', 'group': MATCH}, 'data', allow_duplicate=True),
        Input({'type': 'comparison-controls-store', 'group': MATCH}, 'data'),
        State({'type': 'comparison-controls-store', 'group': MATCH}, 'id'),
        prevent_initial_call='initial_duplicate'  # Fire on initial creation to restore from sessionStorage
    )

    print("[Persistence] Clientside callbacks registered for sessionStorage restoration")

    @app.callback(
        Output({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
        Output({'type': 'comparison-vtk-picker', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-vtk-picker', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-remove-file', 'group': MATCH, 'path': ALL}, 'n_clicks'),
        State({'type': 'comparison-remove-file', 'group': MATCH, 'path': ALL}, 'id'),
        State({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
        prevent_initial_call=True
    )
    def _update_comparison_selected_files(selected_values, remove_clicks, remove_ids, current_selected):
        """Persist selected VTK/Comparison files per group and handle remove buttons."""
        triggered = ctx.triggered_id
        # Picker change wins.
        if isinstance(triggered, dict) and triggered.get('type') == 'comparison-vtk-picker':
            picked = selected_values or []
            # Since we clear the dropdown display, Dash may only report the newly picked item(s).
            # Merge with existing selection to preserve multi-select behavior.
            values = list(current_selected or [])
            for p in picked:
                if p not in values:
                    values.append(p)
            return values, []
        # Remove button clicked.
        if isinstance(triggered, dict) and triggered.get('type') == 'comparison-remove-file':
            # Ignore spurious triggers from layout re-rendering (n_clicks == 0/None).
            triggered_value = ctx.triggered[0].get('value') if ctx.triggered else None
            if not triggered_value:
                raise PreventUpdate
            path = triggered.get('path')
            values = list(current_selected or [])
            if path in values:
                values.remove(path)
            return values, []
        raise PreventUpdate

    @app.callback(
        Output({'type': 'comparison-heatmap-rows', 'group': MATCH}, 'children'),
        Input({'type': 'comparison-heatmap-field', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-heatmap-range-min', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-heatmap-range-max', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-heatmap-palette', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-heatmap-full-scale', 'group': MATCH}, 'checked'),
        Input({'type': 'comparison-overlay-toggle', 'group': MATCH}, 'checked'),
        Input({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),  # Input so callback fires when data restored
        State({'type': 'comparison-heatmap-rows', 'group': MATCH}, 'id'),
        State('comparison-files-store', 'data'),
    )
    def _update_comparison_heatmaps(field, range_min, range_max, palette, full_scale, overlay_checked, selected_paths, rows_id, files):
        """Update heatmaps for a single comparison group."""
        group = rows_id.get('group') if isinstance(rows_id, dict) else None

        # Debug logging
        print(f"\n[HEATMAP UPDATE] Callback fired for group: {group}")
        print(f"[HEATMAP UPDATE] Selected paths: {selected_paths} (type: {type(selected_paths)})")
        print(f"[HEATMAP UPDATE] Field: {field}, Range: {range_min}-{range_max}, Palette: {palette}")

        # Check if we have selected files (handle None from sessionStorage)
        if not selected_paths or selected_paths is None:
            print("[HEATMAP UPDATE] No selected paths - returning empty")
            return []

        group_entries = _comparison_entries_from_selected(selected_paths)
        print(f"[HEATMAP UPDATE] Group entries count: {len(group_entries)}")
        if not group_entries:
            print("[HEATMAP UPDATE] No group entries - returning empty")
            return []

        panels = get_comparison_panels(group_entries)
        print(f"[HEATMAP UPDATE] Panels created: {len(panels)}")
        if not panels:
            print("[HEATMAP UPDATE] No panels created - returning empty")
            return []

        panels_for_group = {
            entry.get('path'): panels.get(entry.get('path'))
            for entry in group_entries
            if entry and entry.get('path') in panels
        }
        print(f"[HEATMAP UPDATE] Panels for group: {len(panels_for_group)}")
        if not panels_for_group:
            print("[HEATMAP UPDATE] No panels for group - returning empty")
            return []

        settings, _, _ = _comparison_settings(
            panels_for_group, field, range_min, range_max, palette, full_scale,
            interfaces_overlay_visible=overlay_checked
        )
        result = build_comparison_heatmap_row(panels_for_group, group_entries, settings, group, app=app)
        print(f"[HEATMAP UPDATE] Returning {len(result) if isinstance(result, list) else 'non-list'} heatmap rows")
        return result

    @app.callback(
        Output({'type': 'comparison-heatmap-field', 'group': MATCH}, 'options'),
        Output({'type': 'comparison-heatmap-field', 'group': MATCH}, 'value'),
        Output({'type': 'comparison-heatmap-field', 'group': MATCH}, 'disabled'),
        Output({'type': 'comparison-heatmap-palette', 'group': MATCH}, 'options'),
        Output({'type': 'comparison-heatmap-palette', 'group': MATCH}, 'value'),
        Output({'type': 'comparison-heatmap-palette', 'group': MATCH}, 'disabled'),
        Input({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
        State({'type': 'comparison-controls-store', 'group': MATCH}, 'data'),
    )
    def _sync_comparison_control_options(selected_paths, stored_controls):
        """Lazy-load comparison control options only after user selects files."""
        group_entries = _comparison_entries_from_selected(selected_paths)
        panels = get_comparison_panels(group_entries)
        panels_for_group = {
            entry.get('path'): panels.get(entry.get('path'))
            for entry in group_entries
            if entry and entry.get('path') in panels
        }

        has_selection = bool(panels_for_group)
        stored = stored_controls or {}
        # Use stored values regardless of file selection to preserve settings during tab switches
        settings, scalar_options, palette_options = _comparison_settings(
            panels_for_group,
            scalar_value=stored.get('scalar'),
            range_min=stored.get('range_min'),
            range_max=stored.get('range_max'),
            palette_value=stored.get('palette'),
            full_scale=stored.get('full_scale', False),
            slider_range=stored.get('slider_range'),
            interfaces_overlay_visible=stored.get('interfaces_overlay_visible', False),
        )

        return (
            scalar_options or [],
            settings.get('scalar'),
            not has_selection,
            palette_options or [],
            settings.get('palette'),
            not has_selection,
        )

    @app.callback(
        Output({'type': 'comparison-heatmap-range-min', 'group': MATCH}, 'disabled'),
        Output({'type': 'comparison-heatmap-range-max', 'group': MATCH}, 'disabled'),
        Output({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'disabled'),
        Output({'type': 'comparison-heatmap-reset', 'group': MATCH}, 'disabled'),
        Output({'type': 'comparison-heatmap-full-scale', 'group': MATCH}, 'disabled'),
        Output({'type': 'comparison-overlay-toggle', 'group': MATCH}, 'disabled'),
        Input({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
    )
    def _toggle_comparison_range_controls(selected_paths):
        """Enable range controls only when this group has a selection."""
        has_selection = bool(_comparison_entries_from_selected(selected_paths))
        disabled = not has_selection
        return disabled, disabled, disabled, disabled, disabled, disabled

    @app.callback(
        Output({'type': 'comparison-project-picker', 'group': MATCH}, 'options'),
        Output({'type': 'comparison-project-picker', 'group': MATCH}, 'value'),
        Input('comparison-files-store', 'data'),
        Input('projects-store', 'data'),
        State({'type': 'comparison-project-picker', 'group': MATCH}, 'value'),
    )
    def _update_comparison_project_picker(files, projects_store, current_value):
        """Update items in the project picker when files/projects change."""
        from .helpers import get_project_options

        all_entries = _comparison_entries(files, list_vtk_files())
        options = get_project_options(all_entries)
        allowed = {o.get('value') for o in options or []}

        value = current_value if current_value in allowed else None
        active = (projects_store or {}).get('active')
        if value is None and active in allowed:
            value = active

        return options, value

    @app.callback(
        Output({'type': 'comparison-vtk-picker', 'group': MATCH}, 'options'),
        Input({'type': 'comparison-project-picker', 'group': MATCH}, 'value'),
        Input('comparison-files-store', 'data'),
    )
    def _filter_comparison_files_by_project(selected_project, files):
        """Filter the file picker options based on the selected project."""
        from pathlib import Path
        all_files = _comparison_entries(files, list_vtk_files())
        # Group by comparison group (we only need the current group but we don't have it explicitly passed)
        # However, list_vtk_files returns paths, we can just process them locally.
        
        # Actually, let's look at how build_comparison_content does it.
        # It calls list_vtk_files() and then _group_comparison_entries.
        # But we are inside a callback for a specific group.
        # We need to preserve the group context.
        # The 'files' input contains uploaded comparison files.
        # We need to re-generate the full list of options for this group.
        
        # Since we don't easily have 'group' here, we have to rely on logic.
        # But wait, looking at the layout, the picker is strictly for VTK files usually?
        # No, it's for the specific group.
        
        # Better approach: 
        # The UI builder already filtered 'available_group_entries' for the specific group.
        # We should probably do the same here.
        # But we don't know the group name here (MATCH).
        # Actually, MATCH gives us the id with the group.
        
        # MATCH gives us the output ID with the group, regardless of what triggered it.
        if not ctx.outputs_list:
             raise PreventUpdate
        
        # ctx.outputs_list is a list (single output) or list of lists (multi output)
        # Here we have a single output (options list).
        # It should be a dict: {'id': {'group': ..., 'type': ...}, 'property': ...}
        output_item = ctx.outputs_list[0] if isinstance(ctx.outputs_list, list) else ctx.outputs_list
        # If multiple outputs, it might be a list of dicts. But here just one.
        # Check structure
        if isinstance(output_item, list):
             output_item = output_item[0]
             
        group = output_item['id']['group']
        
        # Get all available entries globally
        all_entries = _comparison_entries(files, list_vtk_files())

        grouped = _group_comparison_entries(all_entries)

        group_entries = grouped.get(group, [])
        
        filtered_entries = []
        if not selected_project:
            filtered_entries = group_entries
        else:
            # Extract project name from "Project/VTK" format if needed
            project_name = selected_project
            if '/' in selected_project:
                project_name = selected_project.split('/')[0]

            for e in group_entries:
                path_obj = Path(e.get('path') or '')
                parts = list(path_obj.parts)
                # Check if this file belongs to the selected project
                # 1. Standard: "Project1/VTK/file.vts"
                # 2. Custom: "MyFolder/file.vts" -> Project is MyFolder
                is_match = False

                # Check standard structure first
                found_vtk_structure = False
                for idx, part in enumerate(parts):
                    if part.lower() == 'vtk' and idx > 0:
                        if parts[idx - 1] == project_name:
                            is_match = True
                        found_vtk_structure = True
                        break

                # Check simple parent structure if not matched via standard structure
                if not is_match and not found_vtk_structure:
                    if len(parts) > 1 and parts[-2] == project_name:
                        is_match = True

                if is_match:
                    filtered_entries.append(e)

        def _label_for(e):
            name = e.get('name') or Path(e.get('path') or '').name
            if e.get('source') == 'comparison':
                return f"{name} (Comparison)"
            # Simplify label if project selected (remove project prefix)?
            # Or keep it consistent. Let's keep consistent for now.
            p = Path(e.get('path') or '')
            parts = list(p.parts)
            proj = None
            
            # 1. Standard
            for idx, part in enumerate(parts):
                if part.lower() == 'vtk' and idx > 0:
                    proj = parts[idx - 1]
                    break
            
            # 2. Custom (Parent folder)
            if not proj and len(parts) > 1:
                proj = parts[-2]
                
            if selected_project and proj == selected_project:
                return name
            return f"{proj}/{name}" if proj else name

        return [{'label': _label_for(e), 'value': e['path']} for e in filtered_entries]

    @app.callback(
        Output({'type': 'comparison-heatmap-range-min', 'group': MATCH}, 'value'),
        Output({'type': 'comparison-heatmap-range-max', 'group': MATCH}, 'value'),
        Output({'type': 'comparison-range-selection', 'group': MATCH}, 'data'),
        Output({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'value'),
        Output({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'min'),
        Output({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'max'),
        Output({'type': 'comparison-heatmap-full-scale', 'group': MATCH}, 'checked'),
        Input({'type': 'comparison-heatmap-reset', 'group': MATCH}, 'n_clicks'),
        Input({'type': 'comparison-graph', 'group': MATCH, 'file': ALL}, 'clickData'),
        Input({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-selected-files-store', 'group': MATCH}, 'data'),
        Input({'type': 'comparison-heatmap-field', 'group': MATCH}, 'value'),
        State({'type': 'comparison-heatmap-range-min', 'group': MATCH}, 'value'),
        State({'type': 'comparison-heatmap-range-max', 'group': MATCH}, 'value'),
        State('comparison-files-store', 'data'),
        State({'type': 'comparison-range-selection', 'group': MATCH}, 'data'),
        State({'type': 'comparison-heatmap-rows', 'group': MATCH}, 'id'),
        State({'type': 'comparison-heatmap-full-scale', 'group': MATCH}, 'checked'),
        State({'type': 'comparison-controls-store', 'group': MATCH}, 'data'),
        prevent_initial_call=True
    )
    def _update_comparison_range(reset_clicks, clicks, slider_values, selected_paths, field, input_min, input_max, files, store_data, rows_id, full_scale_checked, controls_store):
        """Handle range updates from reset, graph clicks, slider, file selection, or scalar change."""
        group = rows_id.get('group') if isinstance(rows_id, dict) else None
        group_entries = _comparison_entries_from_selected(selected_paths)
        panels = get_comparison_panels(group_entries)
        panels_for_group = {
            entry.get('path'): panels.get(entry.get('path'))
            for entry in group_entries
            if entry and entry.get('path') in panels
        }
        default_lo, default_hi = (None, None)
        if panels_for_group and field:
            default_lo, default_hi = _comparison_range_defaults(panels_for_group, field)

        triggered = ctx.triggered_id
        print(f"[DEBUG RANGE] Triggered: {triggered}, type={triggered.get('type') if isinstance(triggered, dict) else 'N/A'}")
        if isinstance(triggered, dict):
            t_type = triggered.get('type')
            if t_type in ('comparison-selected-files-store', 'comparison-heatmap-reset', 'comparison-heatmap-field'):
                if not panels_for_group:
                    raise PreventUpdate

                print(f"[DEBUG RANGE] t_type={t_type}, controls_store={controls_store}, input_min={input_min}, input_max={input_max}")

                # For reset button or field change, reset to defaults
                if t_type in ('comparison-heatmap-reset', 'comparison-heatmap-field'):
                    # User explicitly requested reset or changed field - reset to defaults
                    min_val, max_val = _comparison_range_defaults(panels_for_group, field)
                    if min_val is None or max_val is None:
                        raise PreventUpdate
                    print(f"[DEBUG RANGE] User action - resetting to defaults: {min_val} to {max_val}")
                    return (
                        min_val,
                        max_val,
                        {'click_count': 0, 'first_click': None},
                        [min_val, max_val],
                        min_val,
                        max_val,
                        full_scale_checked,
                    )

                # For file selection change, preserve existing range
                if t_type == 'comparison-selected-files-store':
                    # If inputs already have values (from UI initialization), don't overwrite them
                    if input_min is not None and input_max is not None:
                        print(f"[DEBUG RANGE] Inputs already initialized, preventing update")
                        raise PreventUpdate

                    # First-time file selection - set defaults
                    min_val, max_val = _comparison_range_defaults(panels_for_group, field)
                    if min_val is None or max_val is None:
                        raise PreventUpdate
                    print(f"[DEBUG RANGE] First-time file selection - setting defaults: {min_val} to {max_val}")
                    return (
                        min_val,
                        max_val,
                        {'click_count': 0, 'first_click': None},
                        [min_val, max_val],
                        min_val,
                        max_val,
                        full_scale_checked,
                    )


        if isinstance(triggered, dict) and triggered.get('type') == 'comparison-graph':
            triggered_value = ctx.triggered[0].get('value') if ctx.triggered else None
            click_data = triggered_value if triggered_value and 'points' in triggered_value else None
            if not click_data:
                click_list = clicks or []
                for cd in click_list:
                    if cd and 'points' in cd and cd['points']:
                        click_data = cd
                        break
            if not click_data or 'points' not in click_data or not click_data['points']:
                raise PreventUpdate
            try:
                point = click_data['points'][0]
            except (IndexError, KeyError):
                raise PreventUpdate
            z_val = point.get('z')
            if z_val is None:
                raise PreventUpdate
            try:
                z_val = float(z_val)
            except (TypeError, ValueError):
                raise PreventUpdate
            store = store_data or {'click_count': 0, 'first_click': None}
            click_count = store.get('click_count', 0)
            first_click = store.get('first_click')
            if click_count == 0 or first_click is None:
                current_lo = input_min if input_min is not None else default_lo
                current_hi = input_max if input_max is not None else default_hi
                return (
                    current_lo,
                    current_hi,
                    {'click_count': 1, 'first_click': z_val},
                    [current_lo, current_hi],
                    default_lo if default_lo is not None else current_lo,
                    default_hi if default_hi is not None else current_hi,
                    full_scale_checked,
                )
            lo, hi = sorted([first_click, z_val])
            return (
                lo,
                hi,
                {'click_count': 0, 'first_click': None},
                [lo, hi],
                default_lo if default_lo is not None else lo,
                default_hi if default_hi is not None else hi,
                full_scale_checked,
            )

        if triggered == {'type': 'comparison-heatmap-range-slider', 'group': group}:
            if not slider_values or len(slider_values) != 2:
                raise PreventUpdate
            try:
                lo = float(slider_values[0])
                hi = float(slider_values[1])
            except (TypeError, ValueError):
                raise PreventUpdate
            lo, hi = sorted([lo, hi])
            return (
                lo,
                hi,
                {'click_count': 0, 'first_click': None},
                [lo, hi],
                default_lo if default_lo is not None else lo,
                default_hi if default_hi is not None else hi,
                full_scale_checked,
            )

        raise PreventUpdate

    @app.callback(
        Output({'type': 'comparison-controls-store', 'group': MATCH}, 'data'),
        Input({'type': 'comparison-heatmap-field', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-heatmap-range-min', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-heatmap-range-max', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-heatmap-palette', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-heatmap-full-scale', 'group': MATCH}, 'checked'),
        Input({'type': 'comparison-overlay-toggle', 'group': MATCH}, 'checked'),
        Input({'type': 'comparison-heatmap-range-slider', 'group': MATCH}, 'value'),
        prevent_initial_call=True
    )
    def _save_comparison_group_controls(field, range_min, range_max, palette, full_scale, overlay_checked, slider_range):
        """Persist control values per comparison group."""
        return {
            'scalar': field,
            'range_min': range_min,
            'range_max': range_max,
            'palette': palette,
            'full_scale': bool(full_scale),
            'interfaces_overlay_visible': bool(overlay_checked),
            'slider_range': slider_range,
        }

    @app.callback(
        Output({'type': 'comparison-add-path-input', 'group': MATCH}, 'value'),
        Input({'type': 'comparison-browse-btn', 'group': MATCH}, 'n_clicks'),
        prevent_initial_call=True
    )
    def _comparison_browse_folder(n_clicks):
        """Open system folder dialog via easygui or plyer."""
        # Try easygui first
        try:
            import easygui
            # Check for tkinter issue early if possible, or let it throw
            path = easygui.diropenbox(title="Select Folder containing VTK files")
            if path:
                return path
        except ImportError as e:
            pass # Try next
        except Exception as e:
            # If tkinter missing, try plyer
            pass

        # Try plyer
        try:
            from plyer import filechooser
            # choose_dir returns a list of paths
            selection = filechooser.choose_dir(title="Select Folder containing VTK files")

            if selection and len(selection) > 0:
                return selection[0]
        except ImportError:
            pass
        except Exception as e:
            return f"Error with plyer: {e}"

        return "Error: Please install 'plyer' (pip install plyer) to use Browse."
        
        return no_update

    @app.callback(
        Output('comparison-files-store', 'data', allow_duplicate=True),
        Output({'type': 'comparison-add-path-status', 'group': ALL}, 'children'),
        Input({'type': 'comparison-add-path-btn', 'group': ALL}, 'n_clicks'),
        State({'type': 'comparison-add-path-input', 'group': ALL}, 'value'),
        State('comparison-files-store', 'data'),
        prevent_initial_call=True
    )
    def _comparison_add_path(n_clicks_list, path_val_list, current_store):
        """Add files from valid folder path to store. Uses ALL to allow global store update."""
        import os
        from pathlib import Path
        
        # Determine which button triggered
        trig = ctx.triggered_id
        if not trig or not isinstance(trig, dict) or 'group' not in trig:
            return no_update, [no_update] * len(n_clicks_list)

        group_triggered = trig['group']
        
        # Find index of triggered group to get corresponding input value and set corresponding output
        # ctx.inputs_list[0] corresponds to n_clicks inputs. They are strictly ordered?
        # Dash provides list of inputs. We can rely on ctx.triggered_id to identify key, 
        # but to map to the inputs list, we might need to iterate or zip.
        # Actually, simpler: we need to produce a list of outputs for 'children' component.
        # The list order matches the order of found components in the DOM?
        # Dash guarantees order of ALL outputs matches order of ALL inputs IF they are same set? Not necessarily.
        # But commonly we just return a list.
        # Wait, for the STATUS output, we need to correct index.
        
        # Strategy: Map inputs by group ID to easily find value.
        # n_clicks_list and path_val_list are lists of values.
        # We need the dictionary inputs to map group -> value.
        
        # ctx.inputs_list is clearer.
        # ctx.inputs_list[0] is list of dicts for n_clicks: [{'id': ..., 'value': ...}, ...]
        # ctx.states_list[0] is list of dicts for path_input: [{'id': ..., 'value': ...}, ...]
        
        path_map = {}
        # Comparison-add-path-input state list is index 0 of states_list?
        # State args: 1. Input arg: 1.
        
        # Safe way: enumerate ctx.states_list[0]
        # But passing n_clicks_list, path_val_list gives just values.
        # Let's inspect ctx structure if needed, or re-construct map.
        # Better: use ctx.states_list to find the value for the triggered group.
        
        triggered_path = None
        for i, item in enumerate(ctx.states_list[0]):
            if item['id']['group'] == group_triggered:
                triggered_path = path_val_list[i]
                break
        
        # Find index of triggered group to get corresponding input value and set corresponding output
        # ctx.outputs_list[1] is the list of dicts for the status outputs.
        outputs_list = ctx.outputs_list[1] if len(ctx.outputs_list) > 1 else []
        status_outputs = [no_update] * len(outputs_list)
        
        output_idx = -1
        for i, item in enumerate(outputs_list):
            if item['id']['group'] == group_triggered:
                output_idx = i
                break
        
        if output_idx == -1:
            # Should not happen if trigger exists
            return no_update, [no_update] * len(n_clicks_list)

        if not triggered_path:
            status_outputs[output_idx] = "Please enter or select a path."
            return no_update, status_outputs
        
        p = Path(triggered_path)
        if not p.exists() or not p.is_dir():
             status_outputs[output_idx] = f"Invalid directory: {triggered_path}"
             return no_update, status_outputs
            
        # Scan for VTK files
        found_files = []
        try:
            for f in os.listdir(p):
                if f.lower().endswith(('.vtk', '.vti', '.vtp', '.vtr', '.vts')):
                    full_path = str(p / f)
                    if os.path.isfile(full_path):
                        found_files.append(full_path)
            found_files.sort()
        except Exception as e:
            status_outputs[output_idx] = f"Error scanning: {e}"
            return no_update, status_outputs
            
        if not found_files:
            status_outputs[output_idx] = "No VTK files found in this folder."
            return no_update, status_outputs

        # Update store
        store_data = current_store or []
        # Ensure it is a list
        if not isinstance(store_data, list):
             store_data = []
             
        # Add new files, avoiding duplicates?
        existing_set = set(store_data)
        new_files = [f for f in found_files if f not in existing_set]
        updated_store = store_data + new_files
        
        status_outputs[output_idx] = f"Added {len(new_files)} files ({len(found_files) - len(new_files)} skipped)."
        
        return updated_store, status_outputs

    # Note: comparison-content rendering is managed by TabCallbackManager so Multi View can
    # have its own "Add Panel" + tab state separate from Single View.
