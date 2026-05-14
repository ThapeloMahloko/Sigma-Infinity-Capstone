# =========================================================
# TELEGRAM PAGE
# =========================================================

import panel as pn
import requests
import qrcode
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_BOT_USERNAME, COLOR_TEXT_MUTED

# =========================================================
# QR CODE GENERATION
# =========================================================

telegram_link = f"https://t.me/{TELEGRAM_BOT_USERNAME}"

try:
    qr = qrcode.make(telegram_link)
    qr.save("telegram_qr.png")
except:
    pass

# =========================================================
# TELEGRAM FUNCTIONS
# =========================================================

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("TELEGRAM NOT CONFIGURED: missing token or chat id")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
# =========================================================
# Resolve bot username and optionally generate a QR code
# If TELEGRAM_BOT_USERNAME is empty, call getMe to fetch the username at runtime.

            "text": message
        }
        requests.post(url, data=data)
        print("TELEGRAM SENT")
    except Exception as e:
        print("TELEGRAM ERROR:", e)

# =========================================================
# TELEGRAM WIDGETS
# =========================================================

telegram_link = f"https://t.me/{bot_username}" if bot_username else None

telegram_btn_send = pn.widgets.Button(
    name="📨 Send Test Message",
    button_type="primary"
)

def send_test(event):
    send_telegram_message("✅ Smart Farm Connected")
    telegram_result.object = "Test message sent."

telegram_btn_send.on_click(send_test)

# =========================================================
# TELEGRAM PAGE LAYOUT
# =========================================================

telegram_page = pn.Column(
    pn.pane.HTML("""
    <div class='hero'>
    <div style='font-size:14px;letter-spacing:4px;color:%s;'>TELEGRAM BOT</div>
    <div style='font-size:52px;font-weight:800;color:white;margin-top:10px;'>Smart Farm Bot</div>
    </div>
    """ % COLOR_TEXT_MUTED),

    pn.Row(
        pn.Column(
                    pn.pane.Markdown("""
                    ## Telegram Setup

                    1. Open Telegram
                    2. Scan QR code (if available)
                    3. Start the bot
                    4. Receive live alerts
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
