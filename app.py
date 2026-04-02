from flask import Flask, request, jsonify, render_template
import pymysql
import re
import requests
import os

app = Flask(__name__)

def get_db_connection():
    return pymysql.connect(
        host=os.environ.get('MYSQLHOST'),
        user=os.environ.get('MYSQLUSER'),
        password=os.environ.get('MYSQLPASSWORD'),
        database=os.environ.get('MYSQLDATABASE'),
        port=int(os.environ.get('MYSQLPORT', 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_to_admin(name, phone, whatsapp):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing.")
        return
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
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram status: {response.status_code}")
    except Exception as e:
        print(f"Telegram failed: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    name     = data.get('name', '').strip()
    phone    = data.get('phone', '').strip()
    whatsapp = data.get('whatsapp', '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if not re.match(r'^\+?[\d\s\-]{10,}$', phone):
        return jsonify({'error': 'Invalid phone number'}), 400
    if not re.match(r'^\+?[\d\s\-]{10,}$', whatsapp):
        return jsonify({'error': 'Invalid WhatsApp number'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO contacts (name, phone, whatsapp) VALUES (%s, %s, %s)",
            (name, phone, whatsapp)
        )
        conn.commit()
        cur.close()
        conn.close()
        send_telegram_to_admin(name, phone, whatsapp)
        return jsonify({'message': 'Success!', 'name': name}), 200
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({'error': 'Database connection failed'}), 500

@app.route('/contacts', methods=['GET'])
def get_contacts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM contacts ORDER BY created_at DESC")
        contacts = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(contacts), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
