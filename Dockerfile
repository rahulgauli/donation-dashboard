FROM python:3.12

WORKDIR /app

# Install deps
RUN pip install --no-cache-dir pipenv

COPY Pipfile Pipfile.lock ./
# Install into system site-packages so we don't need pipenv at runtime
RUN PIPENV_VENV_IN_PROJECT=0 pipenv install --system --deploy --ignore-pipfile

# Copy the code
COPY . .

EXPOSE 8000

# Start FastAPI via Uvicorn; adjust "main:app" to your module:app if different
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
