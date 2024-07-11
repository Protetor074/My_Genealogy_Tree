from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
import psycopg2
import base64
from werkzeug.security import generate_password_hash, check_password_hash
import string
import random
from datetime import datetime, timedelta
from functools import wraps
from PIL import Image
import io

app = Flask(__name__)
app.secret_key = 'supersecretkey'


# Konfiguracja połączenia z bazą danych
# ONLINE
def get_db_connection():
    conn = psycopg2.connect(
        dbname='gen_tree',  # Nazwa bazy danych
        user='gen_tree_owner',  # Nazwa użytkownika bazy danych
        password='zXpdLhHUR9F2',  # Hasło do bazy danych
        host='ep-divine-term-a2ib4suo-pooler.eu-central-1.aws.neon.tech',  # Adres hosta
        port='5432',  # Port (domyślny port PostgreSQL)
        sslmode='require'
    )
    return conn

# LOCAL
# def get_db_connection():
#     conn = psycopg2.connect(
#         dbname="gen_tree",
#         user="admin",
#         password="admin",
#         host="localhost"
#     )
#     return conn


# GLOBAL FUNCTION

def generate_access_key(level, expiration_days=None):
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    expiration_date = (datetime.now() + timedelta(days=expiration_days)).date() if expiration_days else None
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO AccessKeys (access_key, level, expiration_date) VALUES (%s, %s, %s)",
                (key, level, expiration_date))
    conn.commit()
    cur.close()
    conn.close()
    return key


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_level') < 10:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function

def moderator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_level') < 5:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def work_progres(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_level') < 10:
            return redirect(url_for('work_sait'))
        return f(*args, **kwargs)

    return decorated_function


