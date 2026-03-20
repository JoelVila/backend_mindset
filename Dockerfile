FROM python:3.11-slim

# Hugging Face Spaces requires a non-root user with uid 1000
RUN useradd -m -u 1000 user

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Hugging Face Spaces uses port 7860
EXPOSE 7860

USER user

ENTRYPOINT ["./entrypoint.sh"]
