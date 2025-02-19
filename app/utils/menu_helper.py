from typing import List, Dict
from app.schemas.menu import MenuItem, MenuResponse

def build_menu_tree(menu_items: List[Dict]) -> List[MenuItem]:
    """
    Construye un árbol de menú jerárquico a partir de una lista plana de items
    
    Args:
        menu_items: Lista de diccionarios con información del menú
        
    Returns:
        List[MenuItem]: Lista de items de menú en estructura jerárquica
    """
    menu_dict: Dict[int, MenuItem] = {}
    root_items: List[MenuItem] = []

    # Primero, crear un diccionario de todos los items
    for item in menu_items:
        menu_dict[item['MenuId']] = MenuItem(
            id=item['MenuId'],
            name=item['Name'],
            icon=item['Icon'],
            path=item['Path'],
            order_index=item['OrderIndex'],
            level=item['Level'],
            children=[]
        )

    # Luego, construir la estructura jerárquica
    for item in menu_items:
        if item['ParentId'] is None:
            root_items.append(menu_dict[item['MenuId']])
        else:
            parent = menu_dict[item['ParentId']]
            parent.children.append(menu_dict[item['MenuId']])

    # Ordenar los items por order_index
    root_items.sort(key=lambda x: x.order_index)
    for item in menu_dict.values():
        item.children.sort(key=lambda x: x.order_index)

    return root_items

def create_menu_response(menu_items: List[Dict]) -> MenuResponse:
    """
    Crea una respuesta de menú completa
    
    Args:
        menu_items: Lista de diccionarios con información del menú
        
    Returns:
        MenuResponse: Respuesta formateada del menú
    """
    menu_tree = build_menu_tree(menu_items)
    return MenuResponse(menu=menu_tree)