def inTest(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_level') < 5:
            return redirect(url_for('work_sait'))
        return f(*args, **kwargs)

    return decorated_function

def login_test(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


def convert_image_to_bytea(image):
    binary_data = image.read()
    return binary_data

def convert_image_to_bytea_from_path(image_path):
    with open(image_path, 'rb') as file:
        binary_data = file.read()
    return binary_data

def convert_to_jpeg(input_path, output_path):
    try:
        # Otwórz obraz wejściowy
        with Image.open(input_path) as img:
            # Jeśli obraz nie jest w formacie RGB, konwertuj go
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Zapisz obraz w formacie JPEG
            img.save(output_path, 'JPEG')

            print(f'Konwersja zakończona pomyślnie: {input_path} -> {output_path}')
            return True

    except IOError as e:
        print(f'Błąd konwersji: {e}')
        return False


##MAIN SAIT
@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('index.html')
    return redirect(url_for('user_page'))


##LOGIN/REGISTER - SAITS

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, password, temp_key FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

        if user:
            if check_password_hash(user[1], password):
                session['user_id'] = user[0]
                temp_key = user[2]

                cur.execute("SELECT level FROM accesskeys WHERE access_key = %s", (temp_key,))
                level = cur.fetchone()
                session['user_level'] = level[0] if level else None

                # Aktualizacja czasu logowania
                cur.execute("UPDATE users SET last_login = %s WHERE id = %s", (current_datetime, user[0]))
                conn.commit()
                cur.close()
                conn.close()

                return jsonify({'success': True, 'redirect': url_for('index')})
            else:
                return jsonify({'success': False, 'message': 'Niepoprawne hasło.'})
        else:
            return jsonify({'success': False, 'message': 'Nie znaleziono użytkownika.'})

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_level', None)
    return redirect(url_for('index'))  # Poprawiono url_for('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        access_key = request.form['access_key']

        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')

        conn = get_db_connection()
        cur = conn.cursor()

        # Sprawdzenie, czy użytkownik o takiej nazwie już istnieje
        cur.execute("SELECT id FROM Users WHERE username = %s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Taki użytkownik już istnieje.'})

        # Sprawdzenie poprawności klucza dostępu
        cur.execute("SELECT id, level, expiration_date, used FROM AccessKeys WHERE access_key = %s", (access_key,))
        key_data = cur.fetchone()

        if key_data:
            key_id, level, expiration_date, used = key_data

            if expiration_date and expiration_date < datetime.now().date():
                cur.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Podany klucz stracił ważność.'})

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            cur.execute("INSERT INTO Users (username, password, temp_key) VALUES (%s, %s, %s) RETURNING id",
                        (username, hashed_password, access_key))
            user_id = cur.fetchone()[0]
            cur.execute("UPDATE AccessKeys SET used = TRUE WHERE id = %s", (key_id,))

            cur.execute("UPDATE Users SET last_login = %s WHERE id = %s", (current_datetime, user_id))

            conn.commit()
            cur.close()
            conn.close()

            session['user_id'] = user_id
            session['user_level'] = level
            return jsonify({'success': True, 'redirect': url_for('index')})
        else:
            cur.close()
            conn.close()
            return jsonify(
                {'success': False, 'message': 'Podano niepoprawny klucz proszę skontaktować się z administratorem.'})

    # Jeżeli metoda nie jest POST, renderuj stronę rejestracji
    return render_template('register.html')


##ADMIN FUNCTION
@app.route('/admin')
@admin_required
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT username, last_login FROM users WHERE last_login IS NOT NULL ORDER BY last_login DESC")
    logged_in_users = cur.fetchall()

    cur.execute("SELECT * FROM accesskeys WHERE level = 1")
    universal_key = cur.fetchall()

    cur.execute("SELECT access_key, level, expiration_date, used, created_by_id FROM accesskeys order by level")
    keys = cur.fetchall()

    cur.execute("SELECT access_key FROM accesskeys")
    available_keys = cur.fetchall()

    cur.execute("""
        SELECT u.username, u.id, u.temp_key, a.level
        FROM users u
        JOIN accesskeys a ON u.temp_key = a.access_key
        WHERE u.temp_key IS NOT NULL order by u.id
    """)
    users_with_temp_keys = cur.fetchall()

    cur.execute("SELECT id, username FROM users")
    users = cur.fetchall()

    cur.close()
    conn.close()

    # Formatowanie last_login dla każdego użytkownika
    formatted_logged_in_users = [
        (username, last_login.strftime('%Y-%m-%d %H:%M')) for username, last_login in logged_in_users
    ]

    return render_template('admin.html',
                           universal_key=universal_key,
                           keys=keys,
                           users_with_temp_keys=users_with_temp_keys,
                           logged_in_users=formatted_logged_in_users,
                           users=users,
                           available_keys=available_keys)


@app.route('/generate_key', methods=['POST'])
@admin_required
def generate_key():
    data = request.get_json()
    level = data['level']
    expiration_date = data.get('expiration_date')
    # Generate the key and save to database
    # ...
    generated_key = "example_key"  # Replace with actual key generation logic
    return jsonify({"key": generated_key})


@app.route('/delete_key', methods=['POST'])
@admin_required
def delete_key():
    key = request.form['key']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM accesskeys WHERE access_key = %s", (key,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": f"Klucz {key} został usunięty."})


@app.route('/reset_password', methods=['POST'])
@admin_required
def reset_password():
    user_id = request.form['user_id']
    new_password = request.form['new_password']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password = %s WHERE id = %s",
                (new_password, user_id))  # Hash the password in a real application
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Hasło zostało zresetowane."})


@app.route('/update_user_key', methods=['POST'])
@admin_required
def update_user_key():
    user_id = request.form['user_id']
    new_key = request.form['new_key']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET temp_key = %s WHERE id = %s", (new_key, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Zmieniono klucz użytkownika."})


@app.route('/moderator')
@moderator_required
def moderator_panel():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, last_login FROM users WHERE last_login IS NOT NULL ORDER BY last_login DESC")
    logged_in_users = cur.fetchall()
    cur.close()
    conn.close()
    formatted_logged_in_users = [
        (username, last_login.strftime('%Y-%m-%d %H:%M')) for username, last_login in logged_in_users
    ]
    return render_template('moderator.html', logged_in_users=formatted_logged_in_users)


@app.route('/work_sait')
@login_test
def work_sait():
    return render_template('work_sait.html')


@app.route('/user_page')
@login_test
def user_page():
    # Pobranie nazwy użytkownika
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM Users WHERE Id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()

    # Pobranie poziomu uprawnień użytkownika
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT a.level FROM Users u JOIN accesskeys a ON a.access_key = u.temp_key WHERE u.Id = %s",
                (session['user_id'],))
    user_permission_level = cur.fetchone()
    cur.close()
    conn.close()
    # user_permission_level = 3

    if user and user_permission_level:
        return render_template('user.html', username=user[0], user_permission_level=user_permission_level)
    else:
        return redirect(url_for('login'))


