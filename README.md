# Service Desk DP

Sistema completo de Help Desk especializado para Departamento Pessoal.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Django 5 + DRF |
| Banco / Auth / Storage | Supabase (PostgreSQL) |
| Tempo real | Django Channels + Redis |
| Filas | Celery + Redis |
| Frontend | Django Templates + Bootstrap 5 |
| Container | Docker / docker-compose |

---

## Estrutura do Projeto

```
Ticket/
├── backend/
│   ├── config/           # Settings, URLs, ASGI, Celery
│   ├── core/             # Models base, mixins, permissões, middleware
│   ├── apps/
│   │   ├── accounts/     # Usuários (Admin, Analista, Cliente)
│   │   ├── companies/    # Empresas multitenancy
│   │   ├── tickets/      # Tickets, Categorias, Mensagens, Signals
│   │   ├── attachments/  # Anexos (Supabase Storage)
│   │   ├── sla/          # Controle de prazo SLA
│   │   ├── notifications/# Notificações + WebSocket Consumer
│   │   ├── knowledge_base# Base de conhecimento
│   │   └── audit/        # Log de auditoria
│   └── api/              # DRF Serializers + ViewSets + Router
├── frontend/
│   ├── templates/
│   │   ├── base/         # layout.html, login.html, profile.html
│   │   ├── client/       # Portal do cliente
│   │   ├── admin/        # Painel interno DP
│   │   └── knowledge_base/
│   └── static/css+js/
├── workers/              # Celery tasks
└── infrastructure/       # docker-compose.yml
```

---

## Configuração Rápida

### 1. Clone e configure o ambiente

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 2. Configure variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas credenciais Supabase
```

### 3. Migrações e dados iniciais

```bash
python manage.py migrate
python manage.py seed_data        # Cria categorias DP + admin padrão
python manage.py collectstatic
```

### 4. Rode o servidor

```bash
# Desenvolvimento (sem WebSocket)
python manage.py runserver

# Com WebSocket (produção)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### 5. Celery (opcional para SLA e notificações)

```bash
# Terminal 1 — Worker
celery -A config.celery worker --loglevel=info

# Terminal 2 — Beat (agendador)
celery -A config.celery beat --loglevel=info
```

### 6. Docker completo

```bash
cd infrastructure
docker-compose up --build
```

---

## Acesso Inicial

| URL | Descrição |
|---|---|
| `/auth/login/` | Login do sistema |
| `/` | Dashboard (redireciona por role) |
| `/tickets/` | Lista de tickets |
| `/kanban/` | Quadro Kanban (analistas) |
| `/knowledge/` | Base de conhecimento |
| `/django-admin/` | Admin Django |
| `/api/` | DRF API Browser |

**Usuário padrão:** `admin` / `admin123` _(troque imediatamente!)_

---

## API REST

### Autenticação

```http
POST /api/auth/login/
{
  "username": "user",
  "password": "pass"
}
# Retorna: { "token": "...", "role": "...", ... }
```

### Endpoints principais

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/tickets/` | Lista tickets |
| POST | `/api/tickets/` | Criar ticket |
| GET | `/api/tickets/{id}/` | Detalhe ticket |
| POST | `/api/tickets/{id}/reply/` | Responder |
| PATCH | `/api/tickets/{id}/assign/` | Atribuir analista |
| PATCH | `/api/tickets/{id}/change_status/` | Mudar status |
| GET | `/api/tickets/metrics/` | Dashboard métricas |
| GET | `/api/categories/` | Categorias DP |
| GET | `/api/companies/` | Empresas |
| GET | `/api/notifications/` | Notificações |
| POST | `/api/notifications/mark_all_read/` | Marcar lidas |
| GET | `/api/knowledge/` | Artigos |

---

## Tipos de Usuário

| Role | Acesso |
|---|---|
| `admin` | Tudo — configurações, empresas, usuários |
| `analyst` | Tickets, SLA, base de conhecimento |
| `client` | Apenas tickets da sua empresa |

---

## Categorias DP (pré-configuradas)

- Admissão (resposta automática com checklist de docs)
- Demissão
- Folha de Pagamento
- Benefícios
- FGTS / INSS
- eSocial
- Férias (resposta automática)
- Afastamentos
- Dúvidas Gerais

---

## Recursos

- **Multiempresa (SaaS-ready):** cada empresa vê apenas seus tickets
- **SLA automático:** criado ao abrir ticket, alertas via Celery
- **Respostas automáticas:** por categoria
- **Notas internas:** visíveis apenas para analistas
- **Upload para Supabase Storage:** com fallback local
- **WebSocket:** notificações em tempo real
- **Auditoria:** log de todas as ações
- **Kanban:** visão de quadro para analistas
- **Base de conhecimento:** artigos para reduzir chamados
