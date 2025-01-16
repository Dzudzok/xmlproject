FROM python:3.9

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie plików do kontenera
COPY . /app

# Instalacja zależności
RUN pip install --no-cache-dir -r requirements.txt

# Eksportowanie portu 8080 dla Cloud Run
EXPOSE 8080

# Ustawienie zmiennej PORT
ENV PORT 8080

# Uruchomienie aplikacji
CMD ["python", "app.py"]