@app.route('/change_password', methods=['POST'])
@login_test
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')

    if not current_password or not new_password:
        flash('Proszę wypełnić wszystkie pole.', 'danger')
        return jsonify({'success': False, 'message': 'Proszę wypełnić wszystkie pole.'})

    if len(new_password) < 4:
        flash('Hasło nie może być krótsze niż 4 znaki.', 'danger')
        return jsonify({'success': False, 'message': 'Hasło nie może być krótsze niż 4 znaki.'})

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Pobranie hasła użytkownika i sprawdzenie jego poprawności
        cur.execute("SELECT password FROM users WHERE Id = %s", (session['user_id'],))
        user = cur.fetchone()

        if user and check_password_hash(user[0], current_password):
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')

            # Użycie transakcji SQL do wykonania aktualizacji
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE users SET password = %s WHERE Id = %s",
                                   (hashed_password, session['user_id']))

            flash('Hasło zmienione poprawnie!', 'success')
            return jsonify({'success': True, 'message': 'Hasło zmienione poprawnie!!'})
        else:
            flash('Niepoprawne aktualne hasło', 'danger')
            return jsonify({'success': False, 'message': 'Niepoprawne aktualne hasło.'})

    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'})

    finally:
        cur.close()
        conn.close()


@app.route('/search', methods=['GET', 'POST'])
@login_test
def search():
    if request.method == 'POST':
        query = request.form.get('name', '')
    else:
        query = request.args.get('query', '')

    if ' ' in query:
        name_parts = query.split(' ')
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
    else:
        first_name = query
        last_name = ''

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, imię, nazwisko, EXTRACT(YEAR FROM data_urodzenia) AS rok_urodzenia
        FROM osoba
        WHERE (imię ILIKE %s AND nazwisko ILIKE %s)
        OR (imię ILIKE %s OR nazwisko ILIKE %s)
        LIMIT 5;
    """, (f'{first_name}%', f'{last_name}%', f'{query}%', f'{query}%'))
    results = cur.fetchall()
    cur.close()
    conn.close()

    if request.method == 'POST':
        return render_template('index.html', results=results)
    return jsonify({'results': results})


# Wyświetlanie szczegółów osoby
@app.route('/person/<int:person_id>', methods=['GET', 'POST'])
@login_test
def person(person_id):
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')

    user_id = session['user_id']  # Pobieranie user_id z sesji

    conn = get_db_connection()
    cur = conn.cursor()

    # Pobieranie informacji o osobie
    cur.execute("""
        SELECT Id, Imię, Nazwisko, Płeć, EXTRACT(YEAR FROM data_urodzenia) AS rok_urodzenia, EXTRACT(YEAR FROM data_śmierci) AS rok_śmierci, EXTRACT(YEAR FROM data_ślubu), zdjęcie
        FROM Osoba
        WHERE Id = %s
    """, (person_id,))
    person = cur.fetchone()

    if person == None:
        return redirect(url_for('user_page'))

    # Pobieranie informacji o uprawnieniach do modyfikacji
    cur.execute("""
         SELECT u.id, u.username
            FROM users u
            WHERE u.id = (
            SELECT o.modified_by
                FROM osoba o
                WHERE o.id = %s)
        """, (person_id,))
    owner = cur.fetchone()

    user_id = session.get('user_id')

    # Pobieranie małżonka
    cur.execute("""
        SELECT o.Id, o.Imię, o.Nazwisko, o.Płeć, EXTRACT(YEAR FROM o.data_urodzenia) AS rok_urodzenia, EXTRACT(YEAR FROM o.data_śmierci) AS rok_śmierci, o.zdjęcie
        FROM Osoba o
        JOIN Relacje r ON o.Id = r.Id_Osoby_w_Relacji
        WHERE r.Id_Osoby = %s AND r.Relacja = 'małżonek'
    """, (person_id,))
    spouses = cur.fetchall()

    childrens = {}

    # Pobieranie dzieci
    cur.execute("""
        SELECT o.Id, o.Imię, o.Nazwisko, o.Płeć, EXTRACT(YEAR FROM o.data_urodzenia) AS rok_urodzenia, EXTRACT(YEAR FROM o.data_śmierci) AS rok_śmierci, o.zdjęcie
        FROM Osoba o
        JOIN Relacje r ON o.Id = r.Id_Osoby
        WHERE r.Id_Osoby_w_Relacji = %s AND r.Relacja = 'rodzic'
    ORDER BY rok_urodzenia
    """, (person_id,))
    children = cur.fetchall()

    # Pobieranie dzieci dla poszczególnych matek
    for spouse in spouses:
        spouse_id = spouse[0]  # Zakładając, że ID małżonka jest na pierwszej pozycji
        cur.execute("""
            SELECT o.Id, o.Imię, o.Nazwisko, o.Płeć, EXTRACT(YEAR FROM o.data_urodzenia) AS rok_urodzenia, EXTRACT(YEAR FROM o.data_śmierci) AS rok_śmierci, o.zdjęcie
            FROM Osoba o
            JOIN Relacje r ON o.Id = r.Id_Osoby
            WHERE r.Id_Osoby_w_Relacji = %s AND r.Relacja = 'rodzic'
            ORDER BY rok_urodzenia
        """, (spouse_id,))
        children_0 = cur.fetchall()
        childrens[spouse_id] = children_0

    # Pobieranie rodziców
    cur.execute("""
        SELECT o.Id, o.Imię, o.Nazwisko, o.Płeć, o.zdjęcie
        FROM Osoba o
        JOIN Relacje r ON o.Id = r.Id_Osoby_w_Relacji
        WHERE r.Id_Osoby = %s AND r.Relacja = 'rodzic';
    """, (person_id,))
    parents = cur.fetchall()

    # Pobieranie ojca
    cur.execute("""
        SELECT o.Id, o.Imię, o.Nazwisko, EXTRACT(YEAR FROM o.data_urodzenia) AS rok_urodzenia, EXTRACT(YEAR FROM o.data_śmierci) AS rok_śmierci, o.zdjęcie
        FROM Osoba o
        JOIN Relacje r ON o.Id = r.Id_Osoby_w_Relacji
        WHERE r.Id_Osoby = %s AND r.Relacja = 'rodzic' AND o.Płeć = 'M'
    """, (person_id,))
    father = cur.fetchone()

    # Pobieranie matki
    cur.execute("""
        SELECT o.Id, o.Imię, o.Nazwisko, EXTRACT(YEAR FROM o.data_urodzenia) AS rok_urodzenia, EXTRACT(YEAR FROM o.data_śmierci) AS rok_śmierci, o.zdjęcie
        FROM Osoba o
        JOIN Relacje r ON o.Id = r.Id_Osoby_w_Relacji
        WHERE r.Id_Osoby = %s AND r.Relacja = 'rodzic' AND o.Płeć = 'F'
    """, (person_id,))
    mother = cur.fetchone()

    # Pobieranie rodzeństwa całego
    cur.execute("""
        SELECT DISTINCT sib.Id, sib.Imię, sib.Nazwisko, sib.Płeć, EXTRACT(YEAR FROM sib.data_urodzenia) AS rok_urodzenia, EXTRACT(YEAR FROM sib.data_śmierci) AS rok_śmierci, sib.zdjęcie
        FROM osoba sib
        JOIN relacje p ON sib.id = p.id_osoby
        WHERE p.id_osoby_w_relacji IN (
            SELECT Id_Osoby_w_Relacji
            FROM Relacje
            WHERE Id_Osoby = %s AND Relacja = 'rodzic')
            AND relacja = 'rodzic' AND Id_Osoby != %s
            order by rok_urodzenia
        """, (person_id, person_id))
    siblings = cur.fetchall()

    # Pobieranie rodzeństwa dla obydwu rodziców
    cur.execute("""
               SELECT DISTINCT sib.Id, sib.Imię, sib.Nazwisko, sib.Płeć, EXTRACT(YEAR FROM sib.data_urodzenia) AS rok_urodzenia, EXTRACT(YEAR FROM sib.data_śmierci) AS rok_śmierci, sib.zdjęcie
            FROM osoba sib
            JOIN relacje p1 ON sib.id = p1.id_osoby
            JOIN relacje p2 ON sib.id = p2.id_osoby
            WHERE p1.id_osoby_w_relacji IN (
                    SELECT r1.id_osoby_w_relacji
                    FROM relacje r1
                    WHERE r1.Id_Osoby = %s AND r1.Relacja = 'rodzic'
                )
              AND p2.id_osoby_w_relacji IN (
                    SELECT r2.id_osoby_w_relacji
                    FROM relacje r2
                    WHERE r2.Id_Osoby = %s AND r2.Relacja = 'rodzic'
                )
              AND p1.id_osoby_w_relacji != p2.id_osoby_w_relacji
              AND sib.Id != %s
              AND p1.Relacja = 'rodzic'
              AND p2.Relacja = 'rodzic'
            ORDER BY rok_urodzenia;
                """, (person_id, person_id, person_id))
    siblings2 = cur.fetchall()

    siblings = [list(sibling) for sibling in siblings]
    for sibling in siblings:
        sibling[6] = base64.b64encode(sibling[6]).decode('utf-8')

    siblings2 = [list(sibling2) for sibling2 in siblings2]
    for sibling2 in siblings2:
        sibling2[6] = base64.b64encode(sibling2[6]).decode('utf-8')

    half = len(siblings2) // 2
    siblings_first_half = siblings2[:half]
    siblings_second_half = siblings2[half:]

    # Aktualizacja czasu logowania
    cur.execute("UPDATE users SET last_login = %s WHERE id = %s", (current_datetime, user_id))
    conn.commit()

    cur.close()
    conn.close()

    def convert_image(image_data):
        if image_data:
            return base64.b64encode(image_data).decode('utf-8')
        return None

    person = list(person)
    if person[7]:  # Zakładając, że Zdjęcie jest na 9 pozycji
        person[7] = convert_image(person[7])

    spouses = [list(spouse) for spouse in spouses]
    for spouse in spouses:
        if spouse[6]:  # Zakładając, że Zdjęcie jest na 4 pozycji
            spouse[6] = convert_image(spouse[6])

    if father != None:
        father = list(father)
        if father[5]:  # Zakładając, że Zdjęcie jest na 5 pozycji
            father[5] = convert_image(father[5])

    if mother != None:
        mother = list(mother)
        if mother[5]:  # Zakładając, że Zdjęcie jest na 5 pozycji
            mother[5] = convert_image(mother[5])

    children = [list(child) for child in children]
    for child in children:
        if child[6]:  # Zakładając, że Zdjęcie jest na 4 pozycji
            child[6] = convert_image(child[6])

    for spouse_id, children_0 in childrens.items():
        childrens[spouse_id] = [list(child_0) for child_0 in children_0]
        for child_0 in childrens[spouse_id]:
            if child_0[6]:  # Zakładając, że Zdjęcie jest na 6 pozycji
                child_0[6] = convert_image(child_0[6])

    return render_template('person.html', person=person, spouses=spouses, children=children, childrens=childrens,
                           parents=parents, siblings=siblings, father=father, mother=mother,
                           siblings_first_half=siblings_first_half, siblings_second_half=siblings_second_half,
                           owner=owner, user_id=user_id)


@app.route('/modify_person_data/<int:person_id>', methods=['GET', 'POST'])
@inTest
def modify_person_data(person_id):
    if request.method == 'POST':
        imie = request.form['imie']
        nazwisko = request.form['nazwisko']
        plec = request.form['plec']
        data_urodzenia = request.form['data_urodzenia']
        data_slubu = request.form.get('data_slubu')
        data_smierci = request.form.get('data_smierci')
        zdjecie = request.files.get('zdjecie')
        image_data = None
        temp_image_path = None

        if plec == "Mężczyzna":
            plec = 'M'
        else:
            plec = 'F'

        if data_slubu == "":
            data_slubu = None
        if data_smierci == "":
            data_smierci = None

        if zdjecie and zdjecie.filename != '':
            try:
                # Sprawdzenie czy plik jest plikiem graficznym
                image = Image.open(zdjecie)
                image.verify()  # Verify if it is an image
                zdjecie.seek(0)  # Reset the file pointer to the start
                image_data = convert_image_to_bytea(zdjecie)
            except (IOError, SyntaxError) as e:
                return jsonify({'error': 'Plik nie jest prawidłowym obrazem'}), 400

        user_id = session.get('user_id')

        conn = get_db_connection()
        cur = conn.cursor()
        if image_data is not None:
            cur.execute(
                "UPDATE osoba SET imię = %s, nazwisko = %s, płeć = %s, "
                "data_urodzenia = %s, data_ślubu = %s, data_śmierci = %s, "
                "zdjęcie = %s, modified_by = %s "
                "WHERE Id = %s",
                (imie, nazwisko, plec, data_urodzenia, data_slubu, data_smierci, image_data, user_id, person_id)
            )
        else:
            cur.execute(
                "UPDATE osoba SET imię = %s, nazwisko = %s, płeć = %s, "
                "data_urodzenia = %s, data_ślubu = %s, data_śmierci = %s, "
                "modified_by = %s WHERE Id = %s",
                (imie, nazwisko, plec, data_urodzenia, data_slubu, data_smierci, user_id, person_id)
            )

        conn.commit()
        cur.close()
        conn.close()

        flash('Osoba została zmodyfikowana pomyślnie!')
        return redirect(url_for('person', person_id=person_id))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Osoba WHERE Id = %s", (person_id,))
    person = cur.fetchone()
    cur.close()
    conn.close()

    if person is None:
        return "Person not found", 404

    person_dict = {
        'id': person[0],
        'imie': person[1],
        'nazwisko': person[2],
        'plec': person[3],
        'data_urodzenia': person[4],
        'data_smierci': person[5],
        'data_slubu': person[6],
        'image_url': person[7]
    }
    return render_template('modify_person_data.html', person=person_dict)


# Endpoint dla dodawania i usuwania zdjęcia

@app.route('/add_photo/<int:person_id>/<int:user_id>/<int:person_modification_owner>', methods=['POST'])
@inTest
def add_photo(person_id, user_id, person_modification_owner):
    if 'zdjecie' not in request.files:
        flash('Brak pliku', 'error')
        return redirect(url_for('person', person_id=person_id))

    zdjecie = request.files['zdjecie']

    if zdjecie.filename == '':
        flash('Nie wybrano pliku', 'error')
        return redirect(url_for('person', person_id=person_id))

    try:
        # Sprawdzenie czy plik jest plikiem graficznym
        image = Image.open(io.BytesIO(zdjecie.read()))
        image.verify()  # Verify if it is an image
        zdjecie.seek(0)  # Reset the file pointer to the start
    except (IOError, SyntaxError) as e:
        flash('Plik nie jest prawidłowym obrazem', 'error')
        return redirect(url_for('person', person_id=person_id))

    if zdjecie.filename != '':
        image_data = convert_image_to_bytea(zdjecie)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE osoba SET zdjęcie = %s WHERE Id = %s", (image_data, person_id))
        conn.commit()
        cur.close()
        conn.close()

        flash('Zdjęcie zostało dodane', 'success')
        return redirect(url_for('person', person_id=person_id))
    else:
        flash('Niedozwolony format pliku', 'error')
        return redirect(url_for('person', person_id=person_id))

@app.route('/remove_photo/<int:person_id>', methods=['POST'])
@inTest
def remove_photo(person_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT płeć FROM osoba WHERE Id = %s", (person_id,))
    plec = cur.fetchone()
    cur.close()
    conn.close()

    image_data = None
    if plec and plec[0] == 'M':
        image_data = convert_image_to_bytea_from_path('Import_Image/me2.jpg')
    elif plec and plec[0] == 'F':
        image_data = convert_image_to_bytea_from_path('Import_Image/fe2.jpg')
    else:
        flash('Nieprawidłowa płeć', 'error')
        return redirect(url_for('person', person_id=person_id))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE osoba SET zdjęcie = %s WHERE Id = %s", (image_data, person_id))
    conn.commit()
    cur.close()
    conn.close()

    flash('Zdjęcie zostało usunięte', 'success')
    return redirect(url_for('person', person_id=person_id))


@app.route('/add_parent/<int:person_id>', methods=['GET', 'POST'])
@inTest
def add_parent(person_id):
    if request.method == 'POST':
        # Ojciec
        imie_ojca = request.form.get('imie_ojca')
        nazwisko_ojca = request.form.get('nazwisko_ojca')
        data_urodzenia_ojca = request.form.get('data_urodzenia_ojca')
        data_slubu_ojca = request.form.get('data_slubu_ojca')
        data_smierci_ojca = request.form.get('data_smierci_ojca')
        zdjecie_ojca = request.files.get('zdjecie_ojca')

        # Matka
        imie_matki = request.form.get('imie_matki')
        nazwisko_matki = request.form.get('nazwisko_matki')
        data_urodzenia_matki = request.form.get('data_urodzenia_matki')
        data_slubu_matki = request.form.get('data_slubu_matki')
        data_smierci_matki = request.form.get('data_smierci_matki')
        zdjecie_matki = request.files.get('zdjecie_matki')

        user_id = session.get('user_id')

        conn = get_db_connection()
        cur = conn.cursor()

        def add_parent_to_db(imie, nazwisko, data_urodzenia, data_slubu, data_smierci, zdjecie, plec, person_id):
            image_data = None
            father_id = None
            mother_id = None
            if zdjecie and zdjecie.filename != '':
                image_data = convert_image_to_bytea(zdjecie)
            else:
                if plec == 'M':
                    image_data = convert_image_to_bytea_from_path('Import_Image/me2.jpg')
                else:
                    image_data = convert_image_to_bytea_from_path('Import_Image/fe2.jpg')

            if not data_slubu:
                data_slubu = None
            if not data_smierci:
                data_smierci = None
            if not data_urodzenia:
                data_urodzenia = None

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO osoba (imię, nazwisko, płeć, data_urodzenia, data_ślubu, data_śmierci, zdjęcie, modified_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (imie, nazwisko, plec, data_urodzenia, data_slubu, data_smierci, image_data, user_id)
            )
            new_parent_id = cur.fetchone()[0]
            cur.execute("CALL dodaj_relacje_rodzic_dziecko(%s, %s)", (person_id, new_parent_id))
            conn.commit()
            cur.close()
            conn.close()

            return new_parent_id

        # Dodaj ojca
        if imie_ojca and nazwisko_ojca:
            father_id = add_parent_to_db(imie_ojca, nazwisko_ojca, data_urodzenia_ojca, data_slubu_ojca,
                                         data_smierci_ojca,
                                         zdjecie_ojca, 'M', person_id)

        # Dodaj matkę
        if imie_matki and nazwisko_matki:
            mother_id = add_parent_to_db(imie_matki, nazwisko_matki, data_urodzenia_matki, data_slubu_matki,
                                         data_smierci_matki,
                                         zdjecie_matki, 'F', person_id)

        cur.execute("CALL call dodaj_relacje_malzenska()(%s, %s)", (father_id, mother_id))

        conn.commit()
        cur.close()
        conn.close()

        flash('Rodzice zostali dodani pomyślnie!')
        return redirect(url_for('person', person_id=person_id))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Osoba WHERE Id = %s", (person_id,))
    person = cur.fetchone()

    cur.execute("SELECT COUNT(*) FROM relacje WHERE id_osoby = %s AND relacja = 'rodzic'; ", (person_id,))
    parents = cur.fetchone()
    cur.close()
    conn.close()

    if parents !=0:
        flash('Osoba posiada już rodziców', 'error')
        return redirect(url_for('person', person_id=person_id))

    if person is None:
        return "Person not found", 404

    person_dict = {
        'id': person[0],
        'imie': person[1],
        'nazwisko': person[2],
        'plec': person[3],
        'data_urodzenia': person[4],
        'data_smierci': person[5],
        'data_slubu': person[6],
        'image_url': person[7]
    }
    return render_template('add_parent.html', person=person_dict)


@app.route('/add_child/<int:parent_id>', methods=['GET', 'POST'])
@inTest
def add_child(parent_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Pobierz informacje o rodzicu
    cur.execute("SELECT imię, nazwisko FROM osoba WHERE id = %s", (parent_id,))
    parent = cur.fetchone()

    if not parent:
        cur.close()
        conn.close()
        flash('Nie znleziono rodzica', 'error')
        return redirect(url_for('person', person_id=parent_id))

    # Pobierz małżonków
    cur.execute("""
         SELECT o.id, o.imię, o.nazwisko
        FROM osoba o
        JOIN relacje r ON r.id_osoby = o.id
        WHERE r.id_osoby_w_relacji = %s AND r.relacja = 'małżonek'
    """, (parent_id,))
    spouses = cur.fetchall()

    if (spouses.__len__() == 0):
        flash('Osoba nie posiada partnera. Najpierw dodaj partnera lub wprowadź dane fikcyjne.', 'error')
        return redirect(url_for('person', person_id=parent_id))


    if request.method == 'POST':
        imie = request.form['imie']
        nazwisko = request.form['nazwisko']
        plec = request.form['plec']
        data_urodzenia = request.form['data_urodzenia']
        data_slubu = request.form.get('data_slubu')
        data_smierci = request.form.get('data_smierci')
        zdjecie = request.files['zdjecie']
        second_parent_id = request.form.get('second_parent_id')

        if not second_parent_id:
            flash('Musisz wybrać drugiego rodzica!')
            return redirect(url_for('add_child', parent_id=parent_id))

        if plec == "Mężczyzna":
            plec = 'M'
        else:
            plec = 'F'

        if data_slubu == "":
            data_slubu = None
        if data_smierci == "":
            data_smierci = None

        image_data = None
        if zdjecie and zdjecie.filename != '':
            image_data = convert_image_to_bytea(zdjecie)
        else:
            if plec == 'M':
                image_data = convert_image_to_bytea_from_path('Import_Image/me2.jpg')
            else:
                image_data = convert_image_to_bytea_from_path('Import_Image/fe2.jpg')

        user_id = session.get('user_id')
        cur.execute(
            """
            INSERT INTO osoba (imię, nazwisko, płeć, data_urodzenia, data_ślubu, data_śmierci, zdjęcie, modified_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (imie, nazwisko, plec, data_urodzenia, data_slubu, data_smierci, image_data, user_id)
        )
        new_person_id = cur.fetchone()[0]

        # Dodaj relacje dziecko-rodzic
        cur.execute("CALL dodaj_relacje_rodzic_dziecko(%s, %s)", (new_person_id, parent_id))
        cur.execute("CALL dodaj_relacje_rodzic_dziecko(%s, %s)", (new_person_id, second_parent_id))

        conn.commit()
        cur.close()
        conn.close()

        flash('Dziecko zostało dodane pomyślnie!')
        return redirect(url_for('person', person_id=parent_id))

    person_dict = {
        'id': parent_id,
        'imie': parent[0],
        'nazwisko': parent[1]
    }

    cur.close()
    conn.close()

    return render_template('add_child.html', person=person_dict, spouses=spouses)


