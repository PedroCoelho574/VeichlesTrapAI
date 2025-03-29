# ISP Monitor - Sistema de Monitoramento de Veículos

## Estrutura do Projeto

```
isp-monitor/
├── backend/               # Código do servidor
│   ├── api/               # Endpoints da API
│   ├── core/              # Lógica principal
│   ├── models/            # Modelos de banco de dados
│   ├── services/          # Serviços e business logic
│   ├── utils/             # Utilitários e helpers
│   ├── templates/         # Templates HTML (se necessário)
│   └── tests/             # Testes do backend
│
├── frontend/              # Aplicação frontend
│   ├── src/               # Código fonte principal
│   │   ├── assets/        # Imagens, fonts, etc
│   │   ├── components/    # Componentes React/Vue
│   │   ├── styles/        # Arquivos CSS/SCSS
│   │   └── views/         # Páginas/views
│   └── public/            # Arquivos estáticos
│
├── ai_models/             # Modelos de IA
│   ├── detection/         # Detecção de objetos
│   └── recognition/       # Reconhecimento específico
│
├── config/                # Arquivos de configuração
├── scripts/               # Scripts auxiliares
├── docs/                  # Documentação
└── requirements.txt       # Dependências Python
```

## Como Executar

```bash
# Backend
cd isp-monitor/backend
python -m api.app

# Frontend
cd ../frontend
npm install
npm start