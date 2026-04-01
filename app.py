from flask import Flask, request, jsonify, render_template
from flask_mysqldb import MySQL
import re
import requests  # for Telegram

app = Flask(__name__)

# ─── XAMPP MySQL Configuration ───────────────────────────────────────────────
import os

app.config['MYSQL_HOST'] = os.environ.get('MYSQLHOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQLUSER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQLPASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQLDATABASE')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQLPORT', 3306))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


# ─── Telegram Config ─────────────────────────────────────────────────────────


TELEGRAM_TOKEN = os.environ.get("8506673108:AAGGrelDXWgx8Vn7rVyoavPuqbFsaxFY4XA")
TELEGRAM_CHAT_ID = os.environ.get("6927424028")


# ─── Telegram Notification Function ──────────────────────────────────────────
def send_telegram_to_admin(name, phone, whatsapp):
    try:
        message = (
            f"🪵 *New Enquiry - Sri VekkaliyammaN Interiors*\n\n"
            f"👤 Name     : {name}\n"
            f"📞 Phone    : {phone}\n"
            f"💬 WhatsApp : {whatsapp}\n\n"
            f"Reply quickly!!!! 🙏"
        )
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        print("Telegram status:", response.status_code)
    except Exception as e:
        print("Telegram notification failed:", e)


# ─── Home Page ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


# ─── Submit Contact Form ──────────────────────────────────────────────────────
@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()

    name     = data.get('name',     '').strip()
    phone    = data.get('phone',    '').strip()
    whatsapp = data.get('whatsapp', '').strip()

    # ── Server-side Validation ──
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    if not re.match(r'^\+?[\d\s\-]{10,}$', phone):
        return jsonify({'error': 'Invalid phone number'}), 400

    if not re.match(r'^\+?[\d\s\-]{10,}$', whatsapp):
        return jsonify({'error': 'Invalid WhatsApp number'}), 400

    # ── Save to Database ──
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO contacts (name, phone, whatsapp) VALUES (%s, %s, %s)",
            (name, phone, whatsapp)
        )
        mysql.connection.commit()
        cur.close()

        # ── Send Telegram to Admin ──
        send_telegram_to_admin(name, phone, whatsapp)

        return jsonify({
            'message': 'Request saved successfully!',
            'name': name
        }), 200

    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500


# ─── View All Contacts ────────────────────────────────────────────────────────
@app.route('/contacts', methods=['GET'])
def get_contacts():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM contacts ORDER BY created_at DESC")
        contacts = cur.fetchall()
        cur.close()
        return jsonify(contacts), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)