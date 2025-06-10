# Kubernetes MCP Server

Ein Docker-basierter MCP (Model Context Protocol) Server für Kubernetes-Operationen mit kubectl und Bash-Script-Ausführung.

## Features

- 🐳 Läuft als Docker Container
- ⚡ kubectl vollständig integriert
- 📝 YAML Manifeste ins Filesystem schreiben
- 🖥️ Bash Scripts ausführen
- 🔧 KUBECONFIG als Umgebungsvariable
- ✅ MCP-konforme Responses (OK/Error mit Details)

## Schnellstart

### 1. Repository Setup

```bash
git clone <this-repo>
cd bash-kubectl-droide
```

### 2. Kubeconfig als Base64 bereitstellen

```bash
# Kubeconfig als Base64 encodieren
export KUBECONFIG_B64=$(cat ~/.kube/config | base64 -w 0)

# Oder .env Datei erstellen
echo "KUBECONFIG_B64=$(cat ~/.kube/config | base64 -w 0)" > .env
```

### 3. Container starten

```bash
# Mit Docker Compose
docker-compose up -d

# Oder direkt mit Docker
docker build -t kubectl-mcp-server .
docker run -d -p 8000:8000 \
  -v $(pwd)/manifests:/app/manifests \
  -v $(pwd)/scripts:/app/scripts \
  -v $(pwd)/logs:/app/logs \
  -e KUBECONFIG_B64="$KUBECONFIG_B64" \
  kubectl-mcp-server
```

### 4. Server testen

```bash
# Health Check
curl http://localhost:8000/health

# API Info
curl http://localhost:8000/
```

## MCP API Endpoints

### POST /mcp

Hauptendpoint für MCP-Requests. Unterstützte Methoden:

#### 1. YAML Manifest schreiben
```json
{
  "method": "write_yaml_manifest",
  "params": {
    "yaml": "apiVersion: v1\nkind: Pod\n...",
    "filename": "my-pod.yaml"
  }
}
```

#### 2. kubectl Kommando ausführen
```json
{
  "method": "execute_kubectl",
  "params": {
    "command": ["get", "pods", "-n", "default"]
  }
}
```

#### 3. Bash Script ausführen
```json
{
  "method": "execute_bash_script",
  "params": {
    "script": "#!/bin/bash\necho 'Hello World'\nkubectl get nodes",
    "name": "my_script"
  }
}
```

#### 4. Manifeste auflisten
```json
{
  "method": "list_manifests",
  "params": {}
}
```

## Response Format

Alle Responses folgen dem MCP-Standard:

### Erfolgreiche Response
```json
{
  "success": true,
  "result": {
    "exit_code": 0,
    "stdout": "Output here...",
    "stderr": ""
  }
}
```

### Fehler Response
```json
{
  "success": false,
  "error": "Error description",
  "result": {
    "exit_code": 1,
    "stdout": "",
    "stderr": "Error details..."
  }
}
```

## Beispiele

### Python Client Beispiel

```python
import requests

def send_mcp_request(method, params):
    response = requests.post("http://localhost:8000/mcp", json={
        "method": method,
        "params": params
    })
    return response.json()

# kubectl get pods ausführen
result = send_mcp_request("execute_kubectl", {
    "command": ["get", "pods", "--all-namespaces"]
})

print(result)
```

### Bash Script mit kubectl

```bash
# Script Content
SCRIPT='#!/bin/bash
echo "=== Cluster Info ==="
kubectl cluster-info

echo "=== Nodes ==="
kubectl get nodes

echo "=== Pods ==="
kubectl get pods --all-namespaces'

# MCP Request senden
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d "{
    \"method\": \"execute_bash_script\",
    \"params\": {
      \"script\": \"$SCRIPT\",
      \"name\": \"cluster_info\"
    }
  }"
```

## Verzeichnisstruktur

```
bash-kubectl-droide/
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
├── requirements.txt
├── .env.example         # Beispiel für KUBECONFIG_B64
├── src/
│   └── mcp_server.py
├── examples/
│   ├── nginx-deployment.yaml
│   ├── test_script.sh
│   └── test_mcp_requests.py
├── manifests/           # YAML Manifests (gemountet)
├── scripts/             # Bash Scripts (gemountet)
└── logs/               # Log Files (gemountet)
```

## Erweiterte Nutzung

### Eigene Scripts hinzufügen

Scripts im `scripts/` Verzeichnis sind im Container verfügbar:

```bash
# Script erstellen
echo '#!/bin/bash\nkubectl get pods' > scripts/get_pods.sh
chmod +x scripts/get_pods.sh

# Über MCP ausführen
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "execute_bash_script",
    "params": {
      "script": "#!/bin/bash\n./scripts/get_pods.sh",
      "name": "run_get_pods"
    }
  }'
```

### Persistent Volumes

Für persistente Daten kannst du zusätzliche Volumes mounten:

```yaml
volumes:
  - ./data:/app/data
  - ./backups:/app/backups
```

## Troubleshooting

### Container startet nicht
```bash
# Logs prüfen
docker-compose logs kubectl-mcp-server

# Container Status
docker-compose ps
```

### kubectl funktioniert nicht
```bash
# kubeconfig prüfen
docker exec kubectl-mcp-server kubectl config view

# Cluster-Verbindung testen
docker exec kubectl-mcp-server kubectl cluster-info
```

### Base64 kubeconfig Probleme
```bash
# Base64 encoding testen
echo "KUBECONFIG_B64=$(cat ~/.kube/config | base64 -w 0)"

# Container Logs prüfen für kubeconfig Decode-Meldungen
docker logs kubectl-mcp-server

# Direkt im Container testen
docker exec kubectl-mcp-server ls -la /root/.kube/
```

## Development

### Lokale Entwicklung
```bash
# Python Dependencies installieren
pip install -r requirements.txt

# Server lokal starten
cd src
python mcp_server.py
```

### Tests ausführen
```bash
# Test Client ausführen
python examples/test_mcp_requests.py

# Oder mit curl
bash examples/test_script.sh
```

## Kubernetes Training Integration

Perfekt für Kubernetes-Trainings:
- Isolierte Ausführungsumgebung
- Vollzugriff auf kubectl
- Scriptable für Übungen
- MCP-konform für Integration in größere Systeme
- Einfaches Setup mit Docker Compose

## Lizenz

MIT License