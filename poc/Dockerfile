# Fix Agent POC: ADK in Linux (avoids Windows Smart App Control blocking ADK's packages).
# Add language toolchains here when the agent targets other repos (e.g. a JDK for Java).
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory '*'
WORKDIR /app/poc
COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt
EXPOSE 8000
# adk web serves both the chat UI and the REST API (/run, /apps/...) on port 8000.
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8000"]
