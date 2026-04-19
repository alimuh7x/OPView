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


def main():
    print("[verify][custom-graph] building app layout", flush=True)
    layout = build_app_layout(
        discovered_project_folders={},
        comparison_files=[],
        initial_active_tab=None,
        build_tab_children_func=lambda *_args, **_kwargs: [],
        build_comparison_content_func=lambda *_args, **_kwargs: [],
        allowed_comparison_groups_func=lambda *_args, **_kwargs: set(),
        get_project_folder_options_func=lambda *_args, **_kwargs: [],
        group_projects_by_parent_func=lambda *_args, **_kwargs: {},
        server_session_id="verify-custom-graph",
    )
    print("[verify][custom-graph] layout built", flush=True)
    ids = _collect_ids(layout)
    print(f"[verify][custom-graph] id_count={len(ids)}", flush=True)
    print(f"[verify][custom-graph] has_notebook_state={'notebook-state' in ids}", flush=True)
    notebook_state = None
    stack = [layout]
    while stack:
        component = stack.pop()
        if getattr(component, "id", None) == "notebook-state":
            notebook_state = getattr(component, "data", None)
            break
        children = getattr(component, "children", None)
        if isinstance(children, (list, tuple)):
            stack.extend(children)
        elif children is not None:
            stack.append(children)
    print(f"[verify][custom-graph] notebook_state={notebook_state}", flush=True)


if __name__ == "__main__":
    main()
