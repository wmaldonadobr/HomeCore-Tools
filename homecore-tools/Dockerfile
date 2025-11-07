ARG BUILD_FROM
FROM $BUILD_FROM

# Informações do build
ARG BUILD_ARCH
ARG BUILD_VERSION

# Metadados do add-on
LABEL \
    io.hass.name="HomeCore Tools" \
    io.hass.description="Ferramentas de manutenção e atualização para sistemas HomeCore" \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.type="addon" \
    io.hass.arch="${BUILD_ARCH}"

# Instalar dependências
RUN apk add --no-cache \
    bash \
    curl \
    unzip \
    python3 \
    py3-pip \
    py3-aiohttp \
    py3-flask \
    py3-yaml \
    py3-requests \
    jq \
    tzdata

RUN pip3 install --no-cache-dir --break-system-packages \
    flask-cors

# Copiar rootfs
COPY rootfs /

# Copiar scripts extras
COPY run.sh /run.sh
COPY tools /tools

# ✅ Aqui dizemos ao Python onde estão seus módulos HomeCore
ENV PYTHONPATH="/usr/lib/homecore:${PYTHONPATH}"

# ✅ Criar um launcher limpo para o daemon
RUN printf '#!/bin/sh\nexec python3 /usr/lib/homecore/hct_daemon.py "$@"\n' > /usr/bin/hct-daemon && \
    chmod +x /usr/bin/hct-daemon

# Permissões
RUN chmod a+x /run.sh && \
    chmod a+x /etc/cont-init.d/10-homecore.sh && \
    chmod a+x /etc/services.d/hct-daemon/run && \
    chmod a+x /etc/services.d/hct-daemon/finish && \
    chmod a+x /tools/*.sh && \
    chmod a+x /tools/Molsmart/*.sh

# Diretórios padrão
RUN mkdir -p /data/logs /data/manifests /data/backups

CMD ["/init"]
