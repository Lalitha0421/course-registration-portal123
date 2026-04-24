from config import get_connection

def count_tables():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Refined query to exclude recycle bin and system tables
    cursor.execute("SELECT table_name FROM user_tables WHERE table_name NOT LIKE 'BIN$%' ORDER BY table_name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Total valid tables: {len(tables)}")
    print("Table List:")
    for t in tables:
        print(f"- {t}")
    
    conn.close()

if __name__ == "__main__":
    count_tables()
