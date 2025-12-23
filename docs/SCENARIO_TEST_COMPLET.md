# Scénario de Test Complet - OSPF Optimizer
## Guide Pratique avec les Données Réelles du Projet

---

## Informations du Projet

| Élément | Valeur |
|---------|--------|
| **UUID GNS3** | `69de82ae-4d4a-48a4-a6fd-3dfa70716b11` |
| **Méthode de connexion** | `docker_exec` |
| **Timeout** | 30 secondes |
| **Coût de base** | 15 |
| **Stratégie** | Basée sur la latence (100%) |

---

## Topologie du Réseau

```
               ┌───────────────┐
               │     ABR3      │
               │   3.3.3.3     │
               │ GNS3.ABR3.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 │
               └───────┬───────┘
            eth0       │       eth1
           10.0.1.2      │     10.0.2.1
                   │
        ┌────────────────────┴────────────────────┐
        │                                         │
     eth3 │ 10.0.1.1                       10.0.2.2 │ eth3
  ┌─────────┴─────────┐                   ┌───────────┴────────┐
  │       ABR1        │───────eth1/eth1───│        ABR2        │
  │     1.1.1.1       │  10.0.0.1/10.0.0.2│      2.2.2.2       │
  │ GNS3.ABR1.69d...  │                   │  GNS3.ABR2.69d...  │
  └─────────┬─────────┘                   └───────────┬────────┘
     eth0 │ eth2                              eth0  │  eth2
   10.1.1.1 │ 10.1.2.1                      10.2.1.1  │  10.2.2.1
        │                                         │
  ┌─────────┴─────────┐                   ┌───────────┴────────┐
  │      ZONE 1       │                   │       ZONE 2       │
  │                   │                   │                    │
  │  ┌────┐   ┌────┐  │                   │  ┌────┐   ┌────┐   │
  │  │ R1 │   │ R2 │  │                   │  │ R3 │   │ R4 │   │
  │  │1.1.│   │1.1.│  │                   │  │2.2.│   │2.2.│   │
  │  │1.11│   │1.12│  │                   │  │2.11│   │2.12│   │
  │  └──┬─┘   └──┬─┘  │                   │  └──┬─┘   └──┬─┘   │
  │     │        │    │                   │     │        │     │
  │  [PC1]    [PC2]   │                   │  [PC3]    [PC4]    │
  └───────────────────┘                   └────────────────────┘
```

---

## Table d'Adressage Complète

### Routeurs ABR (Area Border Routers)

| Routeur | Container Name | Router ID | Interface | IP | Zone |
|---------|----------------|-----------|-----------|-----|------|
| **ABR1** | `GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11` | 1.1.1.1 | eth1 | 10.0.0.1 | 0 |
| | | | eth3 | 10.0.1.1 | 0 |
| | | | eth0 | 10.1.1.1 | 1 |
| | | | eth2 | 10.1.2.1 | 1 |
| **ABR2** | `GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11` | 2.2.2.2 | eth1 | 10.0.0.2 | 0 |
| | | | eth3 | 10.0.2.2 | 0 |
| | | | eth0 | 10.2.1.1 | 2 |
| | | | eth2 | 10.2.2.1 | 2 |
| **ABR3** | `GNS3.ABR3.69de82ae-4d4a-48a4-a6fd-3dfa70716b11` | 3.3.3.3 | eth0 | 10.0.1.2 | 0 |
| | | | eth1 | 10.0.2.1 | 0 |

### Routeurs Internes

| Routeur | Container Name | Router ID | Interface | IP | Zone |
|---------|----------------|-----------|-----------|-----|------|
| **R1** | `GNS3.R1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11` | 1.1.1.11 | eth1 | 10.1.1.2 | 1 |
| **R2** | `GNS3.R2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11` | 1.1.1.12 | eth1 | 10.1.2.2 | 1 |
| **R3** | `GNS3.R3.69de82ae-4d4a-48a4-a6fd-3dfa70716b11` | 2.2.2.11 | eth1 | 10.2.1.2 | 2 |
| **R4** | `GNS3.R4.69de82ae-4d4a-48a4-a6fd-3dfa70716b11` | 2.2.2.12 | eth1 | 10.2.2.2 | 2 |

