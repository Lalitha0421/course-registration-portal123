import os
import re

def get_tables_from_code():
    project_dir = r"c:\Users\DELL\OneDrive\Desktop\course_portal"
    found_tables = set()
    
    # Regex to find FROM table_name or JOIN table_name or INTO table_name or UPDATE table_name
    patterns = [
        re.compile(r"FROM\s+([a-zA-Z0-9_]+)", re.IGNORECASE),
        re.compile(r"JOIN\s+([a-zA-Z0-9_]+)", re.IGNORECASE),
        re.compile(r"INTO\s+([a-zA-Z0-9_]+)", re.IGNORECASE),
        re.compile(r"UPDATE\s+([a-zA-Z0-9_]+)", re.IGNORECASE)
    ]
    
    for root, dirs, files in os.walk(project_dir):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", errors="ignore") as f:
                        content = f.read()
                        for pattern in patterns:
                            matches = pattern.findall(content)
                            for match in matches:
                                found_tables.add(match.upper())
                except:
                    pass
    
    # Filter out common SQL keywords and dual
    keywords = {'DUAL', 'SELECT', 'WHERE', 'INSERT', 'NULL', 'SET', 'SYSDATE'}
    tables = sorted([t for t in found_tables if t not in keywords])
    
    print(f"Tables used in code ({len(tables)}):")
    for t in tables:
        print(f"- {t}")
    
    return tables

if __name__ == "__main__":
    get_tables_from_code()
