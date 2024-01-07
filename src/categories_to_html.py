from typing import List, Dict
import pandas as pd


class CategoryTree:
    def __init__(self):
        self.tree = {}

    def parse_categories(self, categories: List[str]) -> None:
        for category in categories:
            parts = category.split(" > ")
            current_level = self.tree
            for part in parts:
                if part not in current_level:
                    current_level[part] = {'subcategories': {}, 'todos': []}
                current_level = current_level[part]['subcategories']

    def add_todo_to_category(self, category_path: str, todo: str) -> None:
        parts = category_path.split(" > ")
        current_level = self.tree
        for part in parts[:-1]:
            if part not in current_level:
                current_level[part] = {'subcategories': {}, 'todos': []}
            current_level = current_level[part]['subcategories']

        last_part = parts[-1]
        if last_part not in current_level:
            current_level[last_part] = {'subcategories': {}, 'todos': []}

        current_level[last_part]['todos'].append(todo)

    def generate_html_with_todos(self, tree: Dict[str, dict] = None, parent_id: str = '') -> str:
        if tree is None:
            tree = self.tree

        if not tree:
            return ''

        html_content = '<ul>\n'
        for idx, (category, data) in enumerate(tree.items()):
            current_id = f"{parent_id}_{idx}" if parent_id else str(idx)
            has_subcategories_or_todos = bool(data['subcategories']) or bool(data['todos'])
            collapsible_class = 'collapsible' if has_subcategories_or_todos else ''
            display_style = 'none' if has_subcategories_or_todos else 'block'

            html_content += f'  <li>\n'
            html_content += f'    <span class="{collapsible_class}" onclick="toggleVisibility(\'{current_id}\')">{category}</span>\n'
            html_content += f'    <div id="{current_id}" style="display: {display_style};">\n'
            html_content += self.generate_html_with_todos(data['subcategories'], current_id)
            if data['todos']:
                html_content += f'    <ul>\n'
                for todo in data['todos']:
                    html_content += f'      <li style="list-style-type: disc;">{todo}</li>\n'
                html_content += f'    </ul>\n'
            html_content += f'    </div>\n'
            html_content += f'  </li>\n'
        html_content += '</ul>\n'

        html_output_with_todos = f"<html>\n<head>\n{self.CSS}\n{self.JAVASCRIPT}\n</head>\n<body>\n<div id='myUL'>\n{html_content}</div>\n</body>\n</html>"
        return html_output_with_todos

    JAVASCRIPT = """
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

    CSS = """
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
    tree = CategoryTree()
    categories = pd.read_csv('data/category_paths.csv')['show_category'].tolist()
    tree.parse_categories(categories)

    # Add todo item
    todo_item = "read Sapiens"
    category_path = "Broaden knowledge > Read books"
    tree.add_todo_to_category(category_path, todo_item)

    html_output_with_todos = tree.generate_html_with_todos()

    with open('output_collapsible.html', mode='w', encoding='utf-8') as file:
        file.write(html_output_with_todos)