---

## Liens Surveillés

| Nom du Lien | Source | Interface | Destination | Interface | IP Destination |
|-------------|--------|-----------|-------------|-----------|----------------|
| ABR1-ABR2 | ABR1 | eth1 | ABR2 | eth1 | 10.0.0.2 |
| ABR1-ABR3 | ABR1 | eth3 | ABR3 | eth0 | 10.0.1.2 |
| ABR2-ABR3 | ABR2 | eth3 | ABR3 | eth1 | 10.0.2.1 |
| ABR1-R1 | ABR1 | eth0 | R1 | eth1 | 10.1.1.2 |
| ABR1-R2 | ABR1 | eth2 | R2 | eth1 | 10.1.2.2 |
| ABR2-R3 | ABR2 | eth0 | R3 | eth1 | 10.2.1.2 |
| ABR2-R4 | ABR2 | eth2 | R4 | eth1 | 10.2.2.2 |

---

## Configuration des Seuils

```yaml
thresholds:
  latency:
  high: 50        # Alerte si latence > 50ms
  recovery: 30    # Retour normal si < 30ms
  packet_loss:
  high: 5         # Alerte si perte > 5%
  bandwidth:
  high: 80        # Alerte si utilisation > 80%

cost_factors:
  base_cost: 15
  min_cost: 1
  max_cost: 500
  min_change_threshold: 1
  multipliers:
  bandwidth_weight: 0.0
  latency_weight: 1.0
  packet_loss_weight: 0.0
```

---

## SCÉNARIO 1 : Vérification de l'Environnement

### Étape 1.1 : Activer l'environnement virtuel

**Windows (PowerShell) :**
```powershell
cd C:\OSPF_Optimizer
.\venv\Scripts\Activate.ps1
```

**Linux/Mac :**
```bash
cd ~/OSPF_Optimizer
python3 -m venv venv
source venv/bin/activate
```

**Résultat attendu :** Le prompt affiche `(venv)`

### Étape 1.2 : Vérifier les conteneurs Docker

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep "frrouting"
```

**Résultat attendu :**
```
NAMES                                            IMAGE           STATUS
GNS3.ABR3.69de82ae-4d4a-48a4-a6fd-3dfa70716b11   frrouting:v1    Up 2 days
GNS3.R4.69de82ae-4d4a-48a4-a6fd-3dfa70716b11     frrouting:v1    Up 2 days
GNS3.R3.69de82ae-4d4a-48a4-a6fd-3dfa70716b11     frrouting:v1    Up 2 days
GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11   frrouting:v1    Up 2 days
GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11   frrouting:v1    Up 2 days
GNS3.R2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11     frrouting:v1    Up 2 days
GNS3.R1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11     frrouting:v1    Up 2 days
```

---

## SCÉNARIO 2 : Test de Connectivité aux Routeurs

### Étape 2 : Tester l'accès Docker à ABR1

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 echo "Connexion OK"
```

**Résultat attendu :** `Connexion OK`

## SCÉNARIO 3 : Vérification OSPF

### Étape 3.1 : Vérifier les voisins OSPF sur ABR1

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 vtysh -c "show ip ospf neighbor"
```

**Résultat attendu :**
```
Neighbor ID     Pri State           Up Time         Dead Time Address         Interface
2.2.2.2           1 Full/DR         01:23:45        00:00:35  10.0.0.2        eth1:10.0.0.1
3.3.3.3           1 Full/DR         01:23:40        00:00:33  10.0.1.2        eth3:10.0.1.1
1.1.1.11          1 Full/DR         01:23:30        00:00:38  10.1.1.2        eth0:10.1.1.1
1.1.1.12          1 Full/DR         01:23:28        00:00:36  10.1.2.2        eth2:10.1.2.1
```

### Étape 3.2 : Vérifier les voisins OSPF sur ABR2

```bash
docker exec GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 vtysh -c "show ip ospf neighbor"
```

**Résultat attendu :**
```
Neighbor ID     Pri State           Up Time         Dead Time Address         Interface
1.1.1.1           1 Full/DR         01:23:45        00:00:35  10.0.0.1        eth1:10.0.0.2
3.3.3.3           1 Full/DR         01:23:40        00:00:33  10.0.2.1        eth3:10.0.2.2
2.2.2.11          1 Full/DR         01:23:30        00:00:38  10.2.1.2        eth0:10.2.1.1
2.2.2.12          1 Full/DR         01:23:28        00:00:36  10.2.2.2        eth2:10.2.2.1
```

### Étape 3.3 : Vérifier les voisins OSPF sur ABR3

```bash
docker exec GNS3.ABR3.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 vtysh -c "show ip ospf neighbor"
```

**Résultat attendu :**
```
Neighbor ID     Pri State           Up Time         Dead Time Address         Interface
1.1.1.1           1 Full/DR         01:23:45        00:00:35  10.0.1.1        eth0:10.0.1.2
2.2.2.2           1 Full/DR         01:23:40        00:00:33  10.0.2.2        eth1:10.0.2.1
```

### Étape 3.4 : Afficher les interfaces OSPF sur ABR1

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 vtysh -c "show ip ospf interface"
```

