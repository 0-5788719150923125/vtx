FROM nvcr.io/nvidia/cuda:12.2.0-devel-ubuntu22.04

ENV TRANSFORMERS_CACHE="/tmp"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    git \
    ninja-build \
    python3-dev \
    python3-pip \
    python3-packaging \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY src/ /src

CMD ["python3", "main.py"]
