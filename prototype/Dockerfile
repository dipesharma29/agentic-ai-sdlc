# Runs ADK in Linux. Needed on machines where Windows Smart App Control
# blocks the compiled Python packages ADK depends on.
FROM python:3.12-slim
WORKDIR /app/prototype
COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt
EXPOSE 8000
# The project folder is mounted at /app at run time (see docker-compose.yml).
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8000"]