**Résultat attendu (extrait) :**
```
eth1 is up
  Internet Address 10.0.0.1/24, Broadcast 10.0.0.255, Area 0.0.0.0
  MTU mismatch detection: enabled
  Router ID 1.1.1.1, Network Type BROADCAST, Cost: 15
  ...

eth3 is up
  Internet Address 10.0.1.1/24, Broadcast 10.0.1.255, Area 0.0.0.0
  Router ID 1.1.1.1, Network Type BROADCAST, Cost: 15
  ...

eth0 is up
  Internet Address 10.1.1.1/24, Broadcast 10.1.1.255, Area 0.0.0.1
  Router ID 1.1.1.1, Network Type BROADCAST, Cost: 15
  ...
```

### Étape 3.5 : Afficher la table de routage OSPF

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 vtysh -c "show ip route ospf"
```

**Résultat attendu :**
```
O   10.0.0.0/24 [110/15] is directly connected, eth1, weight 1, 01:23:45
O   10.0.1.0/24 [110/15] is directly connected, eth3, weight 1, 01:23:45
O   10.0.2.0/24 [110/30] via 10.0.0.2, eth1, weight 1, 01:23:40
        [110/30] via 10.0.1.2, eth3, weight 1, 01:23:40
O   10.1.1.0/24 [110/15] is directly connected, eth0, weight 1, 01:23:30
O   10.1.2.0/24 [110/15] is directly connected, eth2, weight 1, 01:23:28
O IA 10.2.1.0/24 [110/30] via 10.0.0.2, eth1, weight 1, 01:23:25
O IA 10.2.2.0/24 [110/30] via 10.0.0.2, eth1, weight 1, 01:23:25
```

---

## SCÉNARIO 4 : Test de Latence entre Routeurs

### Étape 4.1 : Ping ABR1 vers ABR2 (10.0.0.2)

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 ping -c 5 10.0.0.2
```

**Résultat attendu :**
```
PING 10.0.0.2 (10.0.0.2): 56 data bytes
64 bytes from 10.0.0.2: seq=0 ttl=64 time=0.523 ms
64 bytes from 10.0.0.2: seq=1 ttl=64 time=0.412 ms
64 bytes from 10.0.0.2: seq=2 ttl=64 time=0.398 ms
64 bytes from 10.0.0.2: seq=3 ttl=64 time=0.421 ms
64 bytes from 10.0.0.2: seq=4 ttl=64 time=0.445 ms

--- 10.0.0.2 ping statistics ---
5 packets transmitted, 5 packets received, 0% packet loss
round-trip min/avg/max = 0.398/0.439/0.523 ms
```

### Étape 4.2 : Ping ABR1 vers ABR3 (10.0.1.2)

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 ping -c 5 10.0.1.2
```

### Étape 4.3 : Ping ABR2 vers ABR3 (10.0.2.1)

```bash
docker exec GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 ping -c 5 10.0.2.1
```

### Étape 4.4 : Ping ABR1 vers R1 (10.1.1.2)

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 ping -c 5 10.1.1.2
```

### Étape 4.5 : Ping ABR2 vers R3 (10.2.1.2)

```bash
docker exec GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 ping -c 5 10.2.1.2
```

---

## SCÉNARIO 5 : Lancement de l'Optimiseur

