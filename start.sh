#!/bin/bash

# Activar entorno virtual (si es necesario)
# source path/al/entorno/virtual/bin/activate

# Establecer variables de entorno necesarias para la aplicación Flask
export FLASK_APP=app.py
export FLASK_ENV=production

# Ejecutar la aplicación Flask con gunicorn
gunicorn app:app
