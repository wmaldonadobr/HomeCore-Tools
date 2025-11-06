# HomeCore Add-ons Repository

[![GitHub Release](https://img.shields.io/github/release/homecore/homecore-tools-addon.svg?style=flat-square)](https://github.com/homecore/homecore-tools-addon/releases)
[![License](https://img.shields.io/github/license/homecore/homecore-tools-addon.svg?style=flat-square)](LICENSE)

Repositório oficial de add-ons HomeCore para Home Assistant.

## Sobre

Este repositório contém add-ons desenvolvidos pela equipe HomeCore para facilitar a integração, manutenção e monitoramento de sistemas HomeCore no Home Assistant.

## Add-ons Disponíveis

### HomeCore Tools

Ferramentas de manutenção e atualização automática para sistemas HomeCore.

**Funcionalidades:**
- ✅ Verificação automática de atualizações via manifests
- ✅ Aplicação automática de atualizações (configurável)
- ✅ Backup automático antes de cada atualização
- ✅ Rollback automático em caso de falha
- ✅ Dashboard web para monitoramento
- ✅ Logs estruturados
- ✅ Notificações persistentes

[📖 Documentação Completa](homecore-tools/DOCS.md) | [📋 Changelog](homecore-tools/CHANGELOG.md)

## Instalação

### Método 1: Botão Rápido (Recomendado)

Clique no botão abaixo para adicionar o repositório automaticamente:

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fhomecore%2Fhomecore-tools-addon)

### Método 2: Manual

1. No Home Assistant, vá em **Configurações** > **Add-ons**
2. Clique no **ícone da loja** no canto superior direito
3. Clique no menu **⋮** (três pontos) no canto superior direito
4. Selecione **Repositórios**
5. Cole a URL abaixo e clique em **Adicionar**:

```
https://github.com/homecore/homecore-tools-addon
```

6. Encontre **"HomeCore Tools"** na lista de add-ons
7. Clique em **Instalar**

## Requisitos

- Home Assistant OS 2024.1.0 ou superior
- Integração HomeCore Beacon instalada e configurada

## Suporte

### Documentação

- **Documentação completa**: [DOCS.md](homecore-tools/DOCS.md)
- **Guia de instalação**: [INSTALL.md](homecore-tools/INSTALL.md)
- **Changelog**: [CHANGELOG.md](homecore-tools/CHANGELOG.md)

### Contato

- **Email**: suporte@homecore.com.br
- **Website**: https://homecore.com.br
- **Issues**: [GitHub Issues](https://github.com/homecore/homecore-tools-addon/issues)

## Desenvolvimento

### Estrutura do Repositório

```
homecore-tools-addon/
├── repository.yaml          # Configuração do repositório
├── README.md                # Este arquivo
└── homecore-tools/          # Add-on HomeCore Tools
    ├── config.yaml          # Configuração do add-on
    ├── Dockerfile           # Imagem Docker
    ├── icon.png             # Ícone do add-on
    ├── logo.png             # Logo do add-on
    ├── DOCS.md              # Documentação do usuário
    └── ...
```

### Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork este repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Reportar Problemas

Encontrou um bug ou tem uma sugestão? [Abra uma issue](https://github.com/homecore/homecore-tools-addon/issues/new).

## Licença

Este projeto é licenciado sob os termos da licença Apache 2.0. Veja [LICENSE](LICENSE) para detalhes.

## Créditos

Desenvolvido com ❤️ pela equipe [HomeCore](https://homecore.com.br)

---

**Versão do Repositório:** 1.0.0  
**Última Atualização:** 2025-11-05
