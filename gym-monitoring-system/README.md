# Sistema de Monitoramento de Academia - Previsão de Churn

Sistema completo para monitorar frequência de alunos em academia e prever possíveis desistências usando Machine Learning.

## 🚀 Funcionalidades

- **API REST** completa com FastAPI
- **Banco de dados PostgreSQL** com relacionamentos
- **Sistema de filas** com RabbitMQ e Celery
- **Modelo de ML** para previsão de churn
- **Cache Redis** para performance
- **Autenticação JWT**
- **Documentação automática** com Swagger
- **Containerização** com Docker
- **Testes unitários**

## 📋 Requisitos

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- RabbitMQ 3+
- Docker e Docker Compose (opcional)

## 🛠️ Instalação e Configuração

### Opção 1: Com Docker (Recomendado)

```bash
# 1. Clonar o repositório
git clone <seu-repositorio>
cd gym-monitoring-system

# 2. Copiar arquivo de ambiente
cp .env.example .env

# 3. Iniciar todos os serviços
docker-compose up -d

# 4. Inicializar banco com dados de exemplo
docker-compose exec web python scripts/init_db.py
```

### Opção 2: Instalação Manual

```bash
# 1. Clonar o repositório
git clone <seu-repositorio>
cd gym-monitoring-system

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# 5. Inicializar banco de dados
python scripts/init_db.py

# 6. Iniciar serviços

# Terminal 1 - API
uvicorn app.main:app --reload

# Terminal 2 - Worker Celery
celery -A app.workers.tasks worker --loglevel=info

# Terminal 3 - Beat Celery (tarefas agendadas)
celery -A app.workers.tasks beat --loglevel=info
```

## 📚 Documentação da API

Após iniciar o sistema, acesse:

- **Documentação Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 Endpoints Principais

### Autenticação
```http
POST /login
```

### Gestão de Alunos
```http
POST /aluno/registro           # Registrar novo aluno
POST /aluno/checkin           # Registrar entrada
GET  /aluno/{id}/frequencia   # Histórico de frequência
GET  /aluno/{id}/risco-churn  # Probabilidade de churn
```

### Relatórios (Requer Autenticação)
```http
GET /alunos                   # Listar alunos
GET /relatorio/frequencia     # Relatório de frequência
```

## 🤖 Modelo de Machine Learning

O sistema inclui um modelo de Random Forest para prever churn baseado em:

- **Frequência semanal** de visitas
- **Tempo desde último checkin**
- **Duração média** das sessões
- **Tipo de plano** contratado
- **Tempo como aluno**

### Treinamento do Modelo

Execute o notebook Jupyter para ver o processo completo:

```bash
jupyter notebook notebooks/churn_model_training.ipynb
```

## 🔄 Sistema de Filas

O sistema usa Celery para processamento assíncrono:

### Tarefas Disponíveis

- **Processamento de checkins em lote**
- **Geração de relatórios diários**
- **Identificação de alunos em risco**
- **Atualização do modelo de ML**

### Monitoramento

- **Flower** (monitor Celery): http://localhost:5555
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Executar com coverage
pytest --cov=app

# Executar testes específicos
pytest tests/test_api.py
pytest tests/test_models.py
pytest tests/test_services.py
```

## 📊 Monitoramento e Métricas

### Redis Cache
- Frequência de alunos: cache de 15 minutos
- Previsões de churn: cache de 1 hora

### Logs
- API: logs estruturados com FastAPI
- Workers: logs detalhados do Celery
- ML: métricas de performance do modelo

## 🔧 Configurações Avançadas

### Variáveis de Ambiente

```env
# Banco de Dados
DATABASE_URL=postgresql://user:password@localhost:5432/gym_db

# Redis
REDIS_URL=redis://localhost:6379

# RabbitMQ
RABBITMQ_URL=pyamqp://guest@localhost//

# JWT
SECRET_KEY=sua-chave-secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Performance

- **Connection pooling** no PostgreSQL
- **Cache estratégico** com Redis
- **Processamento assíncrono** com Celery
- **Índices otimizados** no banco

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   PostgreSQL    │    │   Redis Cache   │
│   (API REST)    │◄──►│   (Dados)       │    │   (Performance) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RabbitMQ      │    │   Celery        │    │   ML Model      │
│   (Filas)       │◄──►│   (Workers)     │◄──►│   (Predições)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Estrutura do Projeto

```
gym-monitoring-system/
├── app/
│   ├── api/                 # Endpoints e schemas
│   ├── models/              # Modelos do banco
│   ├── services/            # Lógica de negócio
│   ├── ml/                  # Machine Learning
│   └── workers/               # Sistema de filas
├── notebooks/               # Jupyter notebooks
├── scripts/                 # Scripts utilitários
├── tests/                   # Testes automatizados
├── docker-compose.yml       # Orquestração Docker
├── Dockerfile              # Imagem da aplicação
├── requirements.txt        # Dependências Python
└── README.md              # Esta documentação
```

## 🚀 Deploy em Produção

### Considerações Importantes

1. **Segurança**
   - Alterar credenciais padrão
   - Configurar HTTPS
   - Implementar rate limiting
   - Validar tokens JWT adequadamente

2. **Performance**
   - Configurar connection pooling
   - Otimizar queries do banco
   - Monitorar uso de recursos
   - Implementar balanceamento de carga

3. **Monitoramento**
   - Logs centralizados
   - Métricas de negócio
   - Alertas automáticos
   - Health checks

### Docker em Produção

```bash
# Build da imagem
docker build -t gym-monitoring:latest .

# Deploy com docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👥 Equipe

- **Desenvolvedor**: [Seu Nome]
- **Email**: [seu-email@email.com]
- **GitHub**: [seu-usuario]

## 🆘 Suporte

Para dúvidas ou problemas:

1. Verifique a documentação
2. Consulte os logs da aplicação
3. Abra uma issue no GitHub
4. Entre em contato por email

---

**🎯 Objetivo**: Demonstrar habilidades em desenvolvimento full-stack com foco em IA/ML para aplicações práticas de negócio.

**⚡ Status**: Pronto para produção com as devidas configurações de segurança e monitoramento.