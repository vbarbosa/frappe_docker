# URY POS — Interface Mobile (garçom no celular)

Integração da interface mobile do POS ao nosso fork, para permitir que garçons lancem
pedidos pelo **celular** (não só desktop/tablet).

## Origem

O POS v2 (React) do URY, por padrão, **bloqueia telas < 1024px** — feito para desktop/caixa.
A comunidade (contribuidor **bvisible / Jérémy Christillin**, issue ury-erp/ury#53) desenvolveu
uma **interface mobile-first** completa sobre o mesmo POS v2. Não há release oficial dela no
upstream ainda; nós a **integramos ao nosso fork** `vbarbosa/ury` (branch `develop`,
commit `feat(pos): add mobile-first layout (integrated from bvisible)`).

## O que foi integrado

- **13 componentes mobile** em `pos/src/components/mobile/`: `MobilePOSLayout`, `MobileHeader`,
  `MobileFooter`, `MobileMenuGrid`, `CategoryHorizontalScroll`, `FloatingCartButton`,
  `CartBottomSheet` (carrinho em "bottom sheet"), `CheckoutSummarySheet`, `MobileConfigBottomSheet`,
  `MobileOrderDetailsSheet`, `PaymentMethodSheet`, `PaymentSuccessSheet`, `PaymentErrorSheet`.
- Página `pos/src/pages/mobile/MobileOrders.tsx`.
- Hooks `useMediaQuery.ts` (com `useIsMobile`) e `useCheckout.ts`.
- Dependências novas: `framer-motion`, `motion`, `react-modal-sheet` (animações/gaveta).

## Como funciona (troca automática desktop ↔ mobile)

`POS.tsx` e `Orders.tsx` usam `useIsMobile()`. Se a tela é pequena, renderizam o layout
**mobile** (`MobilePOSLayout` / `MobileOrders`); senão, o desktop de sempre. **Mesmo código,
mesma URL** (`/pos`), sem instalação ou app separado — o navegador do celular carrega a versão
mobile automaticamente. O `ScreenSizeProvider` **não bloqueia mais** telas < 1024px.

## O que preservamos (não regrediu)

- **Tradução pt-BR** (`pos/src/i18n/locales/pt-BR.json`) + registro em `config.ts`.
- **Cliente padrão pré-selecionado** (`getDefaultCustomer` no `pos-store.ts`, `default_customer`
  no `pos-profile-api.ts`).

### Reconciliação de i18n (detalhe técnico)
Os componentes do bvisible usam um sistema de tradução estilo Frappe (`__('texto')`), diferente
do nosso (`useTranslation` + `t('chave')` com JSONs). Em vez de trocar ~60 chamadas, criamos um
**shim** `pos/src/lib/i18n.ts` que resolve os `__()`/`_()` pelas **nossas** traduções, via um
helper `getMobileString()` (`pos/src/i18n/index.ts`) que lê um mapa `"mobile"` adicionado a
`en/fr/ar/pt-BR.json`. O `lib/i18n.ts` do bvisible **não** foi importado (preserva nosso i18n).

## Como usar

1. Rebuildar a imagem (o mobile vem do fork via `apps.json`) e recriar os containers:
   ```bash
   cd /home/ubuntu/GitHub/frappe_docker
   docker build --secret id=apps_json,src=apps.json --build-arg FRAPPE_BRANCH=version-15 \
     --build-arg CACHE_BUST=$(date +%s) --tag ury-erp:v15 --file images/custom/Containerfile .
   export TS_IP=100.70.92.116
   docker compose -f pwd.yml -f ury.override.yml up -d --force-recreate
   ```
2. No **celular do garçom**, abrir `http://<host>:8080/pos` (via Tailscale/rede da loja) e logar.
   - O garçom precisa das roles do URY (Captain/Cashier) e estar vinculado à branch (já é o caso
     do setup da seed para o Administrator; para garçons reais, cadastrar cada um em `Branch.user`).
3. A tela mobile aparece automaticamente em telas pequenas. Limpar o cache do POS se necessário
   (Ctrl+Shift+R) após atualizar a imagem.

## Observações

- **Um label** ("Orders" no `MobileFooter`) ficou hardcoded em inglês no upstream — cosmético,
  traduzível depois.
- Impressão: usar `qz_print=0` (impressão via navegador) como no desktop — ver `URY_POS_CUSTOMIZACOES.md`.
- Esta é uma boa base para o objetivo maior (storefront próprio / substituir Suitable): o mesmo
  backend e componentes mobile podem ser reaproveitados.
