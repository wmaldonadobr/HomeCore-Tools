ARG BUILD_ARCH=amd64
FROM ghcr.io/home-assistant/${BUILD_ARCH}-base-python:3.13

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apk add --no-cache \
    bash \
    curl \
    unzip \
    jq \
    ca-certificates

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY run.sh /app/run.sh

# Copy rootfs containing s6 service definitions
COPY rootfs/ /

# Make scripts executable
RUN chmod +x /app/run.sh /etc/services.d/homecore-tools/run

# Use s6-overlay init as entrypoint; this will run services defined under /etc/services.d
CMD ["/init"]
