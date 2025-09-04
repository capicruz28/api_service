FROM debian:bullseye

ENV ACCEPT_EULA=Y
ENV DEBIAN_FRONTEND=noninteractive

# Instalar Python 3.10 y herramientas del sistema
RUN apt-get update && apt-get install -y \
    curl wget gnupg2 lsb-release unixodbc-dev gcc g++ make \
    software-properties-common apt-transport-https \
    python3.10 python3-pip python3.10-venv python3.10-dev

# Usar python3.10 como predeterminado
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Instalar ODBC Driver 17 para SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg \
    && install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/ \
    && echo "deb [arch=amd64] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm microsoft.gpg

# Instalar dependencias del proyecto
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar código fuente
COPY . .

# Exponer puerto de la app
EXPOSE 10000

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