@app.route('/add_spouse/<int:person_id>', methods=['GET', 'POST'])
@inTest
def add_spouse(person_id):
    if request.method == 'POST':
        imie = request.form['imie']
        nazwisko = request.form['nazwisko']
        plec = request.form['plec']
        data_urodzenia = request.form['data_urodzenia']
        data_slubu = request.form.get('data_slubu')
        data_smierci = request.form.get('data_smierci')
        zdjecie = request.files['zdjecie']
        image_data = None
        temp_image_path = None

        if plec == "Mężczyzna":
            plec = 'M'
        else:
            plec = 'F'

        if data_urodzenia == "":
            data_urodzenia = None
        if data_slubu == "":
            data_slubu = None
        if data_smierci == "":
            data_smierci = None

        if zdjecie.filename != '':
            image_data = convert_image_to_bytea(zdjecie)
        else:
            if plec == 'M':
                image_data = convert_image_to_bytea_from_path('Import_Image/me2.jpg')
            else:
                image_data = convert_image_to_bytea_from_path('Import_Image/fe2.jpg')

        user_id = session.get('user_id')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO osoba (imię, nazwisko, płeć, data_urodzenia, data_ślubu, data_śmierci, zdjęcie, modified_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (imie, nazwisko, plec, data_urodzenia, data_slubu, data_smierci, image_data, user_id)
        )
        new_person_id = cur.fetchone()[0]
        cur.execute("CALL dodaj_relacje_malzenska(%s, %s)", (new_person_id, person_id))
        conn.commit()
        cur.close()
        conn.close()

        flash('Osoba została dodana pomyślnie!')
        return redirect(url_for('person', person_id=person_id))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Osoba WHERE Id = %s", (person_id,))
    person = cur.fetchone()
    cur.close()
    conn.close()

    if person is None:
        return "Person not found", 404

    person_dict = {
        'id': person[0],
        'imie': person[1],
        'nazwisko': person[2],
        'plec': person[3],
        'data_urodzenia': person[4],
        'data_smierci': person[5],
        'data_slubu': person[6],
        'image_url': person[7]
    }
    return render_template('add_spouse.html', person=person_dict)


@app.route('/remove_person/<int:person_id>', methods=['POST'])
@inTest
def remove_person(person_id):
    user_id = session['user_id']
    # Pobranie hasła z bazy danych
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
       SELECT modified_by FROM osoba where id = %s
        """,
        (person_id,)
    )
    owner_id = cur.fetchone()[0]
    cur.close()
    conn.close()

    if owner_id != person_id:
        if session['user_level'] < 6:
            flash('Nie masz uprawnień do zarządzania tą osobą(Nie jesteś jej twórcą)','error')
            return redirect(url_for('/person/',person_id = person_id))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM relacje
        WHERE id_osoby = %s OR id_osoby_w_relacji = %s;
        """,
        (person_id, person_id)
    )

    cur.execute(
        """
        DELETE FROM osoba
        WHERE id = %s;
        """,
        (person_id,)
    )
    conn.commit()
    cur.close()
    conn.close()

    flash('Nie masz uprawnień do zarządzania tą osobą(Nie jesteś jej twórcą)','messages')
    return redirect(url_for('user_page'))


if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'images'
    app.run("192.168.1.108", debug=True)
