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

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY run.sh /app/run.sh

# Copia a estrutura de serviços s6 corretamente
COPY rootfs/ /

# Permissões do serviço s6 + script inicial
RUN chmod +x /app/run.sh \
    && chmod +x /etc/services.d/homecore-tools/run

# Deixa o s6 ser o PID 1
CMD ["/init"]