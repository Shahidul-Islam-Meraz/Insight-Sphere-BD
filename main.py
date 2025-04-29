import csv
import os
import sqlite3
import uuid
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Should be more secure in production

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database setup
def init_db():
    with sqlite3.connect('admins.db') as conn:
        c = conn.cursor()
        # Admin table
        c.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                designation TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                cv_filename TEXT,
                certificate_filename TEXT,
                is_approved INTEGER DEFAULT 0,
                is_super INTEGER DEFAULT 0
            )
        ''')
        # Event table
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                event_date TEXT,
                max_participants INTEGER,
                cost REAL,
                payment_method TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        # Registration table
        c.execute('''
            CREATE TABLE IF NOT EXISTS registrations (
                id TEXT PRIMARY KEY,
                event_id TEXT,
                name TEXT,
                email TEXT,
                phone TEXT,
                registration_time TEXT,
                is_paid INTEGER DEFAULT 0,
                FOREIGN KEY (event_id) REFERENCES events(id)
            )
        ''')
        # Insert first admin if not already there
        c.execute("SELECT * FROM admins WHERE is_super=1")
        if not c.fetchone():
            c.execute('''
                INSERT INTO admins (id, full_name, phone, address, designation, password_hash, is_approved, is_super)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()),
                'First Admin',
                '01000000000',
                'Head Office',
                'Director',
                generate_password_hash('admin123'),
                1,
                1
            ))
        conn.commit()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Admin Registration
@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        data = request.form
        files = request.files

        full_name = data['full_name']
        phone = data['phone']
        address = data['address']
        designation = data['designation']
        password = data['password']

        # File uploads
        cv = files['cv']
        cert = files['certificate']

        if not (cv and allowed_file(cv.filename)) or not (cert and allowed_file(cert.filename)):
            flash('Please upload only PDF files for CV and Certificate.')
            return redirect(request.url)

        cv_filename = secure_filename(f"cv_{uuid.uuid4()}.pdf")
        cert_filename = secure_filename(f"cert_{uuid.uuid4()}.pdf")
        cv.save(os.path.join(app.config['UPLOAD_FOLDER'], cv_filename))
        cert.save(os.path.join(app.config['UPLOAD_FOLDER'], cert_filename))

        admin_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)

        with sqlite3.connect('admins.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO admins (id, full_name, phone, address, designation, password_hash, cv_filename, certificate_filename) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (admin_id, full_name, phone, address, designation, password_hash, cv_filename, cert_filename))
            conn.commit()

        flash("Registration successful! Awaiting approval.")
        return redirect(url_for('admin_login'))

    return render_template('admin_register.html')

# Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']

        with sqlite3.connect('admins.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM admins WHERE phone=?", (phone,))
            admin = c.fetchone()

        if admin and check_password_hash(admin[5], password):
            if admin[8] == 1:
                session['admin_id'] = admin[0]
                session['is_super'] = bool(admin[9])
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Account not yet approved.")
        else:
            flash("Invalid credentials.")

    return render_template('admin_login.html')

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    return render_template('admin_dashboard.html', is_super=session.get('is_super'))

# Create Event (Admin)
@app.route('/admin/create_event', methods=['GET', 'POST'])
def create_event():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        data = request.form
        event_id = str(uuid.uuid4())
        title = data['title']
        description = data['description']
        event_date = data['event_date']
        max_participants = int(data['max_participants'])
        cost = float(data['cost']) if data['cost'] else 0.0
        payment_method = data['payment_method']
        is_active = 1 if data.get('is_active') == 'on' else 0

        with sqlite3.connect('admins.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO events (id, title, description, event_date, max_participants, cost, payment_method, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (event_id, title, description, event_date, max_participants, cost, payment_method, is_active))
            conn.commit()

        flash("Event created successfully!")
        return redirect(url_for('admin_dashboard'))

    return render_template('create_event.html')

# API to fetch active events for registration dropdown
@app.route('/api/active_events')
def active_events():
    with sqlite3.connect('admins.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id, title FROM events WHERE is_active=1")
        events = c.fetchall()
    return jsonify(events)

# Logout
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
