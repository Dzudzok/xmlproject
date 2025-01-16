from flask import Flask, request, send_file, jsonify, render_template, session, redirect
import os
import xml.etree.ElementTree as ET
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 📌 Folder do przechowywania plików (Render obsługuje lokalne przechowywanie)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 📌 Konfiguracja bazy danych SQLite zamiast Firestore
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 📌 Model użytkownika (zastępuje Firestore)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

# 📌 Tworzenie bazy danych, jeśli nie istnieje
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

# 📌 Rejestracja użytkownika
@app.route('/register', methods=['POST'])
def register():
    data = request.form
    username = data['username']
    email = data['email']
    password_hash = generate_password_hash(data['password'], method='pbkdf2:sha256')

    # Sprawdzenie, czy użytkownik już istnieje
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'User already exists.', 'status': 'error'}), 400

    new_user = User(username=username, email=email, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registration successful!', 'status': 'success'}), 200

# 📌 Logowanie użytkownika
@app.route('/login', methods=['POST'])
def login():
    data = request.form
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        session['username'] = user.username
        return jsonify({'message': 'Login successful!', 'status': 'success'})
    
    return jsonify({'error': 'Invalid username or password.', 'status': 'error'})

# 📌 Przesyłanie pliku XML (teraz pliki zapisujemy lokalnie)
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Brak pliku w zapytaniu'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nie wybrano pliku'}), 400
    
    # 📌 Zapis pliku w katalogu "uploads"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    return jsonify({'message': f'Plik {file.filename} zapisany!', 'status': 'success'}), 200

# 📌 Pobieranie przetworzonego pliku XML
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'Plik nie istnieje'}), 404
    
    return send_file(file_path, as_attachment=True, download_name=filename, mimetype='application/xml')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
