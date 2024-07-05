import psycopg2

def get_db_connection():
    # Zmień te parametry na swoje ustawienia bazy danych
    conn = psycopg2.connect(
        dbname="gen_tree",
        user="admin",
        password="admin",
        host="localhost"
    )
    return conn

def check_and_add_missing_spouse_relations():
    conn = get_db_connection()
    cur = conn.cursor()

    # Pobieranie wszystkich relacji "małżonek"
    cur.execute("""
        SELECT id_osoby, id_osoby_w_relacji 
        FROM relacje 
        WHERE relacja = 'małżonek'
    """)
    relations = cur.fetchall()

    # Przetwarzanie każdej relacji
    for id_osoby, id_osoby_w_relacji in relations:
        # Sprawdzanie, czy istnieje odwrotna relacja
        cur.execute("""
            SELECT COUNT(*) 
            FROM relacje 
            WHERE id_osoby = %s AND id_osoby_w_relacji = %s AND relacja = 'małżonek'
        """, (id_osoby_w_relacji, id_osoby))
        count = cur.fetchone()[0]

        # Jeśli brak odwrotnej relacji, dodaj ją
        if count == 0:
            cur.execute("""
                INSERT INTO relacje (id_osoby, relacja, id_osoby_w_relacji)
                VALUES (%s, 'małżonek', %s)
            """, (id_osoby_w_relacji, id_osoby))
            print(f"Dodano brakującą relację: id_osoby={id_osoby_w_relacji}, małżonek, id_osoby_w_relacji={id_osoby}")

    conn.commit()
    cur.close()
    conn.close()
    print("Wszystkie brakujące relacje zostały dodane.")

if __name__ == "__main__":
    check_and_add_missing_spouse_relations()
