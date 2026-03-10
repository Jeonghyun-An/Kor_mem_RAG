# syntax=docker/dockerfile:1.7
FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    TORCH_CUDA_ARCH_LIST="9.0" \
    MAX_JOBS=64 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y \
    python3.10 python3-pip python3-dev \
    build-essential git curl ninja-build \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.10 /usr/bin/python
RUN python -m pip install --upgrade pip setuptools wheel

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu124

RUN --mount=type=cache,target=/root/.cache/torch_extensions \
    TMPDIR=/tmp \
    pip install packaging ninja && \
    TMPDIR=/tmp pip install flash-attn --no-build-isolation --no-cache-dir

WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]