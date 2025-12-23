# Présentation : Implémentation Pratique de l'OSPF Optimizer
## Ajustement Dynamique des Coûts OSPF en Temps Réel

---

# Slide 1 : Introduction au Projet

## Objectif Principal
**Optimiser automatiquement les coûts OSPF** en fonction des conditions réseau en temps réel

### Métriques surveillées :
- **Utilisation de la bande passante** (%)
- **Latence** (ms)
- **Perte de paquets** (%)

### Problème résolu :
> Les coûts OSPF traditionnels sont **statiques** alors que le trafic réseau est **dynamique**

---

# Slide 2 : Architecture Globale

```
┌─────────────────────────────────────────────────────────────────┐
│                        OSPF OPTIMIZER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │   Collecteur │    │  Calculateur │    │   Interface  │     │
│   │  de Métriques│---->│   de Coûts   │---->│     Web      │     │
│   └──────────────┘    └──────────────┘    └──────────────┘     │
│          │                   │                                   │
│          ▼                   ▼                                   │
│   ┌──────────────────────────────────────────┐                  │
│   │         Router Connection Module          │                  │
│   │            (Docker exec / SSH)            │                  │
│   └──────────────────────────────────────────┘                  │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
       ┌────────┐    ┌────────┐    ┌────────┐
       │  ABR1  │    │  ABR2  │    │  ABR3  │
       │  (FRR) │    │  (FRR) │    │  (FRR) │
       └────────┘    └────────┘    └────────┘
            │              │              │
       ┌────┴────┐    ┌────┴────┐         │
       ▼         ▼    ▼         ▼         │
    ┌────┐   ┌────┐  ┌────┐   ┌────┐      │
    │ R1 │   │ R2 │  │ R3 │   │ R4 │      │
    └────┘   └────┘  └────┘   └────┘      │
       │        │       │        │         │
       ▼        ▼       ▼        ▼         │
    [PC1]    [PC2]   [PC3]    [PC4]        │
                                           │
    Zone 1 ←────────→ Zone 0 ←────────→ Zone 2
```

---

# Slide 3 : Stack Technologique

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| **Routeurs** | FRRouting (FRR) | Routage OSPF |
| **Virtualisation** | Docker + GNS3 | Simulation réseau |
| **Orchestrateur** | Python 3.x | Logique d'optimisation |
| **Interface Web** | Flask | Dashboard monitoring |
| **Configuration** | YAML | Paramétrage flexible |
| **Connexion** | Docker exec | Commandes aux conteneurs |

---

# Slide 4 : Structure du Projet

```
OSPF_Optimizer/
│
├── ospf_optimizer.py          # Script principal d'orchestration
├── auto_start.py              # Démarrage automatique avec détection
│
├── src/                       # Modules sources
│   ├── router_connection.py   # Connexion aux routeurs (Docker/SSH)
│   ├── metrics_collector.py   # Collecte des métriques réseau
│   ├── cost_calculator.py     # Algorithmes de calcul des coûts
│   └── web_interface.py       # API REST + Dashboard
│
├── config/
│   └── routers.yaml          # Configuration des routeurs
│
├── docs/                      # Documentation
└── scripts/                   # Scripts utilitaires
```

---

# Slide 5 : Module de Connexion (`router_connection.py`)

## Fonctionnalités principales :

### 1. Connexion Docker Exec (Recommandé)
```python
def _docker_exec(self, router_name: str, command: str) -> str:
    """Exécute une commande dans un conteneur Docker"""
    container = self.routers[router_name].container_name
    result = subprocess.run(
        ['docker', 'exec', container, 'sh', '-c', command],
        capture_output=True, text=True
    )
    return result.stdout
```

### 2. Commandes vtysh pour FRRouting
```python
def get_ospf_cost(self, router_name: str, interface: str) -> int:
    """Récupère le coût OSPF actuel d'une interface"""
    output = self.vtysh_command(router_name, f"show ip ospf interface {interface}")
    # Parse: "Cost: 10"
    return extracted_cost

def set_ospf_cost(self, router_name: str, interface: str, cost: int):
    """Modifie le coût OSPF d'une interface"""
    self.vtysh_command(router_name, f"""
        configure terminal
        interface {interface}
        ip ospf cost {cost}
        exit
    """)
```

