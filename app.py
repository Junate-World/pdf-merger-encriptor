import os
import re
import tempfile
import PyPDF2
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename

# Create a Flask instance
app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}\

MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # Max 10MB files
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = 'Junate_World_2024'  # Replace with a real secret key for flash messages

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to sanitize filenames
def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the user uploaded any files
        if 'pdf_files' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        files = request.files.getlist('pdf_files')

        # Check if any file is uploaded
        if not files or all(file.filename == '' for file in files):
            flash('No selected files', 'error')
            return redirect(request.url)

        # Create a PDF merger object
        pdf_merger = PyPDF2.PdfMerger()

        # Process each file
        temp_files = []  # Keep track of the temporary files
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                sanitized_filename = sanitize_filename(filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], sanitized_filename)
                file.save(file_path)

                try:
                    pdf_merger.append(file_path)
                except Exception as e:
                    flash(f"Error merging {filename}: {str(e)}", 'error')
                    return redirect(request.url)
            else:
                flash(f"Invalid file format: {file.filename}. Only PDF files are allowed.", 'error')
                return redirect(request.url)

        # Ask for a password for the merged PDF (Optional)
        password = request.form.get('password')
        
        # Set output file path
        merged_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged_output.pdf')

        try:
            # Write the merged PDF
            with open(merged_pdf_path, 'wb') as output_file:
                pdf_merger.write(output_file)

            # If password is provided, encrypt the merged PDF
            if password:
                with open(merged_pdf_path, 'rb') as output_file:
                    pdf_reader = PyPDF2.PdfReader(output_file)
                    pdf_writer = PyPDF2.PdfWriter()
                    for page in pdf_reader.pages:
                        pdf_writer.add_page(page)
                    pdf_writer.encrypt(password)

                    # Write the encrypted PDF
                    encrypted_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'encrypted_output.pdf')
                    with open(encrypted_pdf_path, 'wb') as encrypted_output_file:
                        pdf_writer.write(encrypted_output_file)

                    # Send encrypted PDF for download
                    return send_file(encrypted_pdf_path, as_attachment=True, download_name="merged_output.pdf")

        except Exception as e:
            flash(f"Error while writing the merged PDF: {str(e)}", 'error')
            return redirect(request.url)

        # Return the merged (non-encrypted) PDF for download
        return send_file(merged_pdf_path, as_attachment=True, download_name="merged_output.pdf")

    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)