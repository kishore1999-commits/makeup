import os
from flask import Flask, request, jsonify, send_from_directory, Response
import psycopg2
from datetime import datetime
import csv
import io

app = Flask(__name__, static_folder='.')

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
