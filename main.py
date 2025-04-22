import csv  # Import csv at the top of your file

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

@app.route('/payment')
def payment():
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