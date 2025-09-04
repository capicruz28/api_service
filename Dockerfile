FROM python:3.10

ENV ACCEPT_EULA=Y
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema y ODBC Driver 17
RUN apt-get update && apt-get install -y \
    gnupg2 curl unixodbc-dev gcc g++ apt-transport-https software-properties-common \
    && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg \
    && install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/ \
    && sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/debian/10/prod buster main" > /etc/apt/sources.list.d/mssql-release.list' \
    && apt-get update && apt-get install -y msodbcsql17 \
    && rm -f microsoft.gpg \
    && apt-get clean

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el código fuente
COPY . .

# Expone el puerto
EXPOSE 10000

# Comando para ejecutar la app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
