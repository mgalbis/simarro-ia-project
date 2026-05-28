# QABOT - Plataforma Inteligente de Quality Assessment para Datasets y Modelos ML

## Descripción del proyecto

QABOT es un agente conversacional 
especializado en la verificación de calidad de artefactos generados durante el 
ciclo de vida de un proyecto de Inteligencia Artificial y Big Data.

La aplicación combina:

- una API backend desarrollada con FastAPI  
- un frontend interactivo en React  
- un motor de reglas de calidad de datos y evaluación de modelos  
- soporte para análisis documental conceptual  
- persistencia mediante base de datos ligera (SQLite)  
- sistema integrado de autenticación y seguridad de usuarios  

El sistema permite ejecutar validaciones automáticas sobre datasets, métricas de modelos y particiones train/validation/test, simulando flujos de trabajo reales de MLOps y Data Quality.

---

## Objetivo del proyecto

El objetivo principal es facilitar la evaluación automática de calidad de datos y modelos mediante una interfaz capaz de:

- interpretar solicitudes del usuario  
- inferir tipos de validación  
- ejecutar reglas QA automáticamente  
- generar informes de resultados  
- gestionar ciclos de pruebas persistentes  

El proyecto está orientado a entornos demostrativos relacionados con Data Quality, Testing y MLOps.

---

## Funcionalidades principales

### Autenticación y seguridad
- registro de usuarios  
- login seguro  
- almacenamiento de contraseñas 
- protección de rutas  
- control de sesiones  

---

### Validaciones soportadas

#### Validación de tablas
- detección de nulos  
- detección de duplicados  
- detección de outliers  
- consistencia de tipos  
- balanceo de clases  
- validación de asimetría

#### Validación de particiones
- validación train / validation / test  
- detección de fuga de IDs  
- estabilidad del target  
- distribución de splits  

#### Evaluación de modelos
- accuracy  
- precision  
- recall  
- F1  
- ROC AUC  

#### Scores y umbrales
- análisis de thresholds  
- calidad de clasificación  
- análisis de scores  

---

## Arquitectura general

### Backend (FastAPI)

Responsable de:

- procesamiento de peticiones  
- autenticación de usuarios  
- análisis de datasets  
- ejecución de reglas QA  
- persistencia de sesiones en SQLite  
- análisis documental  
- generación de reportes  

---

### Frontend (React + Vite)

Responsable de:

- interfaz conversacional  
- gestión de ciclos QA  
- subida de datasets  
- visualización de métricas  
- historial de ejecuciones  

---

## Comunicación entre componentes

Arquitectura cliente-servidor:

1. El usuario interactúa con el frontend  
2. El frontend envía peticiones HTTP al backend  
3. FastAPI procesa datasets y reglas QA  
4. Se generan resultados y reportes  
5. El frontend muestra métricas e historial  

### Comunicación utilizada
- API REST (HTTP)  
- JSON para intercambio de datos  
- multipart/form-data para subida de archivos  

---

## Stack tecnológico

| Capa | Tecnología |
|------|------------|
| Frontend | React + Vite + TailwindCSS |
| Backend | FastAPI |
| QA Engine | Python + Pandas |
| Machine Learning | Scikit-learn |
| Persistencia | SQLite |
| Contenedores | Docker / Docker Compose |

---

## Estructura del proyecto

```
QABOT/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── data/
│   ├── requirements.txt
│   └── venv/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── App.jsx
│   │   ├── AppRouter.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
│
├── docs/
│   ├── arquitectura.md
│   └── runbook.md
│
└── README.md
```

---

## Instalación y ejecución

### Requisitos previos

- Python 3.11 o superior  
- Node.js 18 o superior  
- npm  
- Docker (opcional)  
- Puerto 8000 libre  

---

## Backend

```bash
cd backend
python -m venv venv
```

Activar entorno virtual:

Linux / Mac:
```bash
source venv/bin/activate
```

Windows:
```bash
venv\Scripts\activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar backend:

```bash
uvicorn app.main:app --reload
```

Acceso:
- http://localhost:8000  
- http://localhost:8000/docs  

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Acceso:
- http://localhost:5173  

---

## Docker

Desde la raíz del proyecto:

```bash
docker compose up --build
```

Incluye:
- backend FastAPI  
- frontend React/Vite  

---

## Endpoints principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| /auth/login | POST | Login |
| /auth/register | POST | Registro |
| /chat | POST | Ejecuta validaciones QA |
| /sessions | GET/POST | Gestión de sesiones |
| /sessions/{id} | GET | Obtener sesión |
| /sessions/metadata | PUT | Actualizar metadatos |
| /download/{execution_id} | GET | Descargar informe PDF |
| /conceptual-documents/analyze | POST | Análisis documental |
| /sessions/{id}/reports/{exec_id} | DELETE | Eliminar iteración específica |

---

## Flujo de uso

1. Registro / login  
2. Crear sesión QA  
3. Subir dataset  
4. Ejecutar validaciones  
5. Revisar métricas  
6. Iterar resultados  
7. Descargar reportes  

---

## Gestión de sesiones

Cada usuario dispone de:

- sesiones persistentes  
- historial de ejecuciones  
- restauración de sesiones  
- metadatos del proyecto  

Persistencia mediante SQLite.

---

## Funcionalidad documental conceptual

Permite analizar documentos:

- .docx  
- .md  
- .txt  
- .ipynb  

Para:

- inferir reglas de negocio  
- detectar datasets implícitos  
- sugerir validaciones QA  
- mapear estructura de datos  