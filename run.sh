#!/bin/bash

export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/application_default_credentials.json"

# luego lanza gunicorn
exec gunicorn -b :8080 --timeout 512 app:app