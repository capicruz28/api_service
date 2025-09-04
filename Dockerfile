FROM python:3.10-bullseye

ENV ACCEPT_EULA=Y
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema y ODBC Driver 17
RUN apt-get update && apt-get install -y \
    curl gnupg2 unixodbc-dev gcc g++ apt-transport-https software-properties-common \
    && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg \
    && install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/ \
    && echo "deb [arch=amd64] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -f microsoft.gpg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verificar instalación del driver
RUN odbcinst -q -d

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Configurar logging
ENV PYTHONUNBUFFERED=1

# Exponer el puerto
EXPOSE 10000

# Comando de healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# Ejecutar la app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000", "--log-level", "info"]