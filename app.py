from flask import Flask, request, send_file, jsonify, render_template, session, redirect
import os
import xml.etree.ElementTree as ET
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 📌 Folder do przechowywania plików
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 📌 Konfiguracja bazy danych SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 📌 Model użytkownika
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

# 📌 Tworzenie bazy danych
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

# 📌 Wylogowanie użytkownika
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logout successful!', 'status': 'success'}), 200

# 📌 Pobieranie tagów XML
@app.route('/get-tags', methods=['POST'])
def get_tags():
    try:
        uploaded_file = request.files.get('xml-file')
        if not uploaded_file or not uploaded_file.filename.endswith('.xml'):
            return jsonify({'error': 'Nieprawidłowy plik. Prześlij poprawny XML.'}), 400

        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        tags = {element.tag for element in root.iter()}

        return jsonify(sorted(tags))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 📌 Szablony XML
templates = {
    'heureka': {
        'id': 'ITEM_ID',
        'title': 'PRODUCTNAME',
        'description': 'DESCRIPTION',
        'link': 'URL',
        'image_link': 'IMGURL',
        'price': 'PRICE_VAT',
        'brand': 'MANUFACTURER',
        'gtin': 'EAN'
    },
    'allegro': {
        'id': 'OFFER_ID',
        'title': 'NAME',
        'description': 'DESC',
        'link': 'LINK',
        'image_link': 'IMAGE',
        'price': 'COST',
        'brand': 'BRAND',
        'gtin': 'BARCODE'
    },
    'amazon': {
        'id': 'ASIN',
        'title': 'TITLE',
        'description': 'DESCRIPTION_LONG',
        'link': 'PRODUCT_URL',
        'image_link': 'IMAGE_URL',
        'price': 'PRICE_AMOUNT',
        'brand': 'MANUFACTURER_NAME',
        'gtin': 'UPC'
    }
}

# 📌 Pobieranie mapowania pól dla szablonu
@app.route('/get-mapping', methods=['POST'])
def get_mapping():
    template = request.form.get('template')
    if template not in templates:
        return jsonify({'error': 'Nieznany szablon.'}), 400
    return jsonify(templates[template])

# 📌 Przetwarzanie pliku XML
@app.route('/process', methods=['POST'])
def process_file():
    try:
        uploaded_file = request.files.get('xml-file')
        template = request.form.get('template')

        if not uploaded_file or not uploaded_file.filename.endswith('.xml'):
            return jsonify({'error': 'Nieprawidłowy plik. Prześlij poprawny XML.'}), 400

        if template not in templates:
            return jsonify({'error': 'Nieznany szablon.'}), 400

        mappings = request.form.to_dict(flat=True)

        input_tree = ET.parse(uploaded_file)
        input_root = input_tree.getroot()
        output_root = ET.Element('SHOP')

        for item in input_root.findall('.//item'):
            shopitem = ET.SubElement(output_root, 'SHOPITEM')

            for source_field, target_field in mappings.items():
                source_element = item.find(source_field)
                if source_element is not None and source_element.text:
                    ET.SubElement(shopitem, target_field).text = source_element.text

        output = BytesIO()
        output_tree = ET.ElementTree(output_root)
        output_tree.write(output, encoding='utf-8', xml_declaration=True)
        output.seek(0)

        return send_file(output, as_attachment=True, download_name='processed.xml', mimetype='application/xml')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5010))  # Domyślnie 5010, ale na serwerze Render automatycznie ustawi 8080
    app.run(host='0.0.0.0', port=port)
