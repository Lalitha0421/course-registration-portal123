import json

def inject_data():
    with open('mermaid_parts_filtered.json', 'r') as f:
        parts = json.load(f)
    
    with open('er_diagram.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Replace placeholders
    html = html.replace('#MERMAID_FULL#', parts['mermaid_full'])
    html = html.replace('#TABLE_CARDS#', parts['table_cards'])
    
    # Update showView to handle dynamic table cards
    old_show_view = """  if (v === 'ref') {
    diagramView.style.display = 'none';
    tableView.style.display = 'block';
  } else {"""
    
    new_show_view = """  if (v === 'ref') {
    diagramView.style.display = 'none';
    tableView.style.display = 'block';
    // Inject dynamic cards if empty
    const container = document.getElementById('dynamic-table-cards');
    if (container && !container.innerHTML.trim()) {
      container.innerHTML = '<div class="tables-grid">' + document.getElementById('data-table-cards').innerHTML + '</div>';
    }
  } else {"""
    
    html = html.replace(old_show_view, new_show_view)
    
    with open('er_diagram.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    inject_data()
