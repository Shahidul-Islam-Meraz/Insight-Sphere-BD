import csv  # Import csv at the top of your file
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

# Combine the GET and POST methods for the /register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Collect form data
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        event = request.form['event']

        # Save registration data to a CSV file
        with open('registrations.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([fullname, email, phone, event])

        # Render register.html and pass a success message
        return render_template('register.html', message="✅ Registration successful!")

    # For GET request, just render the registration form
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

        # Generate receipt number and current timestamp
        current_time = datetime.now()
        receipt_no = f"INS-{current_time.strftime('%Y%m%d%H%M%S')}"
        
        # Save payment details to CSV
        with open('payments.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([receipt_no, name, email, amount, payment_method, transaction_id])

        # Generate receipt
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

@app.route('/certificate')
def certificate():
    return render_template('certificate.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)