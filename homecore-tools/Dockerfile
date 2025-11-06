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

# Instalar dependências do sistema e pacotes Python via apk
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

# Instalar flask-cors via pip com --break-system-packages (necessário no Alpine 3.19+)
# Outros pacotes já foram instalados via apk acima
RUN pip3 install --no-cache-dir --break-system-packages \
    flask-cors

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
