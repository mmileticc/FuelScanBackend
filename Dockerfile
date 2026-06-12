# Koristimo proverenu Playwright bazu sa instaliranim zavisnostima za pretraživače
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Prvo kopiramo requirements da bismo iskoristili Docker keširanje slojeva
COPY requirements.txt .

# Instalacija Python paketa
RUN pip install --no-cache-dir -r requirements.txt

# Kopiranje ostatka aplikacije (main.py, parser.py)
COPY . .

# Render podrazumevano sluša port 10000 ili onaj koji mu prosledimo, stavljamo 8000
EXPOSE 8000

# Pokretanje Uvicorn servera (main:app znaci fajl main.py, objekat app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]