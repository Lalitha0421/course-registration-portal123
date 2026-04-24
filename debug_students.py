from config import get_connection

def debug_fks():
    conn = get_connection()
    cursor = conn.cursor()
    
    table = 'STUDENTS'
    print(f"--- Constraints for {table} ---")
    cursor.execute("""
        SELECT constraint_name, constraint_type, r_owner, r_constraint_name, status
        FROM user_constraints 
        WHERE table_name = :1
    """, (table,))
    for row in cursor.fetchall():
        print(row)
    
    print(f"--- Columns for {table} ---")
    cursor.execute("SELECT column_name, data_type FROM user_tab_columns WHERE table_name = :1", (table,))
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    debug_fks()
