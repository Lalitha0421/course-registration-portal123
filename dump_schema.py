import os
from config import get_connection
import json

def get_schema():
    conn = get_connection()
    cursor = conn.cursor()
    
    schema = {}
    
    # Detect DB type
    db_type = "ORACLE"
    try:
        # Check if it's SQLite
        import sqlite3
        if isinstance(conn, sqlite3.Connection):
            db_type = "SQLITE"
    except:
        pass
        
    print(f"Detected DB Type: {db_type}")
    
    if db_type == "ORACLE":
        # Get tables
        cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            # Get columns
            cursor.execute("""
                SELECT column_name, data_type, nullable 
                FROM user_tab_columns 
                WHERE table_name = :1 
                ORDER BY column_id
            """, (table,))
            columns = []
            for col in cursor.fetchall():
                columns.append({
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2] == 'Y'
                })
            
            # Get PKs
            cursor.execute("""
                SELECT cols.column_name
                FROM all_constraints cons, all_cons_columns cols
                WHERE cols.table_name = :1
                AND cons.constraint_type = 'P'
                AND cons.constraint_name = cols.constraint_name
                AND cons.owner = cols.owner
            """, (table,))
            pks = [row[0] for row in cursor.fetchall()]
            
            # Get FKs
            cursor.execute("""
                SELECT a.column_name, c_pk.table_name AS r_table_name, b.column_name AS r_column_name
                FROM all_cons_columns a
                JOIN all_constraints c ON a.owner = c.owner AND a.constraint_name = c.constraint_name
                JOIN all_constraints c_pk ON c.r_owner = c_pk.owner AND c.r_constraint_name = c_pk.constraint_name
                JOIN all_cons_columns b ON b.owner = c_pk.owner AND b.constraint_name = c_pk.constraint_name AND b.position = a.position
                WHERE c.constraint_type = 'R' AND a.table_name = :1
            """, (table,))
            fks = []
            for fk in cursor.fetchall():
                fks.append({
                    "column": fk[0],
                    "ref_table": fk[1],
                    "ref_column": fk[2]
                })
                
            schema[table] = {
                "columns": columns,
                "pks": pks,
                "fks": fks
            }
            
    else: # SQLITE
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = []
            pks = []
            for col in cursor.fetchall():
                columns.append({
                    "name": col[1],
                    "type": col[2],
                    "nullable": col[3] == 0
                })
                if col[5] > 0:
                    pks.append(col[1])
            
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            fks = []
            for fk in cursor.fetchall():
                fks.append({
                    "column": fk[3],
                    "ref_table": fk[2],
                    "ref_column": fk[4]
                })
                
            schema[table] = {
                "columns": columns,
                "pks": pks,
                "fks": fks
            }
            
    conn.close()
    return schema

if __name__ == "__main__":
    try:
        schema = get_schema()
        with open("schema_dump.json", "w") as f:
            json.dump(schema, f, indent=4)
        print("Schema dumped to schema_dump.json")
    except Exception as e:
        print(f"Error: {e}")
