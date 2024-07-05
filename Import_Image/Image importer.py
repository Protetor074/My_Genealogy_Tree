import psycopg2
import base64


# Funkcja konwertująca plik obrazu na dane w formacie BYTEA
def convert_image_to_bytea(image_path):
    with open(image_path, 'rb') as file:
        binary_data = file.read()
    return binary_data


# Ścieżki do plików ze zdjęciami startowymi
male_image_path = 'me2.jpg'
female_image_path = 'fe2.jpg'

# Konwersja zdjęć na format BYTEA
male_image_data = convert_image_to_bytea(male_image_path)
female_image_data = convert_image_to_bytea(female_image_path)

# Konfiguracja połączenia z bazą danych

conn = psycopg2.connect(
    dbname="gen_tree",
    user="admin",
    password="admin",
    host="localhost"
)

cur = conn.cursor()

# Aktualizacja zdjęć dla mężczyzn
cur.execute("""
    UPDATE Osoba
    SET Zdjęcie = %s
    WHERE Płeć = 'M' 
""", (psycopg2.Binary(male_image_data),))

# Aktualizacja zdjęć dla kobiet
cur.execute("""
    UPDATE Osoba
    SET Zdjęcie = %s
    WHERE Płeć = 'F' 
""", (psycopg2.Binary(female_image_data),))

conn.commit()
cur.close()
conn.close()

print("Zdjęcia startowe zostały pomyślnie przypisane.")
