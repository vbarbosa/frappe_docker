# ERPNext — Guia de operação

Instância ERPNext (Frappe) rodando via Docker Compose nesta VM Oracle.
Acesso **exclusivamente pela VPN Tailscale** — invisível para a internet.

---

## Como subir / reiniciar o ERP

Sempre que precisar (re)subir o ERP, rode:

```bash
cd /home/ubuntu/GitHub/frappe_docker && sudo bash subir-erp.sh
```

O script `subir-erp.sh`:
1. Detecta o IP **atual** da Tailscale (`tailscale ip -4`).
2. Sobe o container `frontend` com a porta 8080 fixada nesse IP.
3. Mostra o binding aplicado e a URL de acesso.

> Não há IP hard-coded no `pwd.yml` — a linha usa `${TS_IP}:8080:8080`, e o
> script injeta o IP na hora. Se você reinstalar o Tailscale e o IP mudar,
> basta rodar o script de novo. Nada precisa ser editado à mão.

---

## Como acessar

Do seu PC (com Tailscale ligado), no navegador:

```
http://100.70.92.116:8080
```

(Se o IP da VPN tiver mudado, o `subir-erp.sh` imprime a URL correta ao final.)

---

## Comandos úteis

```bash
cd /home/ubuntu/GitHub/frappe_docker

# Ver containers e status
sudo docker compose -f pwd.yml ps

# Ver logs do frontend (ao vivo)
sudo docker compose -f pwd.yml logs -f frontend

# Parar tudo
sudo docker compose -f pwd.yml down

# Subir tudo (todos os serviços, com IP da VPN)
sudo TS_IP="$(tailscale ip -4 | head -n1)" docker compose -f pwd.yml up -d
```

---

## Segurança (resumo)

- Porta 8080 escuta **só no IP da Tailscale** (não em `0.0.0.0`).
- Firewall Oracle: portas 22/80/443/9000 restritas à faixa VPN `100.64.0.0/10`.
- Proteção em camadas: mesmo se o firewall for aberto por engano, o ERP
  continua invisível por causa do bind na VPN.

Detalhes completos de acesso da VM: `/home/ubuntu/ACESSO_VM_ORACLE.md`
