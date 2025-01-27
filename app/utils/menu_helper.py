from typing import List

def build_menu_tree(menu_items: List[dict]) -> List[dict]:
    menu_dict = {}
    root_items = []

    # Primero, crear un diccionario de todos los items
    for item in menu_items:
        menu_dict[item['MenuId']] = {
            'id': item['MenuId'],
            'name': item['Name'],
            'icon': item['Icon'],
            'path': item['Path'],
            'order_index': item['OrderIndex'],
            'level': item['Level'],
            'children': []
        }

    # Luego, construir la estructura jerárquica
    for item in menu_items:
        if item['ParentId'] is None:
            root_items.append(menu_dict[item['MenuId']])
        else:
            parent = menu_dict[item['ParentId']]
            parent['children'].append(menu_dict[item['MenuId']])

    return root_items