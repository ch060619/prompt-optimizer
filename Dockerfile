FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY backend ./backend
COPY data ./data
COPY README.md LICENSE ./
COPY --from=frontend /app/frontend/dist ./frontend/dist
RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e backend
EXPOSE 8000
CMD ["uvicorn", "prompt_optimizer.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
