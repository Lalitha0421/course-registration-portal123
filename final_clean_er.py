import json
import re

def clean_er_diagram():
    with open('mermaid_parts_filtered.json', 'r') as f:
        parts = json.load(f)
    
    with open('er_diagram.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 1. Force replace the Mermaid block in data-full script tag
    pattern_full = re.compile(r'(<script id="data-full" type="text/plain">)(.*?)(</script>)', re.DOTALL)
    html = pattern_full.sub(rf'\1\n{parts["mermaid_full"]}\n\3', html)
    
    # 2. Directly inject table cards into the HTML container for maximum reliability
    # This replaces the placeholder or any previous content in dynamic-table-cards
    pattern_dynamic = re.compile(r'(<div id="dynamic-table-cards">)(.*?)(</div>)', re.DOTALL)
    content_html = f'<div class="tables-grid">\n{parts["table_cards"]}\n</div>'
    html = pattern_dynamic.sub(rf'\1\n{content_html}\n\3', html)
    
    # 3. Ensure the summary stats are correct
    html = html.replace('>39<', '>21<')
    html = html.replace('39 Core Tables', '21 Core Tables')
    html = html.replace('39 Tables', '21 Core Tables')
    
    with open('er_diagram.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    clean_er_diagram()
