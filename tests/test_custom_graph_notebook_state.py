from ui.layout import build_app_layout


def _collect_ids(component):
    ids = []
    component_id = getattr(component, "id", None)
    if component_id is not None:
        ids.append(component_id)

    children = getattr(component, "children", None)
    if children is None:
        return ids
    if isinstance(children, (list, tuple)):
        for child in children:
            ids.extend(_collect_ids(child))
    else:
        ids.extend(_collect_ids(children))
    return ids


def _find_component(component, target_id):
    if getattr(component, "id", None) == target_id:
        return component
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            found = _find_component(child, target_id)
            if found is not None:
                return found
    elif children is not None:
        return _find_component(children, target_id)
    return None


def test_app_layout_includes_global_notebook_state_for_custom_graph():
    layout = build_app_layout(
        discovered_project_folders={},
        comparison_files=[],
        initial_active_tab=None,
        build_tab_children_func=lambda *_args, **_kwargs: [],
        build_comparison_content_func=lambda *_args, **_kwargs: [],
        allowed_comparison_groups_func=lambda *_args, **_kwargs: set(),
        get_project_folder_options_func=lambda *_args, **_kwargs: [],
        group_projects_by_parent_func=lambda *_args, **_kwargs: {},
        server_session_id="test-custom-graph",
    )

    ids = _collect_ids(layout)
    notebook_state = _find_component(layout, "notebook-state")

    assert "notebook-state" in ids
    assert notebook_state is not None
    assert notebook_state.data["variables"] == {}
    assert notebook_state.data["array_variables"] == {}