---

# Slide 6 : Collecteur de Métriques (`metrics_collector.py`)

## Données collectées :

### Structure de données :
```python
@dataclass
class LinkMetrics:
    link_name: str              # Ex: "ABR1-ABR2"
    source_router: str          # Ex: "ABR1"
    dest_router: str            # Ex: "ABR2"
    latency_ms: float           # Latence mesurée
    packet_loss_percent: float  # Taux de perte
    bandwidth_utilization: float # % utilisation
    current_ospf_cost: int      # Coût actuel
    recommended_cost: int       # Coût recommandé
```

### Méthodes de collecte :

| Métrique | Commande | Source |
|----------|----------|--------|
| Latence | `ping -c 5 <dest>` | RTT moyen |
| Perte paquets | `ping -c 10 <dest>` | % paquets perdus |
| Bande passante | `/proc/net/dev` | Statistiques I/O |
| État interface | `ip link show` | UP/DOWN |

---

# 🧮 Slide 7 : Calculateur de Coûts (`cost_calculator.py`)

## Stratégies d'optimisation disponibles :

```python
class OptimizationStrategy(Enum):
    BANDWIDTH_BASED = "bandwidth"    # Basé sur la bande passante
    LATENCY_BASED = "latency"        # Basé sur la latence
    COMPOSITE = "composite"          # Combinaison pondérée
    LOAD_BALANCED = "load_balanced"  # Équilibrage de charge
    MINIMAL_DELAY = "minimal_delay"  # Minimiser le délai
```

## Formule de calcul composite :

```
Coût = Base_Cost × (1 + BW_Factor × BW_Weight 
                     + Latency_Factor × Latency_Weight 
                     + Loss_Factor × Loss_Weight)
```

### Exemple de configuration :
```yaml
cost_factors:
  base_cost: 15
  multipliers:
    bandwidth_weight: 0.0    # Désactivé
    latency_weight: 1.0      # 100% latence
    packet_loss_weight: 0.0  # Désactivé
```

---

# Slide 8 : Seuils de Déclenchement

## Configuration des seuils (`routers.yaml`) :

```yaml
thresholds:
  latency:
    high: 50       # Alerte si > 50ms
    recovery: 30   # Retour normal si < 30ms
    
  packet_loss:
    high: 5        # Alerte si > 5%
    
  bandwidth:
    high: 80       # Alerte si > 80% utilisation
```

## Niveaux d'alerte :

| Niveau | Latence (ms) | Bande Passante (%) | Perte (%) |
|--------|--------------|-------------------|-----------|
| Normal | < 10 | < 30 | < 0.1 |
| Medium | 10-50 | 30-60 | 0.1-1 |
| High | 50-100 | 60-80 | 1-5 |
| Critical | > 100 | > 80 | > 5 |

---

# Slide 9 : Interface Web (`web_interface.py`)

## Dashboard en temps réel :

### Fonctionnalités :
- Visualisation de l'état des routeurs
- Métriques en temps réel par lien
- Historique des optimisations
- Contrôle Start/Stop
- Mode simulation

### API REST disponible :

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/status` | GET | État de l'optimiseur |
| `/api/metrics` | GET | Métriques actuelles |
| `/api/routers` | GET | Liste des routeurs |
| `/api/history` | GET | Historique des changements |
| `/api/start` | POST | Démarrer l'optimisation |
| `/api/stop` | POST | Arrêter l'optimisation |
| `/api/optimize` | POST | Forcer une optimisation |

---

# Slide 10 : Configuration des Routeurs

## Fichier `config/routers.yaml` :

```yaml
routers:
  ABR1:
    container_name: "GNS3.ABR1.367ce91c-77c4-..."
    router_id: 1.1.1.1
    interfaces:
      - name: eth1
        ip: 10.0.0.1
        area: 0        # Backbone
      - name: eth0
        ip: 10.1.1.1
        area: 1        # Zone 1
        
  R1:
    container_name: "GNS3.R1.367ce91c-77c4-..."
    router_id: 1.1.1.11
    interfaces:
      - name: eth1
        ip: 10.1.1.2
        area: 1
