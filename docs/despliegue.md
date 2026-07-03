# Guía de Despliegue — Rol 3: DevOps/Docker

## Responsable: Javier Cataldo

---

## 1. Containerización con Docker

### Archivos creados

| Archivo | Descripción |
|---------|-------------|
| `Dockerfile` | Imagen Python 3.11-slim, instala dependencias, copia el proyecto y ejecuta Streamlit en puerto 8501 |
| `docker-compose.yml` | Orquestación del contenedor, mapeo de puertos, volúmenes para datos, variable de entorno desde `.env` |
| `.env.example` | Template de variables de entorno requeridas |
| `dashboards/app.py` | Dashboard interactivo NHANES con 3 vistas (Ejecutiva, Técnica, Operativa) |
| `requirements.txt` | Actualizado con dependencias: streamlit, plotly, pandas, numpy, pyreadstat |

### Estructura del Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "dashboards/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### docker-compose.yml

```yaml
services:
  dashboard:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    env_file:
      - .env
    restart: unless-stopped
```

### Variables de entorno (`.env`)

```
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

---

## 2. Prueba local

```bash
# Crear .env con las variables
echo "STREAMLIT_SERVER_PORT=8501" > .env
echo "STREAMLIT_SERVER_ADDRESS=0.0.0.0" >> .env

# Construir y levantar
docker compose up --build

# Abrir en navegador
http://localhost:8501
```

---

## 3. Despliegue en AWS EC2

### 3.1 Crear instancia EC2

1. Ir a AWS Console → EC2 → Launch Instance
2. AMI: Ubuntu 22.04 o 26.04 LTS (gratuita)
3. Tipo: t2.micro o t3.micro (capa gratuita)
4. Par de claves: crear nuevo `.pem` y descargarlo
5. Grupo de seguridad: abrir puertos **22 (SSH)** y **8501 (Streamlit)**
6. Lanzar instancia

### 3.2 Conectarse por SSH

```bash
ssh -i tu-clave.pem ubuntu@<IP-publica>
```

### 3.3 Instalar Docker y Git

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
```

### 3.4 Clonar repositorio

```bash
git clone https://github.com/benjaaam0/evaluacion3-datos-nhanes.git
cd evaluacion3-datos-nhanes
git checkout javier
```

### 3.5 Copiar archivos de datos

Los archivos `.xpt` (DEMO_J.xpt, BPX_J.xpt, BMX_J.xpt) deben copiarse a `data/01_raw/`:

```bash
# Desde la máquina local:
scp -i tu-clave.pem data/01_raw/*.xpt ubuntu@<IP-publica>:~/evaluacion3-datos-nhanes/data/01_raw/
```

### 3.6 Crear .env y levantar

```bash
echo "STREAMLIT_SERVER_PORT=8501" > .env
echo "STREAMLIT_SERVER_ADDRESS=0.0.0.0" >> .env
sudo docker compose up --build -d
```

### 3.7 Verificar

```
http://<IP-publica>:8501
```

---

## 4. Detalles técnicos

- **Puerto**: 8501 (Streamlit)
- **Base de datos**: SQLite (generada por Kedro pipeline)
- **Fuentes de datos**: 3 archivos XPT de NHANES (DEMO_J, BPX_J, BMX_J)
- **Dashboard**: Streamlit con Plotly, 3 vistas diferenciadas por audiencia
- **Pipeline ETL**: Kedro (Rol 1 de Cristóbal/Benjamín)

---

## 5. AWS Academy Learner Lab

- Presupuesto: 50 USD
- Duración de sesión: 4 horas (extensible)
- La EC2 se apaga al terminar la sesión pero los recursos se guardan
- Reactivar: volver a Learner Lab → Start Lab

---

## 6. Commits realizados

```
Configuración Docker y dashboard para despliegue AWS
```
