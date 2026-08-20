# 🍗 Super Agente de Selección y Reclutamiento con LangGraph (Chicken Fill)

Este proyecto implementa un **Agente Autónomo Multi-Etapa con LangGraph** para la evaluación con criterio humano de candidatos provenientes de la API de Workstream.

---

## 🌟 ¿Qué hace este Agente?

A diferencia de un script rígido o un webhook tradicional, este sistema utiliza un **Grafo de Estados (StateGraph)** con auto-reflexión:

1. **Ingesta y Enriquecimiento Dinámico**: Consulta la postulación en Workstream y analiza la viabilidad logística (distancia en millas y tiempos de traslado hacia el local).
2. **Evaluación Multidimensional de RRHH**: Analiza actitud, servicio al cliente ("My Pleasure"), disponibilidad horaria y evalúa el valor en candidatos junior con alta proactividad frente a perfiles experimentados.
3. **Nodo Crítico y Auto-Reflexión**: Revisa que la evaluación no sea sesgada, injusta o arbitraria.
4. **Síntesis Ejecutiva y Plan de Entrevista**: Genera un reporte cualitativo y redacta **preguntas personalizadas** para que el reclutador humano las utilice en la llamada telefónica.

---

## 📁 Estructura del Código

```text
e:/AGENTE DE IA PARA CHICKEN FILL/
│
├── requirements.txt            # Dependencias instaladas en el entorno virtual
├── .env.example                # Plantilla de variables de entorno (OpenAI, Maps, Workstream)
├── main.py                     # Ejecutable con interfaz enriquecida en consola
│
└── src/
    ├── config.py               # Configuración de constantes y APIs
    ├── state.py                # Estado tipado del Grafo (AgentState con Pydantic)
    ├── graph.py                # Definición del flujo y compilación de LangGraph
    │
    ├── tools/                  # Herramientas del Agente
    │   ├── workstream_api.py   # Conexión con Workstream API y casos simulados
    │   └── maps_commute.py     # Cálculo de distancias con Google Maps API
    │
    └── nodes/                  # Nodos especialistas del Grafo
        ├── fetch_node.py       # Ingestión y lectura de preguntas dinámicas
        ├── analyst_node.py     # Análisis cualitativo y cuantitativo
        ├── critic_node.py      # Reflexión y balance de juicio
        └── synthesizer_node.py # Generación de informe y preguntas de llamada
```

---

## 🚀 Cómo ejecutarlo

Abre la terminal en la carpeta del proyecto y ejecuta:

```powershell
# Probar el candidato 1 (Alta proactividad)
.venv\Scripts\python main.py 1

# Probar el candidato 2 (Cocina / experiencia con traslado)
.venv\Scripts\python main.py 2

# Probar el candidato 3 (Baja motivación / red flags)
.venv\Scripts\python main.py 3

# Probar todos los perfiles en lote
.venv\Scripts\python main.py 4
```

---

## 🔑 Conectar tus API Keys Reales

Crea un archivo `.env` en la raíz (puedes copiar de `.env.example`) y agrega tus claves:

```env
OPENAI_API_KEY="sk-tu-api-key"
WORKSTREAM_API_KEY="tu-workstream-key"
GOOGLE_MAPS_API_KEY="tu-google-maps-key"
STORE_ADDRESS="Stafford, TX 77477"
```