```

## Topologie OSPF multi-zones :
- **Zone 0** (Backbone) : ABR1 ↔ ABR2 ↔ ABR3
- **Zone 1** : ABR1 → R1, R2 → PC1, PC2
- **Zone 2** : ABR2 → R3, R4 → PC3, PC4

---

# Slide 11 : Démarrage Automatique (`auto_start.py`)

## Fonctionnalités :

### 1. Détection automatique des conteneurs
```python
def get_docker_containers():
    """Détecte les conteneurs FRR en cours d'exécution"""
    result = subprocess.run(
        ['docker', 'ps', '--format', '{{.Names}}\t{{.Image}}'],
        capture_output=True, text=True
    )
    # Filtre: 'frr' dans le nom d'image
    # Match: GNS3.ABR1.uuid, GNS3.R1.uuid, etc.
```

### 2. Mise à jour automatique de la config
```python
def update_routers_yaml(config_path, containers):
    """Met à jour container_name dans routers.yaml"""
```

## Options de lancement :

```bash
# Mode standard avec dashboard web
python auto_start.py --web --port 8080

# Mode test (sans modifications)
python auto_start.py --dry-run --verbose

# Détection uniquement
python auto_start.py --detect-only
```

---

# Slide 12 : Cycle d'Optimisation

```
┌─────────────────────────────────────────────────────────┐
│                    CYCLE D'OPTIMISATION                  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │   1. COLLECTE DES MÉTRIQUES  │
            │   • Ping pour latence/perte  │
            │   • /proc/net/dev pour BW    │
            │   • vtysh pour coût actuel   │
            └──────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │   2. ANALYSE DES SEUILS      │
            │   • Comparer aux thresholds  │
            │   • Détecter les anomalies   │
            └──────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │   3. CALCUL DU NOUVEAU COÛT  │
            │   • Appliquer la stratégie   │
            │   • Vérifier min/max         │
            │   • Anti-oscillation         │
            └──────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │   4. APPLICATION DU COÛT     │
            │   • vtysh configure terminal │
            │   • ip ospf cost <value>     │
            │   • Logging du changement    │
            └──────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │   5. ATTENTE (INTERVALLE)    │
            │   • Défaut: 30 secondes      │
            │   • Configurable             │
            └──────────────────────────────┘
                           │
                           └────────────────┐
                                            │
                                            ▼
                                      [RÉPÉTER]
```

---

# 💻 Slide 13 : Démonstration Pratique

## Étape 1 : Prérequis
```bash
# Vérifier Docker
docker --version

# Vérifier que GNS3 est lancé avec les routeurs FRR
docker ps | grep -E "frr|frrouting"
```

## Étape 2 : Installation
```bash
cd ~/OSPF_Optimizer
python -m venv venv
source venv/bin/activate     # Linux
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

## Étape 3 : Démarrage
```bash
# Avec détection automatique et dashboard
python auto_start.py --web --port 8080
```

## Étape 4 : Accès au Dashboard
```
http://localhost:8080
```

---

# Slide 14 : Commandes de Vérification FRRouting

## Vérifier l'état OSPF :

```bash
# Voir les voisins OSPF
docker exec R1 vtysh -c "show ip ospf neighbor"

# Afficher les interfaces OSPF
docker exec R1 vtysh -c "show ip ospf interface"

# Table de routage OSPF
docker exec R1 vtysh -c "show ip route ospf"

# Base de données OSPF
docker exec R1 vtysh -c "show ip ospf database"
```

## Modifier manuellement un coût :

```bash
docker exec R1 vtysh -c "
  configure terminal
  interface eth1
  ip ospf cost 50
  exit
"
```

---

# Slide 15 : Exemple de Sortie Console

```
╔════════════════════════════════════════════════════════════════╗
║                     OSPF OPTIMIZER                              ║
║              Ajustement Dynamique des Coûts                     ║
╚════════════════════════════════════════════════════════════════╝

Configuration chargée depuis config/routers.yaml
7 routeurs configurés: ABR1, ABR2, ABR3, R1, R2, R3, R4

Collecte des métriques...
  ABR1-eth1 → ABR2-eth1: Latence=12ms, Perte=0%, BW=25%
  ABR1-eth3 → ABR3-eth0: Latence=8ms, Perte=0%, BW=18%
  ABR2-eth3 → ABR3-eth1: Latence=45ms, Perte=2%, BW=72%

Attention: Lien ABR2-ABR3: Latence élevée détectée (45ms > 30ms)
    Coût actuel: 15 → Nouveau coût recommandé: 35

Application des modifications...
  ✓ ABR2/eth3: Coût modifié 15 → 35
  ✓ ABR3/eth1: Coût modifié 15 → 35

Optimisation #42 terminée en 2.3s
   Prochaine analyse dans 30s...
```

