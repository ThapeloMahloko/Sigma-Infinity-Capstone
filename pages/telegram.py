# =========================================================
# TELEGRAM PAGE
# =========================================================

import os
import panel as pn
import requests
import qrcode
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_BOT_USERNAME, COLOR_TEXT_MUTED


# =========================================================
# Resolve bot username and optionally generate a QR code
# If TELEGRAM_BOT_USERNAME is empty, call getMe to fetch the username at runtime.
# =========================================================

bot_username = TELEGRAM_BOT_USERNAME or None
if not bot_username and TELEGRAM_BOT_TOKEN:
    try:
        resp = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok") and data.get("result") and data["result"].get("username"):
            bot_username = data["result"]["username"]
    except Exception:
        bot_username = None

telegram_link = f"https://t.me/{bot_username}" if bot_username else None

if telegram_link:
    try:
        qr = qrcode.make(telegram_link)
        qr.save("telegram_qr.png")
    except Exception:
        # non-fatal
        pass


# =========================================================
# TELEGRAM FUNCTIONS & WIDGETS
# =========================================================

telegram_result = pn.pane.Markdown("No messages sent yet.")

telegram_btn_send = pn.widgets.Button(
    name="📨 Send Test Message",
    button_type="primary"
)

def send_telegram_message(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("TELEGRAM NOT CONFIGURED: missing token or chat id")
        telegram_result.object = "Telegram not configured. Add secrets in Space settings."
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
        resp = requests.post(url, data=data, timeout=5)
        if resp.ok:
            telegram_result.object = "Test message sent."
            print("TELEGRAM SENT")
        else:
            telegram_result.object = f"Send failed: {resp.text}"
            print("TELEGRAM ERROR:", resp.text)
    except Exception as e:
        telegram_result.object = f"Exception: {e}"
        print("TELEGRAM ERROR:", e)


def send_test(event):
    send_telegram_message("✅ Smart Farm Connected")


telegram_btn_send.on_click(send_test)


# =========================================================
# TELEGRAM PAGE LAYOUT
# =========================================================

telegram_page = pn.Column(
    pn.pane.HTML(f"""
    <div class='hero'>
    <div style='font-size:14px;letter-spacing:4px;color:{COLOR_TEXT_MUTED};'>TELEGRAM BOT</div>
    <div style='font-size:52px;font-weight:800;color:white;margin-top:10px;'>Smart Farm Bot</div>
    </div>
    """),

    pn.Row(
        pn.Column(
            pn.pane.Markdown("""
            ## Telegram Setup

            1. Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as Space Secrets
            2. Press the test button to send a verification message
            """),

            telegram_btn_send,
            telegram_result,
            css_classes=["section-box"]
        ),

        pn.Column(
            pn.pane.PNG("telegram_qr.png", width=300) if telegram_link and os.path.exists("telegram_qr.png") else pn.pane.Markdown("QR code not available."),
        )
    )
)
