from flask import Flask, render_template, request, redirect, url_for
import os
import ast 
import csv

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
            # Redirect to the /result page with the filename
            return redirect(url_for('result', filename=filename))

        return 'Invalid file type. Please upload a .txt or .csv file.', 400

    return render_template('index.html')

@app.route('/result')
def result():
    filename = "G://sound//hackathon//output.csv"  # Hardcoded path to the output file

    if filename:
        filepath = filename  # Use the hardcoded file path
        data = []

        # Read and process the CSV file
        try:
            with open(filepath, newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    print(f"Row before parsing: {row}")  # Debugging line to inspect the row

                    # Safely evaluate the 'Extracted Entity' column to convert it to a list
                    try:
                        if isinstance(row['Extracted Entity'], str):
                            row['Extracted Entity'] = ast.literal_eval(row['Extracted Entity'])
                            print(f"Extracted Entity after eval: {row['Extracted Entity']}")
                        
                        if isinstance(row['Entity Type'], str):
                            row['Entity Type'] = ast.literal_eval(row['Entity Type'])
                            print(f"Entity Type after eval: {row['Entity Type']}")
                        
                        if isinstance(row['Supporting Evidence'], str):
                            row['Supporting Evidence'] = ast.literal_eval(row['Supporting Evidence'])
                            print(f"Supporting Evidence after eval: {row['Supporting Evidence']}")
                    except Exception as e:
                        print(f"Error parsing row: {row}, Error: {e}")

                    data.append(row)

        except FileNotFoundError:
            return 'File not found.', 404
        except Exception as e:
            return f'Error reading file: {e}', 500

        # Return the result page with the data from the file
        return render_template('result.html', data=data)

    return 'No file uploaded or invalid file.', 400

if __name__ == '__main__':
    app.run(debug=True)