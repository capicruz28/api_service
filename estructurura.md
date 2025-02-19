app/
├── alembic/                  # Migraciones de base de datos
├── api/
│   └── v1/
│       ├── endpoints/
│       │   ├── empleados.py  # Endpoints de empleados
│       │   ├── usuarios.py   # Endpoints de usuarios
│       │   └── menus.py      # Endpoints de menús
│       └── api.py            # Router principal v1
├── core/
│   ├── __init__.py
│   ├── config.py            # Configuración centralizada
│   ├── exceptions.py        # Manejo de excepciones
│   └── logging_config.py    # Configuración de logging
├── db/
│   ├── __init__.py
│   ├── connection.py        # Gestión de conexiones
│   └── queries.py          # Queries centralizados
├── models/
│   ├── domain/             # Modelos de dominio
│   │   ├── __init__.py
│   │   ├── empleado.py
│   │   ├── usuario.py
│   │   └── menu.py
│   └── schemas/            # Schemas Pydantic
│       ├── __init__.py
│       ├── empleado.py
│       ├── usuario.py
│       └── menu.py
├── services/               # Lógica de negocio
│   ├── __init__.py
│   ├── empleado_service.py
│   ├── usuario_service.py
│   └── menu_service.py
├── utils/                 # Utilidades
│   ├── __init__.py
│   └── menu_helper.py
├── tests/                 # Tests unitarios y de integración
│   ├── __init__.py
│   ├── test_empleados.py
│   ├── test_usuarios.py
│   └── test_menus.py
├── .env                   # Variables de entorno
├── .gitignore            # Archivos ignorados por git
├── requirements.txt      # Dependencias del proyecto
└── main.py              # Punto de entrada de la aplicación