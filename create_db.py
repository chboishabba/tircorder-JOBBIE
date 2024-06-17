import sqlite3

def create_tables():
    conn = sqlite3.connect('state.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS known_files (
        id INTEGER PRIMARY KEY,
        file_name TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transcribe_queue (
        id INTEGER PRIMARY KEY,
        file_name TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS convert_queue (
        id INTEGER PRIMARY KEY,
        file_name TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS skip_files (
        id INTEGER PRIMARY KEY,
        file_name TEXT NOT NULL,
        reason TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