### Étape 5.1 : Mode Dry-Run (Sans modification)

```powershell
cd C:\OSPF_Optimizer
python auto_start.py --dry-run --verbose
```

**Résultat attendu :**
```
╔════════════════════════════════════════════════════════════════╗
║                     OSPF OPTIMIZER                              ║
║              Démarrage Automatique                              ║
╚════════════════════════════════════════════════════════════════╝

Détection des conteneurs Docker...

Conteneurs détectés:
  ABR1: GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  ABR2: GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  ABR3: GNS3.ABR3.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  R1:   GNS3.R1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  R2:   GNS3.R2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  R3:   GNS3.R3.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  R4:   GNS3.R4.69de82ae-4d4a-48a4-a6fd-3dfa70716b11

Configuration déjà à jour

Collecte des métriques...
  ABR1-ABR2: Latence=0.5ms, Perte=0%, BW=12%
  ABR1-ABR3: Latence=0.4ms, Perte=0%, BW=8%
  ABR2-ABR3: Latence=0.6ms, Perte=0%, BW=15%
  ABR1-R1:   Latence=0.3ms, Perte=0%, BW=5%
  ABR1-R2:   Latence=0.3ms, Perte=0%, BW=6%
  ABR2-R3:   Latence=0.4ms, Perte=0%, BW=7%
  ABR2-R4:   Latence=0.4ms, Perte=0%, BW=4%

Analyse des coûts:
  Tous les liens sont dans les seuils normaux
  Aucune modification nécessaire

[DRY-RUN] Aucun changement appliqué
```

### Étape 5.2 : Détection des conteneurs uniquement

```powershell
python auto_start.py --detect-only
```

**Résultat attendu :**
```
Mode détection uniquement

Conteneurs FRRouting détectés:
  ABR1 → GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  ABR2 → GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  ABR3 → GNS3.ABR3.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  R1   → GNS3.R1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  R2   → GNS3.R2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  R3   → GNS3.R3.69de82ae-4d4a-48a4-a6fd-3dfa70716b11
  R4   → GNS3.R4.69de82ae-4d4a-48a4-a6fd-3dfa70716b11

Total: 7 routeurs FRR détectés
```

### Étape 5.3 : Lancement avec Dashboard Web

```powershell
python auto_start.py --web --port 8080
```

**Résultat attendu :**
```
╔════════════════════════════════════════════════════════════════╗
║                     OSPF OPTIMIZER                              ║
╚════════════════════════════════════════════════════════════════╝

7 routeurs configurés
7 liens surveillés

Dashboard web démarré sur http://localhost:8080

Cycle d'optimisation #1...
  Collecte des métriques: OK
  Analyse: Tous les liens stables
  Prochaine analyse dans 30s

[Ctrl+C pour arrêter]
```

**Accès au dashboard :** Ouvrir http://localhost:8080 dans un navigateur

---

## SCÉNARIO 6 : Simulation de Congestion

### Étape 6.1 : Ajouter de la latence sur le lien ABR1-ABR2

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 tc qdisc add dev eth1 root netem delay 100ms
```

### Étape 6.2 : Vérifier la latence

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 ping -c 5 10.0.0.2
```

**Résultat attendu :** Latence ~100ms au lieu de <1ms

### Étape 6.3 : Observer la réaction de l'optimiseur

L'optimiseur devrait détecter la latence élevée (100ms > 50ms) et augmenter le coût :

```
Attention: Lien ABR1-ABR2: Latence élevée détectée (100ms > 50ms)
  Coût actuel: 15 → Nouveau coût recommandé: 115

Application des modifications...
  ✓ ABR1/eth1: Coût modifié 15 → 115
  ✓ ABR2/eth1: Coût modifié 15 → 115
```

### Étape 6.4 : Vérifier le changement de coût

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 vtysh -c "show ip ospf interface eth1" | grep Cost
```

**Résultat attendu :** `Cost: 115`

### Étape 6.5 : Vérifier le reroutage OSPF

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 vtysh -c "show ip route ospf"
```

**Résultat attendu :** Le trafic vers Zone 2 passe maintenant par ABR3 au lieu de ABR1-ABR2 directement

