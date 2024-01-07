from typing import List, Dict

import pandas as pd


def parse_categories(categories: List[str]) -> Dict[str, dict]:
    tree = {}
    for category in categories:
        parts = category.split(" > ")
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {'subcategories': {}, 'todos': []}
            current_level = current_level[part]['subcategories']
    return tree


def generate_html_with_collapsible(tree: Dict[str, List[str]], parent_id: str = '') -> str:
    if not tree:
        return ''

    html = '<ul>\n'
    for idx, (category, sub_tree) in enumerate(tree.items()):
        current_id = f"{parent_id}_{idx}" if parent_id else str(idx)
        has_subcategories = bool(sub_tree)
        collapsible_class = 'collapsible' if has_subcategories else ''
        display_style = 'none' if has_subcategories else 'block'

        html += f'  <li>\n'
        html += f'    <span class="{collapsible_class}" onclick="toggleVisibility(\'{current_id}\')">{category}</span>\n'
        html += f'    <div id="{current_id}" style="display: {display_style};">\n'
        html += generate_html_with_collapsible(sub_tree, current_id)
        html += f'    </div>\n'
        html += f'  </li>\n'
    html += '</ul>\n'
    return html


def add_todo_to_category(tree: Dict[str, dict], category_path: str, todo: str) -> None:
    parts = category_path.split(" > ")
    current_level = tree
    for part in parts[:-1]:  # Go up to the second-to-last part
        if part not in current_level:
            current_level[part] = {'subcategories': {}, 'todos': []}
        current_level = current_level[part]['subcategories']

    # Handle the last part of the path separately
    last_part = parts[-1]
    if last_part not in current_level:
        current_level[last_part] = {'subcategories': {}, 'todos': []}

    # Add the todo to the last category
    current_level[last_part]['todos'].append(todo)


def generate_html_with_todos(tree: Dict[str, dict], parent_id: str = '') -> str:
    if not tree:
        return ''

    html = '<ul>\n'
    for idx, (category, data) in enumerate(tree.items()):
        current_id = f"{parent_id}_{idx}" if parent_id else str(idx)
        has_subcategories_or_todos = bool(data['subcategories']) or bool(data['todos'])
        collapsible_class = 'collapsible' if has_subcategories_or_todos else ''
        display_style = 'none' if has_subcategories_or_todos else 'block'

        html += f'  <li>\n'
        html += f'    <span class="{collapsible_class}" onclick="toggleVisibility(\'{current_id}\')">{category}</span>\n'
        html += f'    <div id="{current_id}" style="display: {display_style};">\n'
        html += generate_html_with_todos(data['subcategories'], current_id)
        if data['todos']:
            html += f'    <ul>\n'
            for todo in data['todos']:
                html += f'      <li style="list-style-type: disc;">{todo}</li>\n'
            html += f'    </ul>\n'
        html += f'    </div>\n'
        html += f'  </li>\n'
    html += '</ul>\n'
    return html


# JavaScript function to toggle visibility
javascript = """
<script>
function toggleVisibility(id) {
    var element = document.getElementById(id);
    if (element.style.display === "none") {
        element.style.display = "block";
    } else {
        element.style.display = "none";
    }
}
</script>
"""

# CSS for styling the collapsible elements
css = """
<style>
ul, #myUL {
  list-style-type: none;
}

#myUL {
  margin: 0;
  padding: 0;
}

.collapsible {
  cursor: pointer;
  font-weight: bold;
}

.collapsible:after {
  content: '\\229E';
  font-size: 12px;
  margin-left: 5px;
}

.collapsible:hover {
  color: #555;
}

.active:after {
  content: "\\229F";
}
</style>
"""


if __name__ == '__main__':
    categories = pd.read_csv('data/category_paths.csv').show_category.tolist()
    tree = parse_categories(categories)
    # Generate HTML with todos
    todo_item = "read Sapiens"
    category_path = "Broaden knowledge > Read books"
    add_todo_to_category(tree, category_path, todo_item)
    html_structure_with_todos = generate_html_with_todos(tree)
    html_output_with_todos = f"<html>\n<head>\n{css}\n{javascript}\n</head>\n<body>\n<div id='myUL'>\n{html_structure_with_todos}</div>\n</body>\n</html>"

    with open('output_collapsible.html', mode='w', encoding='utf-8') as file:
        file.write(html_output_with_todos)
