FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY services/resume-service/pyproject.toml ./pyproject.toml
RUN uv sync --no-dev
RUN python -c "from gliner import GLiNER; GLiNER.from_pretrained('urchade/gliner_multi_pii-v1')"

COPY services/resume-service/src/ src/
COPY contracts/proto/resume.proto /tmp/resume.proto
RUN .venv/bin/python -m grpc_tools.protoc \
    -I/tmp \
    --python_out=/app/src/api/grpc/generated \
    --grpc_python_out=/app/src/api/grpc/generated \
    /tmp/resume.proto

FROM python:3.12-slim

WORKDIR /app
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH="/app/src"

COPY --from=builder /app /app
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface

EXPOSE 50051 8080

CMD ["python", "-m", "main"]
