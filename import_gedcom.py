import psycopg2
from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser


# Konfiguracja połączenia z bazą danych
def get_db_connection():
    conn = psycopg2.connect(
        dbname="gen_tree",
        user="admin",
        password="admin",
        host="localhost"
    )
    return conn


# Funkcja do formatowania daty
def format_date(date_str):
    if date_str is None or date_str.strip() == '':
        return None
    if len(date_str) == 4:  # Tylko rok
        return f"{date_str}-01-01"
    return date_str


# Funkcja do wstawiania osoby do bazy danych
def insert_person(cursor, individual):
    first_name, last_name = individual.get_name()
    gender = individual.get_gender()

    # Pobieranie daty i miejsca urodzenia
    birth_date = birth_place = None
    birth_data = individual.get_birth_data()
    if birth_data:
        birth_date = format_date(birth_data[0])
        birth_place = birth_data[1]

    # Pobieranie daty i miejsca śmierci
    death_date = death_place = None
    death_data = individual.get_death_data()
    if death_data:
        death_date = format_date(death_data[0])
        death_place = death_data[1]

    cursor.execute("""
        INSERT INTO Osoba (Imię, Nazwisko, Płeć, Miejsce_urodzenia, Data_urodzenia, Miejsce_śmierci, Data_śmierci)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING Id
    """, (first_name, last_name, gender, birth_place, birth_date, death_place, death_date))

    return cursor.fetchone()[0]


# Funkcja do wstawiania relacji do bazy danych
def insert_relation(cursor, person_id, related_person_id, relation_type):
    cursor.execute("""
        INSERT INTO Relacje (Id_Osoby, Relacja, Id_Osoby_w_Relacji)
        VALUES (%s, %s, %s)
    """, (person_id, relation_type, related_person_id))


# Ścieżka do pliku GEDCOM
gedcom_file = 'ged0.ged'

# Inicjalizacja parsera GEDCOM
gedcom_parser = Parser()
gedcom_parser.parse_file(gedcom_file)

# Pobieranie wszystkich osób z pliku GEDCOM
individuals = gedcom_parser.get_element_list()

# Połączenie z bazą danych
conn = get_db_connection()
cur = conn.cursor()

# Przetwarzanie każdej osoby
person_map = {}
for element in individuals:
    if isinstance(element, IndividualElement):
        person_id = insert_person(cur, element)
        person_map[element.get_pointer()] = person_id
        print(person_id)

# Przetwarzanie relacji (dzieci, rodzice, małżonkowie)
for element in individuals:
    if isinstance(element, IndividualElement):
        person_id = person_map[element.get_pointer()]

        # Dodanie relacji rodziców
        parents = gedcom_parser.get_parents(element)
        for parent in parents:
            if parent.get_pointer() in person_map:
                parent_id = person_map[parent.get_pointer()]
                insert_relation(cur, person_id, parent_id, 'rodzic')

        # Dodanie relacji małżonka
        families = gedcom_parser.get_families(element, "FAMS")
        for family in families:
            family_members = gedcom_parser.get_family_members(family)
            for member in family_members:
                if member.get_pointer() in person_map and not member.is_child() and member != element:
                    spouse_id = person_map[member.get_pointer()]
                    # Sprawdź, czy relacja małżeńska jest dwukierunkowa
                    cur.execute("""
                        SELECT 1 FROM Relacje
                        WHERE Id_Osoby = %s AND Relacja = 'małżonek' AND Id_Osoby_w_Relacji = %s
                        UNION ALL
                        SELECT 1 FROM Relacje
                        WHERE Id_Osoby = %s AND Relacja = 'małżonek' AND Id_Osoby_w_Relacji = %s
                    """, (person_id, spouse_id, spouse_id, person_id))
                    if cur.rowcount == 0:
                        insert_relation(cur, person_id, spouse_id, 'małżonek')

# Zatwierdzenie zmian i zamknięcie połączenia
conn.commit()
cur.close()
conn.close()
