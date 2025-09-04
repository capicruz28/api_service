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
    && apt-get clean

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el código fuente
COPY . .

# Exponer el puerto
EXPOSE 10000

# Ejecutar la app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
