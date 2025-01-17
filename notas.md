# crear espacio virtual 
python -m venv .venv     

# acceder al espacio virtual 
venv\Scripts\activate

# ejecutar apis
uvicorn app.main:app --reload

# crear (.env) para conexion db
DB_SERVER=perufashions9
DB_USER=sa
DB_PASSWORD=HebsMaq
DB_DATABASE=bdtex
DB_PORT=1433

# GITHUB
# Comandos Básicos de Git
git init: Inicializa un nuevo repositorio Git en el directorio actual.
git clone <url>: Clona un repositorio remoto en tu máquina local.
git status: Muestra el estado actual del repositorio, incluyendo archivos modificados y no rastreados.
git add <archivo>: Agrega archivos al área de preparación (staging area).
git commit -m "mensaje": Crea un commit con los cambios en el área de preparación.
git push: Sube los commits al repositorio remoto.
git pull: Descarga y fusiona los cambios del repositorio remoto.
git fetch: Descarga cambios del repositorio remoto sin fusionarlos.
git merge <rama>: Fusiona la rama especificada con la rama actual.
git branch: Lista las ramas existentes.
git checkout <rama>: Cambia a la rama especificada.
git log: Muestra el historial de commits.
git diff: Muestra las diferencias entre el área de trabajo y el área de preparación o entre commits.

# Comandos Avanzados
git branch <nombre-rama>: Crea una nueva rama.
git checkout -b <nombre-rama>: Crea y cambia a una nueva rama.
git rebase <rama>: Reaplica commits de la rama actual sobre otra rama.
git stash: Guarda temporalmente los cambios no confirmados.
git stash pop: Restaura los cambios guardados con stash y los elimina de la pila de stash.
git reset <archivo>: Quita un archivo del área de preparación.
git reset --hard <commit>: Restablece el repositorio a un estado anterior (¡usa con cuidado!).
git tag <nombre-tag>: Crea una etiqueta en el commit actual.
git remote add <nombre> <url>: Agrega un nuevo repositorio remoto.
git remote -v: Muestra los repositorios remotos configurados.

# Comandos relacionados con GitHub
git push origin <rama>: Sube los commits de una rama específica al repositorio remoto.
git pull origin <rama>: Descarga cambios de una rama específica y los fusiona.
git clone <url>: Clona un repositorio GitHub en tu máquina local.
git remote set-url origin <url>: Cambia la URL del repositorio remoto.
gh repo create: (usando la CLI de GitHub) Crea un nuevo repositorio en GitHub.
gh pr create: (usando la CLI de GitHub) Crea un nuevo pull request en GitHub.