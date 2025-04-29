import csv
import os
import sqlite3
import uuid
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
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

    with sqlite3.connect('admins.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id, full_name, phone, address, designation, is_approved FROM admins")
        admins = c.fetchall()

    return render_template('admin_dashboard.html', is_super=session.get('is_super'), admins=admins)

# Approve Admin
@app.route('/admin/approve/<admin_id>')
def approve_admin(admin_id):
    if not session.get('is_super'):
        flash("Access denied.")
        return redirect(url_for('admin_dashboard'))

    with sqlite3.connect('admins.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE admins SET is_approved=1 WHERE id=?", (admin_id,))
        conn.commit()

    flash("Admin approved.")
    return redirect(url_for('admin_dashboard'))

# Reject Admin
@app.route('/admin/reject/<admin_id>')
def reject_admin(admin_id):
    if not session.get('is_super'):
        flash("Access denied.")
        return redirect(url_for('admin_dashboard'))

    with sqlite3.connect('admins.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM admins WHERE id=? AND is_super=0", (admin_id,))
        conn.commit()

    flash("Admin rejected and removed.")
    return redirect(url_for('admin_dashboard'))

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