---

# Slide 16 : Scénarios de Test

## Test 1 : Simulation de congestion
```bash
# Générer du trafic sur un lien
docker exec PC1 iperf3 -c 10.2.1.2 -t 60 -b 90M
```
**Résultat attendu** : Le coût du lien augmente, OSPF reroute le trafic

## Test 2 : Simulation de latence
```bash
# Ajouter de la latence sur une interface
docker exec ABR1 tc qdisc add dev eth1 root netem delay 100ms
```
**Résultat attendu** : L'optimiseur détecte la latence et augmente le coût

## Test 3 : Perte de paquets
```bash
# Simuler 5% de perte
docker exec ABR2 tc qdisc add dev eth3 root netem loss 5%
```
**Résultat attendu** : Le lien est pénalisé, trafic redirigé

---

# Slide 17 : Anti-Oscillation

## Problème des oscillations :
Si les coûts changent trop fréquemment, le réseau devient instable

## Solutions implémentées :

### 1. Seuil de changement minimum
```python
min_change_threshold: 5  # Changement min de 5 pour appliquer
```

### 2. Hystérésis
```yaml
thresholds:
  latency:
    high: 50       # Déclenche à 50ms
    recovery: 30   # Revient à la normale à 30ms
```

### 3. Historique des coûts
```python
# Détection des patterns oscillatoires
self.cost_history[link] = last_10_costs
if is_oscillating(cost_history):
    dampen_changes()
```

---

# Slide 18 : Interface Web - Aperçu

```
┌──────────────────────────────────────────────────────────────┐
│  OSPF OPTIMIZER DASHBOARD                      [Start][Stop] │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │ STATUS          │  │ MÉTRIQUES       │  │ CONFIG       │ │
│  │ Running         │  │ 7 Routeurs      │  │ Latency Mode  │ │
│  │ Uptime: 2h 34m  │  │ 12 Liens        │  │ Interval: 30s │ │
│  │ Optim: 287      │  │ Alerts: 2       │  │ Min Cost: 1   │ │
│  └─────────────────┘  └─────────────────┘  └───────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ LIENS SURVEILLÉS                                        │ │
│  ├──────────┬──────────┬──────────┬──────────┬────────────┤ │
│  │ Lien     │ Latence  │ Perte    │ BW Usage │ Coût OSPF  │ │
│  ├──────────┼──────────┼──────────┼──────────┼────────────┤ │
│  │ ABR1-ABR2│ 12ms OK  │ 0.0% OK  │ 25% OK   │ 15         │ │
│  │ ABR1-ABR3│ 8ms OK   │ 0.0% OK  │ 18% OK   │ 15         │ │
│  │ ABR2-ABR3│ 45ms High│ 2.0% Med │ 72% High │ 35 up      │ │
│  └──────────┴──────────┴──────────┴──────────┴────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ HISTORIQUE DES MODIFICATIONS                            │ │
│  │ 14:32:15 - ABR2/eth3: 15 → 35 (Latence: 45ms)          │ │
│  │ 14:30:45 - ABR3/eth1: 15 → 35 (Latence: 45ms)          │ │
│  │ 14:25:12 - ABR1/eth1: 20 → 15 (Recovery)               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

# Slide 19 : Points Forts de l'Implémentation

| Aspect | Avantage |
|--------|----------|
| **Modularité** | Chaque composant est indépendant et testable |
| **Flexibilité** | Configuration YAML facilement modifiable |
| **Automatisation** | Détection automatique des conteneurs GNS3 |
| **Monitoring** | Dashboard web en temps réel |
| **Sécurité** | Mode simulation pour tester sans risque |
| **Extensibilité** | Nouvelles stratégies faciles à ajouter |
| **Logging** | Traçabilité complète des modifications |
| **Anti-oscillation** | Stabilité du réseau garantie |

---

# Slide 20 : Perspectives d'Amélioration

## Court terme :
- Application mobile pour le monitoring
- Alertes email/SMS en cas d'anomalie
- Graphiques historiques avancés

## Moyen terme :
- Machine Learning pour prédiction des congestions
- Support multi-protocoles (IS-IS, EIGRP)
- Interface multi-sites

## Long terme :
- Intégration cloud (AWS, Azure)
- API pour orchestrateurs SDN
- Optimisation basée sur l'IA

---

# Slide 21 : Ressources et Documentation

## Fichiers du projet :
- `README.md` - Guide de démarrage rapide
- `docs/RAPPORT_PROJET_OSPF_OPTIMIZER.md` - Rapport complet
- `docs/TEST_WORKFLOW.md` - Procédures de test

## Commandes essentielles :

```bash
# Démarrage rapide
python auto_start.py --web

