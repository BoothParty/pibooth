# Utiliser une image Python comme base
FROM python:3.7-slim-buster

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libsmpeg-dev \
    libportmidi-dev \
    libavformat-dev \
    libswscale-dev \
    libfreetype6-dev \
    libcups2-dev \
    libjpeg-dev \
    libtiff-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers du projet
COPY . /app/

# Installer pibooth avec les extras
RUN pip install -e .[printer]

# Commande par défaut
ENTRYPOINT ["pibooth-config"]