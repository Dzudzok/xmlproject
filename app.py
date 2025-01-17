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
            return jsonify({'error': 'Nieprawidłowy plik XML.'}), 400

        tree = ET.parse(uploaded_file)
        root = tree.getroot()

        tags = set()
        tags.add(root.tag)  # Dodajemy główny tag (np. SHOP)

        for element in root.iter():
            tags.add(element.tag)

        return jsonify(sorted(tags))  # Wysyłamy wszystkie tagi z XML
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

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'Plik nie istnieje'}), 404
    
    return send_file(file_path, as_attachment=True, download_name=filename, mimetype='application/xml')

@app.route('/check-login', methods=['GET'])
def check_login():
    if 'username' in session:
        return jsonify({'logged_in': True, 'username': session['username']})
    return jsonify({'logged_in': False})

# 📌 Pobieranie mapowania pól dla szablonu
user_mappings = {}  # Słownik do przechowywania mapowań użytkownika

@app.route('/set-mapping', methods=['POST'])
def set_mapping():
    global user_mappings
    data = request.json
    template = data.get("template")
    mapping = data.get("mapping")

    if not template or not mapping:
        return jsonify({'error': 'Brak szablonu lub mapowania.'}), 400

    user_mappings[template] = mapping  # Zapisanie mapowania

    return jsonify({'message': 'Mapowanie zapisane poprawnie!'}), 200

@app.route('/get-mapping', methods=['POST'])
def get_mapping():
    template = request.form.get("template")

    if not template or template not in templates:
        return jsonify({'error': 'Nieznany szablon.'}), 400

    return jsonify(templates[template])  # Zwraca dostępne pola szablonu


# 📌 Przetwarzanie pliku XML
@app.route('/process', methods=['POST'])
def process_file():
    try:
        uploaded_file = request.files.get('xml-file')
        template = request.form.get("template")

        if not uploaded_file or not uploaded_file.filename.endswith('.xml'):
            return jsonify({'error': 'Nieprawidłowy plik XML.'}), 400

        tree = ET.parse(uploaded_file)
        root = tree.getroot()

        # Pobranie tagów wybranych przez użytkownika
        output_shop_tag = request.form.get("shop_tag", root.tag).strip()
        output_shopitem_tag = request.form.get("shopitem_tag", root[0].tag if len(root) > 0 else "SHOPITEM").strip()

        output_root = ET.Element(output_shop_tag)

        # Pobranie mapowań dla pozostałych pól
        field_mapping = {}
        for key in request.form:
            if key.startswith("mapping_"):
                original_tag = key.replace("mapping_", "")
                mapped_tag = request.form[key]
                field_mapping[original_tag] = mapped_tag

        # Znalezienie elementów produktów
        found_items = root.findall(f".//{output_shopitem_tag}")

        if not found_items:
            return jsonify({'error': f'Nie znaleziono produktów w tagu <{output_shopitem_tag}>.'}), 400

        # Tworzenie nowego XML
        for item in found_items:
            shopitem = ET.SubElement(output_root, output_shopitem_tag)

            for child in item:
                mapped_tag = field_mapping.get(child.tag, child.tag)
                ET.SubElement(shopitem, mapped_tag).text = child.text if child.text else ""

        # Generowanie pliku XML
        output = BytesIO()
        output_tree = ET.ElementTree(output_root)
        output_tree.write(output, encoding='utf-8', xml_declaration=True)
        output.seek(0)

        print("✅ Plik XML został wygenerowany i jest gotowy do pobrania.")

        return send_file(output, as_attachment=True, download_name='processed.xml', mimetype='application/xml')

    except Exception as e:
        print(f"❌ Błąd w /process: {e}")
        return jsonify({'error': str(e)}), 500






if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5010))  # Domyślnie 5010, ale na serwerze Render automatycznie ustawi 8080
    app.run(host='0.0.0.0', port=port, debug=True)
