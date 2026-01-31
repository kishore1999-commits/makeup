import os
from flask import Flask, request, jsonify, send_from_directory, Response
import psycopg2
from datetime import datetime
import csv
import io
import requests
import resend

app = Flask(__name__, static_folder='.')

NOTIFICATION_EMAIL = "Mua.supriya15@gmail.com"

def get_resend_credentials():
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    repl_identity = os.environ.get('REPL_IDENTITY')
    web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')
    
    if repl_identity:
        x_replit_token = 'repl ' + repl_identity
    elif web_repl_renewal:
        x_replit_token = 'depl ' + web_repl_renewal
    else:
        return None, None
    
    try:
        response = requests.get(
            f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=resend',
            headers={
                'Accept': 'application/json',
                'X_REPLIT_TOKEN': x_replit_token
            }
        )
        data = response.json()
        connection = data.get('items', [{}])[0] if data.get('items') else {}
        settings = connection.get('settings', {})
        return settings.get('api_key'), settings.get('from_email')
    except Exception as e:
        print(f"Error getting Resend credentials: {e}")
        return None, None

def send_notification_email(name, email, phone, message):
    try:
        api_key, from_email = get_resend_credentials()
        if not api_key or not from_email:
            print("Resend not configured, skipping email notification")
            return False
        
        resend.api_key = api_key
        
        html_content = f"""
        <h2>New Enquiry from Telugu Bridal Artistry Website</h2>
        <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
            <tr style="background-color: #f7e7ce;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Name</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">{name}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Email</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;"><a href="mailto:{email}">{email}</a></td>
            </tr>
            <tr style="background-color: #f7e7ce;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Mobile</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;"><a href="tel:{phone}">{phone}</a></td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Message</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">{message}</td>
            </tr>
        </table>
        <p style="color: #666; margin-top: 20px;">This enquiry was submitted through your website.</p>
        """
        
        resend.Emails.send({
            "from": from_email,
            "to": [NOTIFICATION_EMAIL],
            "subject": f"New Enquiry from {name}",
            "html": html_content
        })
        
        print(f"Email notification sent to {NOTIFICATION_EMAIL}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS enquiries (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('''
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='enquiries' AND column_name='phone') THEN
                ALTER TABLE enquiries ADD COLUMN phone VARCHAR(50);
            END IF;
        END $$;
    ''')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/', methods=['GET'])
def index():
    response = send_from_directory('.', 'index.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/<path:path>')
def static_files(path):
    response = send_from_directory('.', path)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/enquiry', methods=['POST'])
def submit_enquiry():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        message = data.get('message', '').strip()
        
        if not name or not email or not message:
            return jsonify({'error': 'All fields are required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO enquiries (name, email, phone, message) VALUES (%s, %s, %s, %s)',
            (name, email, phone, message)
        )
        conn.commit()
        cur.close()
        conn.close()
        
        send_notification_email(name, email, phone, message)
        
        return jsonify({'success': True, 'message': 'Enquiry submitted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enquiries', methods=['GET'])
def get_enquiries():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, name, email, phone, message, created_at FROM enquiries ORDER BY created_at DESC')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        enquiries = []
        for row in rows:
            enquiries.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'phone': row[3],
                'message': row[4],
                'created_at': row[5].isoformat() if row[5] else None
            })
        
        return jsonify(enquiries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/enquiries/export', methods=['GET'])
def export_enquiries():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, name, email, phone, message, created_at FROM enquiries ORDER BY created_at DESC')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Email', 'Mobile Number', 'Message', 'Submitted At'])
        for row in rows:
            writer.writerow([
                row[0],
                row[1],
                row[2],
                row[3] or '',
                row[4],
                row[5].strftime('%Y-%m-%d %H:%M:%S') if row[5] else ''
            ])
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=enquiries.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
