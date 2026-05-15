# =========================================================
# SMART FARM DASHBOARD - MAIN ENTRY POINT
# =========================================================

import os
import argparse
import panel as pn
import webbrowser
from bokeh.models import CustomJS

from config import PANEL_PORT, PANEL_TITLE
from mqtt_handler import init_mqtt, set_active_doc
from ui_components import hero, refresh_cards, refresh_graph, theme_state, dark_css, light_css, shared_css
from pages.dashboard import dashboard_page
from pages.analytics import analytics_page
from pages.export import export_page
from pages.controls import controls_page
from pages.telegram import telegram_page

# =========================================================
# AUTO OPEN BROWSER
# =========================================================

def _detect_port():
    # Priority: --port CLI arg > PORT env var > PANEL_PORT from config
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--port", type=int, help="port to serve on")
    args, _ = parser.parse_known_args()
    if args.port:
        return args.port
    env = os.environ.get("PORT")
    if env:
        try:
            return int(env)
        except ValueError:
            pass
    return PANEL_PORT

# resolved port used by the Docker image / Hugging Face Spaces
PORT = _detect_port()

def open_browser():
    # Skip opening browser in headless/container environments
    try:
        webbrowser.open_new(f"http://localhost:{PORT}")
    except Exception as e:
        print(f"ℹ Browser auto-open skipped: {e}")

def init_theme():
    """Initialize theme class on page load"""
    doc = pn.state.curdoc
    if doc:
                initial_mode = theme_state.mode

                # Inject our dashboard CSS into the client document so theme classes take effect
                import json
                css_content = json.dumps(dark_css + light_css + shared_css)
                doc.js_on_event(
                        "document_ready",
                        CustomJS(code=f"""
(function(){{
    try {{
        if(!document.getElementById('sf-dynamic-css')){{
            const s = document.createElement('style');
            s.id = 'sf-dynamic-css';
            s.textContent = {css_content};
            document.head.appendChild(s);
        }}
        const body = document.body;
        body.classList.remove('theme-dark', 'theme-light');
        body.classList.add('theme-{initial_mode}');
    }} catch(e){{ console.warn('theme init error', e); }}
}})();
""")
                )

pn.state.onload(open_browser)
pn.state.onload(init_theme)

# =========================================================
# NAVIGATION
# =========================================================

main_content = pn.Column(
    dashboard_page,
    sizing_mode="stretch_width"
)

def show_dashboard(event=None):
    main_content.clear()
    main_content.append(dashboard_page)

def show_analytics(event=None):
    main_content.clear()
    main_content.append(analytics_page)

def show_export(event=None):
    main_content.clear()
    main_content.append(export_page)

def show_controls(event=None):
    main_content.clear()
    main_content.append(controls_page)

def show_telegram(event=None):
    main_content.clear()
    main_content.append(telegram_page)

# =========================================================
# SIDEBAR BUTTONS
# =========================================================

dashboard_btn = pn.widgets.Button(name="🏠 Dashboard", button_type="success")
analytics_btn = pn.widgets.Button(name="📊 Analytics")
export_btn = pn.widgets.Button(name="🗄 Data Export")
controls_btn = pn.widgets.Button(name="⚙ Controls")
telegram_btn = pn.widgets.Button(name="🤖 Telegram Bot")

# Theme toggle button
def toggle_theme(event=None):
    new_mode = "light" if theme_state.mode == "dark" else "dark"
    theme_state.mode = new_mode
    
    # Refresh cards with new colors
    from ui_components import refresh_cards
    refresh_cards()

theme_btn = pn.widgets.Button(
    name="🌙 Dark Mode",
    button_type="primary",
    width=200
)
theme_btn.js_on_click(code="""
const body = document.body;
const isDark = body.classList.contains('theme-dark');
body.classList.remove('theme-dark', 'theme-light');
body.classList.add(isDark ? 'theme-light' : 'theme-dark');
""")
theme_btn.on_click(toggle_theme)

# Update button text when theme changes
def update_theme_btn_label(*args):
    theme_btn.name = "☀️ Light Mode" if theme_state.mode == "dark" else "🌙 Dark Mode"

theme_state.param.watch(update_theme_btn_label, "mode")

dashboard_btn.on_click(show_dashboard)
analytics_btn.on_click(show_analytics)
export_btn.on_click(show_export)
controls_btn.on_click(show_controls)
telegram_btn.on_click(show_telegram)

# =========================================================
# SIDEBAR
# =========================================================

sidebar = pn.Column(
    pn.pane.Markdown("""
# 🌱 Smart Farm

## Navigation
    """),

    dashboard_btn,
    analytics_btn,
    export_btn,
    controls_btn,
    telegram_btn,

    pn.Spacer(height=20),
    theme_btn,

    pn.Spacer(height=30),

    pn.pane.Markdown("""
## SYSTEM STATUS

🟢 MQTT Connected

🟢 Database Connected

🟢 ESP32 Online
    """),

    css_classes=["sidebar"],
    width=260,
    height=1200
)

# =========================================================
# FINAL LAYOUT
# =========================================================

dashboard = pn.Row(
    sidebar,
    main_content,
    sizing_mode="stretch_width"
)

dashboard.servable()

# =========================================================
# INITIALIZATION & SERVER START
# =========================================================

# Initialize MQTT early (before servable is called)
try:
    init_mqtt()
except Exception as e:
    print(f"⚠ MQTT init warning: {e}")

def register_session_doc():
    doc = pn.state.curdoc
    if doc is None:
        return

    set_active_doc(doc)

    if not getattr(doc, "_smart_farm_refresh_registered", False):
        doc.add_periodic_callback(refresh_live_view, 1000)
        doc._smart_farm_refresh_registered = True

    def prime_live_view():
        refresh_live_view()

    doc.add_next_tick_callback(prime_live_view)


def refresh_live_view():
    doc = pn.state.curdoc
    if doc is None:
        return

    def apply_live_refresh():
        refresh_cards()
        refresh_graph()

    doc.add_next_tick_callback(apply_live_refresh)

pn.state.onload(register_session_doc)


def app():
    register_session_doc()
    return dashboard

if __name__ == "__main__":
    pn.serve(
        app,
        port=PORT,
        show=True,
        title=PANEL_TITLE
    )
