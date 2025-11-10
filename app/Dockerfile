# Image de base Python officielle
FROM python:3.11-slim

# Métadonnées de l'image
LABEL maintainer="behram.korkut@live.fr"
LABEL description="Application de migration Healthcare vers MongoDB"
LABEL version="1.0"

# Variables d'environnement Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copie du fichier requirements
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copie du code source
COPY . /app/src

# Création des répertoires nécessaires
RUN mkdir -p /app/logs /app/data

# Création d'un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Passage à l'utilisateur non-root
USER appuser

# Healthcheck (optionnel mais recommandé)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Point d'entrée par défaut
CMD ["python", "/app/src/migration.py"]
