"""
Floating AI chat widget — fixed bottom-right, global across all tabs.
Toggle is handled by JS (instant, no round-trip).
"""
from dash import html, dcc


def build_floating_chat():
    """Build the floating chat button + collapsible panel."""
    return html.Div([
        # ── Chat panel (above the button, hidden by default) ───────────────
        # Position controlled entirely by JS toggle — no Python callback needed
        html.Div([
            # Header
            html.Div([
                html.Div([
                    html.Span("✦", className="fchat-header-icon"),
                    html.Span("AI Assistant", className="fchat-header-title"),
                ], className="fchat-header-left"),
                html.Div([
                    html.Button("🗑", id="fchat-clear-btn", n_clicks=0,
                                className="fchat-action-btn", title="Clear chat"),
                    html.Button("", id="fchat-close-btn", n_clicks=0,
                                className="fchat-action-btn opview-image-close-btn", title="Close"),
                ], className="fchat-header-right"),
            ], className="fchat-header"),

            # Messages list
            html.Div(
                id="fchat-messages",
                children=[html.Div("Ask me anything…", className="fchat-placeholder")],
                className="fchat-messages",
            ),

            # Input row
            html.Div([
                dcc.Input(
                    id="fchat-input",
                    type="text",
                    placeholder="Ask anything...",
                    n_submit=0,
                    className="fchat-input",
                    debounce=False,
                    autoComplete="off",
                ),
                html.Button("↑", id="fchat-send-btn", n_clicks=0,
                            className="fchat-send-btn"),
            ], className="fchat-input-area"),

            # Data bridges (dcc.Input so JS can read/write via el.value)
            dcc.Input(id="fchat-history",  type="text", value="[]",  style={"display": "none"}),
            dcc.Input(id="fchat-pending",  type="text", value="",    style={"display": "none"}),
            dcc.Input(id="fchat-code-map", type="text", value="{}",  style={"display": "none"}),
            dcc.Input(id="fchat-insert",   type="text", value="",    style={"display": "none"}),
        ], id="fchat-panel", className="fchat-panel"),

        # ── Toggle bubble (always visible) ────────────────────────────────
        html.Button(
            "💬",
            id="fchat-toggle-btn",
            n_clicks=0,
            className="fchat-toggle-btn",
            title="AI Assistant",
        ),
    ], className="fchat-container")
