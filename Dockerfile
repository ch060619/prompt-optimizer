FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1
RUN addgroup --system rabbit && adduser --system --ingroup rabbit rabbit
COPY --chown=rabbit:rabbit backend ./backend
COPY --chown=rabbit:rabbit data ./data
COPY --chown=rabbit:rabbit README.md LICENSE ./
COPY --from=frontend --chown=rabbit:rabbit /app/frontend/dist ./frontend/dist
RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e backend
USER rabbit
EXPOSE 8000
CMD ["uvicorn", "prompt_optimizer.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
