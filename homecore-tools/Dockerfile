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

# Instalar dependências do sistema
RUN apk add --no-cache \
    bash \
    curl \
    unzip \
    python3 \
    py3-pip \
    py3-aiohttp \
    py3-flask \
    jq \
    tzdata

# Instalar dependências Python
RUN pip3 install --no-cache-dir \
    aiohttp \
    flask \
    flask-cors \
    pyyaml \
    requests

# Copiar arquivos do rootfs
COPY rootfs /

# Copiar scripts hc-tools
COPY tools /tools

# Garantir permissões de execução
RUN chmod a+x /run.sh && \
    chmod a+x /usr/bin/hct-* && \
    chmod a+x /etc/services.d/hct-daemon/run && \
    chmod a+x /etc/services.d/hct-daemon/finish && \
    chmod a+x /tools/*.sh && \
    chmod a+x /tools/Molsmart/*.sh

# Criar diretórios necessários
RUN mkdir -p /data/logs /data/manifests /data/backups

# Script de inicialização
CMD ["/run.sh"]
