from flask import Flask, render_template, request, redirect, url_for,send_from_directory
import os
import csv 
import json
from io import StringIO,BytesIO  
from flask import send_file
from modules.read_input_file import extract_input_file_details
from modules.reputation_risk import fraud_detection, get_entity_details
from modules.extract_entity import entity_extraction



app = Flask(__name__)

# Set the folder where files will be uploaded
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'csv'}

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route to display the upload form
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # entity_extraction("Google")
        # #name, type, Saction, SReason, rep_risk_score, RReason
        # reputation_entities = get_entity_details("Google")
        # fraud_detection(reputation_entities,"Google")
        #name, rep_risk_score, RReason 

        if 'file' not in request.files:
            return 'No file part', 400

        file = request.files['file']
        
        if file.filename == '':
            return 'No selected file', 400

        if file and allowed_file(file.filename):
            filename = file.filename
            # Save the uploaded file in the uploads folder
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            payerName, receiverName, transactionNotes = extract_input_file_details(file_path)
            for payerName, receiverName, transactionNotes in zip(payerName, receiverName, transactionNotes):
                print(f"PayerName: {payerName}, ReceiverName: {receiverName}, Transaction Notes: {transactionNotes}")
                #extract entities
                print("Extracting entity information....")
                entity_extraction(payerName)
                entity_extraction(receiverName)

                #reptutation risk
                print("Calculating reputation risk...")
                reputation_entities = get_entity_details(payerName)
                fraud_detection(reputation_entities,payerName)

                reputation_entities = get_entity_details(receiverName)
                fraud_detection(reputation_entities,receiverName)

            # Redirect to the /result page with the filename
            return redirect(url_for('result', filename=filename))

        return 'Invalid file type. Please upload a .txt or .csv file.', 400

    return render_template('index.html')

file_name = 'output3.json'

# Get the current working directory
current_directory = os.getcwd()

# Join the current directory with the folder and filename
OUTPUT_FILE_PATH = os.path.join(current_directory, file_name) # Replace with the actual path to your JSON file
print(OUTPUT_FILE_PATH)
@app.route('/result')
def result():
    # Read the data from output.json file
    try:
        with open(OUTPUT_FILE_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        return 'File not found.', 404
    except json.JSONDecodeError:
        return 'Error decoding JSON file.', 500

    # Pass the data to the result template
    return render_template('result.html', data=data)

@app.route('/download_data/<file_format>')
def download_data(file_format):
    try:
        # Read the data from output.json file
        with open(OUTPUT_FILE_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        return 'File not found.', 404
    except json.JSONDecodeError:
        return 'Error decoding JSON file.', 500

    if file_format == 'csv':
        # Generate CSV data
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()

        for row in data:
            # Handle list-to-string conversion (for "Extracted Entity" etc.)
            row['Extracted Entity'] = ', '.join(row['Extracted Entity'])
            row['Entity Type'] = ', '.join(row['Entity Type'])
            row['Supporting Evidence'] = ', '.join(row['Supporting Evidence'])
            writer.writerow(row)

        output.seek(0)  # Rewind the StringIO object to start from the beginning

        # Convert StringIO to BytesIO for sending file
        bytes_io = BytesIO(output.getvalue().encode('utf-8'))

        # Send the generated CSV file to the user for download
        return send_file(bytes_io, mimetype='text/csv', as_attachment=True, download_name='output.csv')

    elif file_format == 'json':
        # Generate JSON data
        output = BytesIO()
        json_data = json.dumps(data, indent=4)  # Convert to JSON string
        output.write(json_data.encode('utf-8'))  # Write the JSON string as bytes (Important step)
        output.seek(0)  # Go to the beginning of the BytesIO buffer
        return send_file(output, mimetype='application/json', as_attachment=True, download_name='output.json')

    return 'Invalid file format requested', 400

@app.route('/show_image_page')
def show_image_page():
    # Specify the image filename you want to show
    image_filename = 'score_image.png'  # Change this to your image file name
    return render_template('image.html', image_filename=image_filename)

@app.route('/transaction')
def transaction():
    return render_template('transaction.html')
@app.route('/play_audio')
def play_audio():
    return render_template('result.html')

@app.route('/static/audio/<filename>')
def download_file(filename):
    # Ensure the file exists and is served correctly from the 'static/audio' folder.
    return send_from_directory(os.path.join(app.root_path, 'static', 'audio'), filename)


if __name__ == '__main__':
    app.run(debug=True)
