import json

def generate_html():
    with open('schema_dump.json', 'r') as f:
        schema = json.load(f)

    # Define color mapping
    # #1d4ed8: Auth/Users
    # #059669: Faculty/People
    # #1e3a5f: Course/Syllabus
    # #92400e: Registration
    # #7c3aed: OBE/NBA
    # #7c1d1d: Performance/Attendance
    # #64748b: Misc/Other

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
        "COURSE": "#1e3a5f", # Duplicate?
        "COURSE_OUTCOME": "#1e3a5f", # Duplicate?
        "LAB_EXPERIMENT": "#1e3a5f",
        
        "STUDENT_REGISTRATION": "#92400e",
        "STUDENT_REGISTRATION_COURSES": "#92400e",
        
        "PROGRAM_OUTCOMES": "#7c3aed",
        "CO_PO_MAPPING": "#7c3aed",
        "COURSE_PO_MAPPING": "#7c3aed",
        
        "RESULTS": "#7c1d1d",
        "ATTENDANCE": "#7c1d1d"
    }

    def get_color(tbl):
        return table_categories.get(tbl, "#64748b")

    # Generate Mermaid Full
    mermaid_full = ["erDiagram"]
    for tbl, data in schema.items():
        mermaid_full.append(f"    {tbl} {{")
        for col in data['columns']:
            # Simplified type
            ctype = col['type'].lower()
            if 'varchar' in ctype: ctype = 'string'
            elif 'number' in ctype: ctype = 'int'
            elif 'date' in ctype: ctype = 'date'
            
            note = ""
            if col['name'] in data['pks']: note = "PK"
            # FK detection from data['fks']
            for fk in data['fks']:
                if fk['column'] == col['name']:
                    note = "FK" if not note else "PK, FK"
            
            mermaid_full.append(f"        {ctype} {col['name']} {note}")
        mermaid_full.append("    }")

    # Generate Relationships
    added_rels = set()
    for tbl, data in schema.items():
        for fk in data['fks']:
            rel = tuple(sorted([tbl, fk['ref_table']]))
            # Mermaid ER doesn't handle multiple rels well sometimes, but let's try
            mermaid_full.append(f"    {fk['ref_table']} ||--o{{ {tbl} : \"{fk['column']}\"")

    # Generate Table Cards
    table_cards = []
    for tbl in sorted(schema.keys()):
        data = schema[tbl]
        color = get_color(tbl)
        card = [f'  <div class="tbl-card">', f'    <div class="tbl-header" style="background:{color}">{tbl}</div>', '    <div class="tbl-body">']
        for col in data['columns']:
            note = ""
            if col['name'] in data['pks']: note = '<span class="col-note">PK</span>'
            for fk in data['fks']:
                if fk['column'] == col['name']:
                    note += f'<span class="col-note" title="FK to {fk["ref_table"]}">FK</span>'
            
            card.append(f'      <div class="col-row"><span class="col-name">{note}{col["name"]}</span><span class="col-type">{col["type"]}</span></div>')
        card.append('    </div>')
        card.append('  </div>')
        table_cards.append("\n".join(card))

    # Output parts to be inserted into the HTML template
    return {
        "mermaid_full": "\n".join(mermaid_full),
        "table_cards": "\n".join(table_cards),
        "total_tables": len(schema)
    }

if __name__ == "__main__":
    res = generate_html()
    with open("mermaid_parts.json", "w") as f:
        json.dump(res, f, indent=4)