### Étape 6.6 : Supprimer la latence simulée

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 tc qdisc del dev eth1 root
```

### Étape 6.7 : Attendre la récupération

Après quelques cycles, l'optimiseur devrait détecter le retour à la normale et réduire le coût :

```
Lien ABR1-ABR2: Latence normale (0.5ms < 30ms)
   Coût actuel: 115 → Nouveau coût: 15 (Recovery)
```

---

## SCÉNARIO 7 : Simulation de Perte de Paquets

### Étape 7.1 : Ajouter 10% de perte sur ABR2-ABR3

```bash
docker exec GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 tc qdisc add dev eth3 root netem loss 10%
```

### Étape 7.2 : Vérifier la perte

```bash
docker exec GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 ping -c 20 10.0.2.1
```

**Résultat attendu :** ~10% de paquets perdus

### Étape 7.3 : Supprimer la perte simulée

```bash
docker exec GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 tc qdisc del dev eth3 root
```

---

## SCÉNARIO 8 : Modification Manuelle des Coûts OSPF

### Étape 8.1 : Augmenter le coût sur ABR1/eth1

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 vtysh -c "
configure terminal
interface eth1
ip ospf cost 50
exit
exit
write memory
"
```

### Étape 8.2 : Vérifier le changement

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 vtysh -c "show ip ospf interface eth1" | grep Cost
```

**Résultat attendu :** `Cost: 50`

### Étape 8.3 : Remettre le coût initial

```bash
docker exec GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11 vtysh -c "
configure terminal
interface eth1
ip ospf cost 15
exit
exit
write memory
"
```

---

## SCÉNARIO 9 : Mode Simulation (Données Simulées)

### Étape 9.1 : Exécution unique en mode simulation

```powershell
python ospf_optimizer.py --simulation --once --verbose
```

**Résultat attendu :** Données simulées sans connexion aux vrais routeurs

```
╔════════════════════════════════════════════════════════════════╗
║           OSPF OPTIMIZER - MODE SIMULATION                      ║
╚════════════════════════════════════════════════════════════════╝

Attention: Mode simulation activé - Pas de connexion réelle

Métriques simulées:
  ABR1-ABR2: Latence=12ms (simulé), Perte=0.5%, BW=45%
  ABR1-ABR3: Latence=8ms (simulé), Perte=0.1%, BW=32%
  ABR2-ABR3: Latence=65ms (simulé), Perte=2.3%, BW=78%
  ...

Attention: Liens nécessitant une optimisation:
  ABR2-ABR3: Latence élevée (65ms > 50ms)
  Coût recommandé: 15 → 80

[SIMULATION] Aucun changement appliqué aux routeurs
```

---

## Résumé des Commandes Essentielles

### Démarrage

| Commande | Description |
|----------|-------------|
| `python auto_start.py --web` | Démarrage standard avec dashboard |
| `python auto_start.py --dry-run` | Test sans modification |
| `python auto_start.py --detect-only` | Détection des conteneurs |
| `python ospf_optimizer.py --simulation --once` | Mode simulation |

### Vérification OSPF

| Commande | Description |
|----------|-------------|
| `vtysh -c "show ip ospf neighbor"` | Voisins OSPF |
| `vtysh -c "show ip ospf interface"` | Interfaces OSPF |
| `vtysh -c "show ip route ospf"` | Table de routage |
| `vtysh -c "show ip ospf database"` | Base de données OSPF |

### Simulation de problèmes

| Commande | Description |
|----------|-------------|
| `tc qdisc add dev eth1 root netem delay 100ms` | Ajouter latence |
| `tc qdisc add dev eth1 root netem loss 5%` | Ajouter perte |
| `tc qdisc del dev eth1 root` | Supprimer les simulations |

---

## Checklist de Validation

- [ ] Environnement virtuel activé
- [ ] 7 conteneurs FRR en cours d'exécution
- [ ] Accès Docker exec fonctionnel sur tous les routeurs
- [ ] Voisins OSPF en état FULL
- [ ] Ping fonctionnel entre tous les routeurs adjacents
- [ ] Mode dry-run exécuté sans erreur
- [ ] Dashboard web accessible sur http://localhost:8080
- [ ] Test de latence simulée réussi
- [ ] Récupération automatique après suppression de la latence
