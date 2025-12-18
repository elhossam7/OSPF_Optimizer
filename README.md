# OSPF Optimizer - Ajustement Dynamique des Couts OSPF

## Description

Ce projet permet d'optimiser automatiquement les couts OSPF dans un reseau **FRRouting** en fonction des metriques en temps reel:
- **Utilisation de la bande passante**
- **Latence**
- **Perte de paquets**

## Environnement

| Composant | Technologie |
|-----------|-------------|
| Routeurs | **FRRouting (FRR)** - Conteneurs Docker |
| PCs | **Alpine Linux** - Conteneurs Docker |
| Simulateur | **GNS3** |
| Connexion | docker exec (pas de SSH necessaire) |

## Installation

```bash
cd ~/OSPF_Optimizer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🚀 Démarrage Automatique (Recommandé)

Le script `auto_start.py` détecte automatiquement les conteneurs GNS3 et met à jour la configuration:

```bash
# Démarrage standard avec dashboard web
python3 auto_start.py --web

# Mode test (dry-run) avec détails
python3 auto_start.py --dry-run --verbose

# Détection des conteneurs uniquement (sans démarrer)
python3 auto_start.py --detect-only

# Script shell alternatif (Linux)
chmod +x auto_start.sh
./auto_start.sh --web --port 8080
```

### Options auto_start.py

| Option | Description |
|--------|-------------|
| `--web` | Active le dashboard web |
| `--port 8080` | Port du serveur web (défaut: 8080) |
| `--dry-run` | Affiche les changements sans les appliquer |
| `--verbose` | Mode détaillé |
| `--detect-only` | Détecte les conteneurs sans démarrer |
| `--no-update` | Utilise la config existante sans mise à jour |
| `--simulation` | Mode simulation (données simulées) |
| `--once` | Exécute un seul cycle puis quitte |

## Utilisation Manuelle

### Mode Simulation
```bash
python3 ospf_optimizer.py --simulation --once
```

### Mode Production
```bash
python3 ospf_optimizer.py --once
```

### Dashboard Web
```bash
python3 ospf_optimizer.py --config config/routers.yaml --web --port 8080
```

## Commandes FRRouting

```bash
docker exec R1 vtysh -c "show ip ospf neighbor"
docker exec R1 vtysh -c "show ip ospf interface"
docker exec R1 vtysh -c "show ip route ospf"
```