# Mode test sans modification
python auto_start.py --dry-run --verbose

# Exécution unique
python ospf_optimizer.py --simulation --once

# Avec configuration personnalisée
python ospf_optimizer.py --config config/routers.yaml --web
```

## Logs :
```bash
# Consulter les logs
tail -f ospf_optimizer.log
```

---

# Slide 22 : Conclusion

## Ce que nous avons implémenté :

- **Collecte de métriques** en temps réel via Docker exec
- **Calcul intelligent** des coûts OSPF selon plusieurs stratégies
- **Application automatique** des modifications via vtysh
- **Dashboard web** pour le monitoring et le contrôle
- **Détection automatique** des routeurs GNS3
- **Mode simulation** pour les tests sécurisés
- **Anti-oscillation** pour la stabilité réseau

---

## Merci de votre attention !

### Questions ?

```
┌────────────────────────────────────────┐
│  Contact: [Votre Email]                │
│  GitHub: [URL du Repo]                 │
│  Date: Décembre 2025                   │
└────────────────────────────────────────┘
```

---

# Annexes

## A. Schéma de la Topologie Réseau

```
                        ┌─────────┐
                        │  ABR3   │
                        │ 3.3.3.3 │
                        └────┬────┘
                    eth0     │     eth1
                 10.0.1.2    │   10.0.2.1
                             │
           ┌─────────────────┴─────────────────┐
           │                                   │
      eth3 │ 10.0.1.1                  10.0.2.2│ eth3
    ┌──────┴──────┐                    ┌───────┴─────┐
    │    ABR1     │──────eth1/eth1─────│    ABR2     │
    │  1.1.1.1    │  10.0.0.1/10.0.0.2 │  2.2.2.2    │
    └──────┬──────┘                    └───────┬─────┘
      eth0 │ eth2                         eth0 │ eth2
           │                                   │
    ┌──────┴──────┐                    ┌───────┴─────┐
    │  Zone 1     │                    │   Zone 2    │
    │ R1 ←→ R2    │                    │  R3 ←→ R4   │
    │ PC1   PC2   │                    │  PC3   PC4  │
    └─────────────┘                    └─────────────┘
```

## B. Table d'Adressage IP

| Routeur | Interface | Adresse IP | Zone OSPF |
|---------|-----------|------------|-----------|
| ABR1 | eth1 | 10.0.0.1/24 | 0 |
| ABR1 | eth3 | 10.0.1.1/24 | 0 |
| ABR1 | eth0 | 10.1.1.1/24 | 1 |
| ABR1 | eth2 | 10.1.2.1/24 | 1 |
| ABR2 | eth1 | 10.0.0.2/24 | 0 |
| ABR2 | eth3 | 10.0.2.2/24 | 0 |
| ABR2 | eth0 | 10.2.1.1/24 | 2 |
| ABR2 | eth2 | 10.2.2.1/24 | 2 |
| ABR3 | eth0 | 10.0.1.2/24 | 0 |
| ABR3 | eth1 | 10.0.2.1/24 | 0 |

## C. Dépendances Python (`requirements.txt`)

```
flask>=2.0.0
pyyaml>=6.0
netmiko>=4.0.0  # Pour SSH (optionnel)
paramiko>=2.0.0  # Pour SSH (optionnel)
```
