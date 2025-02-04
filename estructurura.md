```
app/
├── alembic/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   ├── empleados.py
│       │   ├── usuarios.py
│       │   └── menus.py
│       └── api.py
├── core/
│   ├── config.py
│   └── exceptions.py
├── db/
│   ├── connection.py
│   └── queries.py
├── models/
│   ├── domain/
│   └── schemas/
│       ├── empleado.py
│       ├── usuario.py
│       └── menu.py
├── services/
│   ├── empleado_service.py
│   ├── usuario_service.py
│   └── menu_service.py
├── utils/
│   ├── menu_helper.py
│   └── logging_config.py
├── tests/
├── .env
├── .gitignore
├── requirements.txt
└── main.py