# Backup dos volumes Docker (ERP / ury) — 22/08/2026

Os containers e imagens do frappe/ury foram **removidos** desta VM para liberar
espaço em disco (o projeto estava parado desde ~08/2026; o disco precisava de
folga para o jogo Godot de Curitiba). Os **dados foram preservados** em
arquivos compactados.

## Onde estão

Fora do git, em `/home/ubuntu/backups/docker-volumes/`:

| Arquivo | Origem (volume Docker) | Tamanho | Conteúdo |
|---|---|---|---|
| `frappe_docker_db-data.tar.gz` | `frappe_docker_db-data` | 35MB (351MB descompactado) | datadir do MariaDB — os bancos do ERP |
| `frappe_docker_sites.tar.gz` | `frappe_docker_sites` | 80KB | `sites/`, com `site_config.json` e `common_site_config.json` |

`SHA256SUMS` no mesmo diretório tem os hashes para conferência.

> **Por que não estão no repo:** `site_config.json` contém a `encryption_key` do
> site e a senha root do MariaDB, e este repo tem remote público no GitHub.
> Commitar os arquivos vazaria essas credenciais.

Descartados sem backup por não terem dado nenhum: `frappe_docker_logs`,
`frappe_docker_redis-queue-data` (cache), `buildx_buildkit_ury-builder0_state`
(2,7GB de cache de build) e volumes anônimos de `node_modules`.

## Estado dos arquivos

Os dois containers foram parados com saída limpa (`Exited (0)`) antes do
`tar`, então o datadir do MariaDB é um snapshot consistente — não é um
arquivo aberto no meio de uma escrita.

## Como restaurar

As imagens base saem do Docker Hub de novo; a única que exige rebuild é a
`ury-erp:v15` (via `docker compose build`, ver README/subir.sh deste repo).

```bash
cd /home/ubuntu/GitHub/frappe_docker

# 1. recria os volumes vazios
docker volume create frappe_docker_db-data
docker volume create frappe_docker_sites

# 2. despeja o conteúdo de volta (o tar guarda a pasta _data)
cd /home/ubuntu/backups/docker-volumes
sudo tar xzf frappe_docker_db-data.tar.gz -C /var/lib/docker/volumes/frappe_docker_db-data
sudo tar xzf frappe_docker_sites.tar.gz   -C /var/lib/docker/volumes/frappe_docker_sites

# 3. rebuild da imagem do app + sobe
cd /home/ubuntu/GitHub/frappe_docker
./subir.sh      # ou: docker compose build && docker compose up -d
```

**Importante:** o datadir é um snapshot *físico* do MariaDB — precisa voltar na
**mesma versão**, `mariadb:11.8`. Subir com uma versão diferente pode falhar ou
exigir `mariadb-upgrade`. Idem para o Redis (`redis:6.2-alpine`), embora ali não
haja dado a preservar.
