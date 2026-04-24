import json

def generate_filtered_html():
    # Intended tables from schema.sql
    intended_tables = {
        "SYSTEM_CONFIG", "USERS", "FACULTY", "STUDENTS", "COURSE_MASTER",
        "COURSE_PREREQUISITES", "COURSE_OBJECTIVES", "COURSE_OUTCOMES", "COURSE_DESCRIPTION",
        "TEXT_BOOKS", "REFERENCE_BOOKS", "COURSE_INSTANCE", "STUDENT_REGISTRATION",
        "STUDENT_REGISTRATION_COURSES", "RESULTS", "ATTENDANCE", "COORDINATOR",
        "PROGRAM_OUTCOMES", "CO_PO_MAPPING", "EVALUATION_DETAILS", "COURSE_EQUIVALENTS"
    }

    with open('schema_dump.json', 'r') as f:
        full_schema = json.load(f)

    # Filter schema
    schema = {k: v for k, v in full_schema.items() if k.upper() in intended_tables}

    # Define color mapping
    table_categories = {
        "USERS": "#1d4ed8",
        "FACULTY": "#059669",
        "STUDENTS": "#059669",
        "COORDINATOR": "#059669",
        
        "COURSE_MASTER": "#1e3a5f",
        "COURSE_INSTANCE": "#1e3a5f",
        "COURSE_DESCRIPTION": "#1e3a5f",
        "COURSE_OBJECTIVES": "#1e3a5f",
        "COURSE_OUTCOMES": "#1e3a5f",
        "COURSE_PREREQUISITES": "#1e3a5f",
        "TEXT_BOOKS": "#1e3a5f",
        "REFERENCE_BOOKS": "#1e3a5f",
        "EVALUATION_DETAILS": "#1e3a5f",
        "COURSE_EQUIVALENTS": "#1e3a5f",
        
        "STUDENT_REGISTRATION": "#92400e",
        "STUDENT_REGISTRATION_COURSES": "#92400e",
        
        "PROGRAM_OUTCOMES": "#7c3aed",
        "CO_PO_MAPPING": "#7c3aed",
        
        "RESULTS": "#7c1d1d",
        "ATTENDANCE": "#7c1d1d",
        "SYSTEM_CONFIG": "#0891b2"
    }

    def get_color(tbl):
        return table_categories.get(tbl, "#64748b")

    # Generate Mermaid Full
    mermaid_full = ["erDiagram"]
    for tbl, data in schema.items():
        mermaid_full.append(f"    {tbl} {{")
        for col in data['columns']:
            ctype = col['type'].lower()
            if 'varchar' in ctype: ctype = 'string'
            elif 'number' in ctype: ctype = 'int'
            elif 'date' in ctype: ctype = 'date'
            
            note = ""
            if col['name'] in data['pks']: note = "PK"
            # Manually flag known FKs for better labeling in drawing
            known_fks = {
                "STUDENTS": ["USER_ID", "ADVISOR_ID"],
                "FACULTY": ["USER_ID"],
                "COURSE_INSTANCE": ["COURSE_ID", "FACULTY_ID"],
                "STUDENT_REGISTRATION": ["STUDENT_ID"],
                "STUDENT_REGISTRATION_COURSES": ["REG_ID", "COURSE_INSTANCE_ID"],
                "RESULTS": ["STUDENT_ID", "COURSE_ID"],
                "ATTENDANCE": ["STUDENT_ID", "COURSE_INSTANCE_ID"],
                "CO_PO_MAPPING": ["COURSE_OUTCOME_ID", "PROGRAM_OUTCOME_ID"]
            }
            if col['name'] in known_fks.get(tbl, []):
                note = "FK" if not note else "PK, FK"
            
            mermaid_full.append(f"        {ctype} {col['name']} {note}")
        mermaid_full.append("    }")

    # Relationships from Project Design (filling in missing DB constraints)
    manual_rels = [
        "USERS ||--o{ STUDENTS : \"USER_ID\"",
        "FACULTY ||--o{ STUDENTS : \"ADVISOR_ID\"",
        "STUDENTS ||--o{ STUDENT_REGISTRATION : \"STUDENT_ID\"",
        "STUDENTS ||--o{ RESULTS : \"STUDENT_ID\"",
        "STUDENTS ||--o{ ATTENDANCE : \"STUDENT_ID\"",
        "COURSE_MASTER ||--o{ RESULTS : \"COURSE_ID\"",
        "COURSE_MASTER ||--o{ COURSE_INSTANCE : \"COURSE_ID\"",
        "FACULTY ||--o{ COURSE_INSTANCE : \"FACULTY_ID\"",
        "STUDENT_REGISTRATION ||--o{ STUDENT_REGISTRATION_COURSES : \"REG_ID\"",
        "COURSE_INSTANCE ||--o{ STUDENT_REGISTRATION_COURSES : \"COURSE_INSTANCE_ID\"",
        "COURSE_MASTER ||--o{ COURSE_DESCRIPTION : \"COURSE_ID\"",
        "COURSE_MASTER ||--o{ COURSE_OBJECTIVES : \"COURSE_ID\"",
        "COURSE_MASTER ||--o{ COURSE_OUTCOMES : \"COURSE_ID\"",
        "COURSE_MASTER ||--o{ TEXT_BOOKS : \"COURSE_ID\"",
        "COURSE_MASTER ||--o{ REFERENCE_BOOKS : \"COURSE_ID\"",
        "COURSE_MASTER ||--o{ COURSE_PREREQUISITES : \"COURSE_ID\"",
        "COURSE_MASTER ||--o{ COURSE_PREREQUISITES : \"PREREQUISITE_COURSE_ID\"",
        "COURSE_OUTCOMES ||--o{ CO_PO_MAPPING : \"COURSE_OUTCOME_ID\"",
        "PROGRAM_OUTCOMES ||--o{ CO_PO_MAPPING : \"PROGRAM_OUTCOME_ID\"",
        "USERS ||--o{ FACULTY : \"USER_ID\"",
        "COURSE_MASTER ||--o{ EVALUATION_DETAILS : \"COURSE_ID\""
    ]
    
    for rel in manual_rels:
        mermaid_full.append(f"    {rel}")

    # Generate Table Cards
    table_cards = []
    for tbl in sorted(schema.keys()):
        data = schema[tbl]
        color = get_color(tbl)
        card = [f'  <div class="tbl-card">', f'    <div class="tbl-header" style="background:{color}">{tbl}</div>', '    <div class="tbl-body">']
        for col in data['columns']:
            note = ""
            if col['name'] in data['pks']: note = '<span class="col-note">PK</span>'
            # Note FKs in cards too
            known_fks = {
                "STUDENTS": {"USER_ID": "USERS", "ADVISOR_ID": "FACULTY"},
                "FACULTY": {"USER_ID": "USERS"},
                "COURSE_INSTANCE": {"COURSE_ID": "COURSE_MASTER", "FACULTY_ID": "FACULTY"},
                "STUDENT_REGISTRATION": {"STUDENT_ID": "STUDENTS"},
                "STUDENT_REGISTRATION_COURSES": {"REG_ID": "STUDENT_REGISTRATION", "COURSE_INSTANCE_ID": "COURSE_INSTANCE"},
                "RESULTS": {"STUDENT_ID": "STUDENTS", "COURSE_ID": "COURSE_MASTER"},
                "ATTENDANCE": {"STUDENT_ID": "STUDENTS", "COURSE_INSTANCE_ID": "COURSE_INSTANCE"},
                "CO_PO_MAPPING": {"COURSE_OUTCOME_ID": "COURSE_OUTCOMES", "PROGRAM_OUTCOME_ID": "PROGRAM_OUTCOMES"},
                "COURSE_PREREQUISITES": {"COURSE_ID": "COURSE_MASTER", "PREREQUISITE_COURSE_ID": "COURSE_MASTER"},
                "TEXT_BOOKS": {"COURSE_ID": "COURSE_MASTER"},
                "REFERENCE_BOOKS": {"COURSE_ID": "COURSE_MASTER"},
                "COURSE_DESCRIPTION": {"COURSE_ID": "COURSE_MASTER"},
                "COURSE_OBJECTIVES": {"COURSE_ID": "COURSE_MASTER"},
                "COURSE_OUTCOMES": {"COURSE_ID": "COURSE_MASTER"},
                "COORDINTAOR": {"FACULTY_ID": "FACULTY", "STUDENT_ID": "STUDENTS"}
            }
            if tbl in known_fks and col['name'] in known_fks[tbl]:
                ref = known_fks[tbl][col['name']]
                note += f'<span class="col-note" title="FK to {ref}">FK</span>'
            
            card.append(f'      <div class="col-row"><span class="col-name">{note}{col["name"]}</span><span class="col-type">{col["type"]}</span></div>')
        card.append('    </div>')
        card.append('  </div>')
        table_cards.append("\n".join(card))

    return {
        "mermaid_full": "\n".join(mermaid_full),
        "table_cards": "\n".join(table_cards),
        "total_tables": len(intended_tables)
    }

if __name__ == "__main__":
    import json
    res = generate_filtered_html()
    with open("mermaid_parts_filtered.json", "w") as f:
        json.dump(res, f, indent=4)
