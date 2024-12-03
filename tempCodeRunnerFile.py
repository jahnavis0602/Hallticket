from flask import Flask, request, send_file, render_template, redirect, url_for, session
from fpdf import FPDF
import os
import qrcode

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Admin credentials (hardcoded for simplicity; use a database in production)
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123'
}

# Route for the homepage (front page)
@app.route('/')
def home():
    return render_template('frontpage.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check credentials
        if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
            session['admin_logged_in'] = True
            return redirect(url_for('index'))  # Redirect to the home page after login
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

generated_usns = set()


@app.route('/index')
def index():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))  # Redirect to login page if not logged in
    return render_template('index.html')

@app.route('/add_student', methods=['POST'])
def add_student():
    # Collect form data
    name = request.form['name']
    address = request.form['address']
    usn = request.form['usn']
    room_no = request.form['room_no']
    exam_center = request.form['exam_center']

    # Check if the USN is already used
    if usn in generated_usns:
        return "Error: Hall ticket for this USN has already been generated!", 400

    # Add USN to the set
    generated_usns.add(usn)


    # Collect exam subjects, dates, and timings
    subjects = []
    for i in range(1, 6):
        subjects.append({
            "date": request.form[f"date{i}"],
            "subject": request.form[f"subject{i}"],
            "timing": request.form[f"timing{i}"]
        })

    # Save uploaded photo
    photo = request.files['student_image']
    photo_path = os.path.join('uploads', photo.filename)
    photo.save(photo_path)

    # Generate QR code
    qr_data = f"Name: {name}\nUSN: {usn}\nAddress: {address}\nExam Center: {exam_center}\nRoom no:{room_no}"
    qr_code_path = 'uploads/qr_code.png'
    qr = qrcode.make(qr_data)
    qr.save(qr_code_path)

    # Generate hall ticket PDF
    pdf_path = 'hall_ticket.pdf'
    generate_hall_ticket({
        "name": name,
        "address": address,
        "usn":usn,
        "room_no": room_no,
        "exam_center": exam_center,
        "subjects": subjects
    }, photo_path, qr_code_path, pdf_path)

    # Serve the generated PDF
    return send_file(pdf_path, as_attachment=True)

def generate_hall_ticket(data, photo_path, qr_code_path, output_path):
    pdf = FPDF()
    pdf.add_page()

    # Header
    pdf.set_fill_color(80, 200, 120)#green bg
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "GOVERNMENT ENGINEERING COLLEGE, HASSAN", ln=True, align='C')
    pdf.cell(0, 10, "ADMISSION TICKET FOR SEM END EXAMS- 2024", ln=True, align='C')
    pdf.ln(10)

    # Institution logo (optional, placeholder for now)
    pdf.image(r"C:\Users\jahna\Downloads\jaanu\logo_left.jpg", 10, 5, 30)

    # Student photo
    pdf.image(photo_path, 160, 45, 30)  # Top-right position for the photo

    # Student details
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Name: {data['name']}", ln=True)
    pdf.cell(0, 10, f"Address: {data['address']}", ln=True)
    pdf.cell(0, 10, f"USN: {data['usn']}", ln=True)
    pdf.cell(0, 10, f"Room number: {data['room_no']}", ln=True)
    pdf.cell(0, 10, f"Exam center: {data['exam_center']}", ln=True)
    pdf.ln(5)
    

# Exam timetable
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Exam Timetable", ln=True, align='C')
    pdf.set_fill_color(255, 218, 185)
    pdf.cell(50, 10, "Date", border=1, fill=True, align='C')
    pdf.cell(60, 10, "Subject", border=1, fill=True, align='C')
    pdf.cell(40, 10, "Timing", border=1, fill=True, align='C')
    pdf.cell(40, 10, "Invigilator's Sign", border=1, fill=True, align='C')  # New column
    pdf.ln()
    pdf.set_font('Arial', '', 12)

    for subject in data['subjects']:
        pdf.cell(50, 10, subject['date'], border=1, align='C')
        pdf.cell(60, 10, subject['subject'], border=1, align='C')
        pdf.cell(40, 10, subject['timing'], border=1, align='C')
        pdf.cell(40, 10, '', border=1, align='C')  # Empty cell for invigilator's sign
        pdf.ln()

    
    # QR code
    pdf.ln(10)
    pdf.image(qr_code_path, x=80, y=pdf.get_y(), w=50)  # Centered QR code

    # Adjust position of the registrar's signature
    pdf.set_y(-40)  # Move higher by reducing the value (default was -30)
    pdf.set_x(140)  # Align to the right
    pdf.cell(60, 10, txt="HOD's Signature:", ln=False, align="L")
    pdf.line(140, pdf.get_y() + 9, 200, pdf.get_y() + 9)  # Draw signature line
    # Add student's signature (on the left)
    pdf.set_y(-40)  # Same vertical position as the registrar's signature
    pdf.set_x(10)   # Align to the left
    pdf.cell(60, 10, txt="Student's Signature:", ln=False, align="L")
    pdf.line(10, pdf.get_y() + 9, 70, pdf.get_y() + 9)

    # Add instructions
    pdf.add_page()  # Add a new page
    pdf.set_font("Arial", "B", size=12)
    pdf.cell(200, 10, txt="Instructions for the Exam:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, txt=(
    "General Instructions:\n"
    "1.Carry the Hall Ticket: Candidates must bring a printed copy of the hall ticket to the examination hall. Entry without it will not be permitted.\n"
    "2.Photo Identification: Along with the hall ticket, candidates should carry a valid government-issued photo ID (e.g., Aadhaar Card, Passport, or Driving License).\n"
    "3.Reporting Time: Arrive at the examination center at least 30 to 60 minutes before the reporting time mentioned on the hall ticket.\n"
    "4.Examination Venue: Verify the address of the exam center mentioned on the hall ticket and ensure you know how to reach it.\n"
    "5.Entry Closure: Entry to the exam hall will close 15 to 30 minutes before the exam begins. Latecomers will not be allowed.\n"
    "During the Examination:\n"
    "1.Stationery: Bring required items such as pens, pencils, erasers, etc., as specified in the instructions. Sharing of stationery is prohibited.\n"
    "2.Electronic Devices: Mobile phones, calculators, smartwatches, and other electronic gadgets are strictly prohibited inside the exam hall.\n"
    "3.Personal Belongings: Bags, books, and any other personal belongings are not allowed inside the examination hall.\n"
    "4.Hall Ticket Preservation: Keep the hall ticket intact until the examination is over. Do not tamper with or damage it.\n"
    "5.Seat Allotment: Sit only at the seat assigned to you as per the roll number mentioned on the hall ticket."
    ))

   
    # Save the PDF
    pdf.output(output_path)

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')  # Create directory for storing uploaded files
    app.run(debug=True)
