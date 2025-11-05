ARG BUILD_ARCH=amd64
FROM ghcr.io/home-assistant/${BUILD_ARCH}-base:3.19

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash \
    curl \
    unzip \
    jq \
    ca-certificates

WORKDIR /app

COPY requirements.txt ./
RUN python3 -m ensurepip --upgrade \
 && pip3 install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY run.sh /app/run.sh

RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]
