# Deploy CEMAPE — cemape.sistema9.com.br

## Pré-requisitos no servidor
- Python 3.10+, pip, venv
- PostgreSQL rodando
- Nginx instalado
- Certbot instalado

---

## 1. Verificar porta disponível

```bash
sudo ss -tlnp | grep -E '800[0-9]'
```
Se 8001 estiver livre, prossiga. Caso contrário, edite `cemape.service`
e `cemape.nginx` trocando 8001 pela porta livre.

---

## 2. Criar a pasta e enviar os arquivos

```bash
sudo mkdir -p /var/www/cemape
sudo chown $USER:www-data /var/www/cemape
sudo chmod 2775 /var/www/cemape
```

Envie o código (git clone ou rsync):
```bash
# Opção A — git
cd /var/www/cemape
git clone <seu-repo> .

# Opção B — rsync (do seu PC Windows via WSL ou Git Bash)
rsync -avz --exclude '.env' --exclude '__pycache__' \
    /e/cemape/ usuario@servidor:/var/www/cemape/
```

---

## 3. Ambiente virtual e dependências

```bash
cd /var/www/cemape
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install gunicorn psycopg2-binary
pip install -r requirements.txt
```

---

## 4. Configurar variáveis de ambiente

```bash
cp deploy/env.producao /var/www/cemape/.env
nano /var/www/cemape/.env   # preencher SECRET_KEY, DB_PASSWORD
```

Gerar SECRET_KEY:
```bash
source .venv/bin/activate
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 5. Banco de dados PostgreSQL

```bash
sudo -u postgres psql
```
```sql
CREATE DATABASE cemape_prod;
CREATE USER cemape WITH PASSWORD 'MESMA_SENHA_DO_ENV';
GRANT ALL PRIVILEGES ON DATABASE cemape_prod TO cemape;
\q
```

---

## 6. Django — migrations e static

```bash
cd /var/www/cemape
source .venv/bin/activate

python manage.py migrate
python manage.py seed_calculadora        # popula tabelas de custas
python manage.py createsuperuser
python manage.py collectstatic --no-input

# Criar pasta de logs
sudo mkdir -p /var/log/cemape
sudo chown www-data:www-data /var/log/cemape
```

---

## 7. Build do CSS (Tailwind)

No seu PC local, gere o CSS minificado e inclua no deploy:
```bash
npm run build   # gera static/css/output.css
```
Ou no servidor se tiver Node:
```bash
npm ci && npm run build
```

---

## 8. Instalar o serviço systemd

```bash
sudo cp deploy/cemape.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cemape
sudo systemctl start cemape
sudo systemctl status cemape   # deve mostrar "active (running)"
```

---

## 9. Configurar Nginx

```bash
sudo cp deploy/cemape.nginx /etc/nginx/sites-available/cemape
sudo ln -s /etc/nginx/sites-available/cemape /etc/nginx/sites-enabled/
sudo nginx -t          # testar sintaxe
sudo systemctl reload nginx
```

---

## 10. Certificado SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d cemape.sistema9.com.br
```
O Certbot edita o nginx automaticamente para adicionar os caminhos do certificado.

---

## Comandos úteis após deploy

```bash
# Reiniciar após atualizar código
sudo systemctl restart cemape

# Ver logs em tempo real
sudo journalctl -u cemape -f
sudo tail -f /var/log/cemape/error.log

# Atualizar (novo deploy)
cd /var/www/cemape
git pull
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
sudo systemctl restart cemape
```
