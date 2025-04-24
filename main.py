import csv
import uuid
from datetime import datetime

from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        event = request.form.get('event')
        hear_about = request.form.get('hear_about')

        # Conditional fields
        if user_type == 'student':
            institution = request.form.get('institution')
            department = request.form.get('student_department')
            session = request.form.get('session')
            designation = organization = experience = job_department = ""
        else:
            designation = request.form.get('designation')
            organization = request.form.get('organization')
            experience = request.form.get('experience')
            job_department = request.form.get('job_department')
            institution = department = session = ""

        unique_id = str(uuid.uuid4())[:8]

        with open('registrations.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                unique_id, user_type, name, email, phone, event,
                institution, department, session,
                designation, organization, experience, job_department,
                hear_about, "Not Downloaded"
            ])

        return render_template('registration_success.html', unique_id=unique_id)

    return render_template('register.html')

@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        amount = request.form['amount']
        payment_method = request.form['payment_method']
        transaction_id = request.form['transaction_id']

        current_time = datetime.now()
        receipt_no = f"INS-{current_time.strftime('%Y%m%d%H%M%S')}"

        with open('payments.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([receipt_no, name, email, amount, payment_method, transaction_id])

        receipt_data = {
            'receipt_no': receipt_no,
            'date': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'name': name,
            'email': email,
            'amount': amount,
            'payment_method': payment_method,
            'transaction_id': transaction_id
        }
        return render_template('receipt.html', **receipt_data)
    return render_template('payment.html')

@app.route('/certificate', methods=['GET', 'POST'])
def certificate():
    if request.method == 'POST':
        unique_id = request.form['unique_id']

        with open('registrations.csv', mode='r') as file:
            reader = csv.reader(file)
            registrations = list(reader)

        for i, row in enumerate(registrations):
            if row[0] == unique_id:
                certificate_data = {
                    'name': row[2],  # Full Name
                    'event': row[5],  # Course/Event
                    'date': datetime.now().strftime('%B %d, %Y'),
                    'unique_id': unique_id
                }

                registrations[i][14] = "Downloaded"

                with open('registrations.csv', mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(registrations)

                return render_template('certificate.html', certificate_data=certificate_data, error=None)

        return render_template('certificate.html', certificate_data=None, error="Invalid Unique ID. Please check and try again.")

    return render_template('certificate.html', certificate_data=None, error=None)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
