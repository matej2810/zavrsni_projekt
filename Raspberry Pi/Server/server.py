from flask import Flask, request, jsonify
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'gym_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'gym_management')

def get_db_connection():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME)

@app.route('/check_uid', methods=['GET'])
def check_uid():
    uid = request.args.get('uid')
    if not uid:
        return jsonify({"status": "deny"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, entry_count FROM members WHERE rfid_card = %s", (uid,))
    member = cursor.fetchone()

    if member:
        role, entry_count = member
        if role == "staff":
            response = {"status": "allow"}
        elif role == "member" and entry_count < 3:
            cursor.execute("UPDATE members SET entry_count = entry_count + 1 WHERE rfid_card = %s", (uid,))
            conn.commit()
            response = {"status": "allow"}
        else:
            response = {"status": "deny"}
    else:
        response = {"status": "deny"}

    cursor.close()
    conn.close()
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='192.168.4.1', port=5000)
