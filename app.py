from flask import Flask, request, send_file, jsonify, render_template, session, redirect
import os
import xml.etree.ElementTree as ET
from io import BytesIO
from google.cloud import storage, firestore
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Konfiguracja Google Cloud Storage
BUCKET_NAME = "xmlproject-448013_cloudbuild"
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# Konfiguracja Firestore dla użytkowników
firestore_client = firestore.Client()
users_collection = firestore_client.collection("users")

@app.route('/')
def home():
    return render_template('index.html')

# Rejestracja użytkownika
@app.route('/register', methods=['POST'])
def register():
    data = request.form
    username = data['username']
    email = data['email']
    password_hash = generate_password_hash(data['password'], method='pbkdf2:sha256')

    users_collection.document(username).set({
        "email": email,
        "password_hash": password_hash,
        "files": []
    })
    return jsonify({'message': 'Registration successful!', 'status': 'success'}), 200

# Logowanie użytkownika
@app.route('/login', methods=['POST'])
def login():
    data = request.form
    user_doc = users_collection.document(data['username']).get()
    
    if user_doc.exists:
        user_data = user_doc.to_dict()
        if check_password_hash(user_data['password_hash'], data['password']):
            session['username'] = data['username']
            return jsonify({'message': 'Login successful!', 'status': 'success'})
    return jsonify({'error': 'Invalid username or password.', 'status': 'error'})

# Przesyłanie pliku XML do Cloud Storage
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Brak pliku w zapytaniu", 400
    file = request.files['file']
    if file.filename == '':
        return "Nie wybrano pliku", 400
    
    blob = bucket.blob(f"xml_files/{session['username']}/{file.filename}")
    blob.upload_from_file(file)
    return f"Plik {file.filename} zapisany w chmurze!", 200

# Pobieranie przetworzonego pliku XML
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    blob = bucket.blob(f"xml_files/{session['username']}/{filename}")
    output = BytesIO()
    blob.download_to_file(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/xml')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
