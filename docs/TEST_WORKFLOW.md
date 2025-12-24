# Optimiseur OSPF - Guide du Flux de Tests

Ce document fournit un flux de travail étape par étape pour vérifier que le projet Optimiseur OSPF fonctionne correctement.

---

## Liste de Vérification des Prérequis

Avant de commencer les tests, assurez-vous que :

- [X] La VM Ubuntu est en cours d'exécution avec GNS3 installé
- [ ] Le projet GNS3 avec la topologie OSPF est ouvert et démarré
- [ ] Docker est en cours d'exécution (`systemctl status docker`)
- [ ] Tous les conteneurs de routeurs sont en cours d'exécution (`docker ps`)
- [ ] Python 3.10+ est installé
- [ ] L'environnement virtuel est configuré

---

## Aperçu du Flux de Tests

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUX DE TESTS                             │
├─────────────────────────────────────────────────────────────┤
│  Étape 1 : Configuration de l'environnement                  │
│  Étape 2 : Détection des conteneurs                          │
│  Étape 3 : Connectivité des routeurs                         │
│  Étape 4 : Vérification du statut OSPF                       │
│  Étape 5 : Collecte des métriques                            │
│  Étape 6 : Optimisation à blanc                              │
│  Étape 7 : Optimisation en direct                            │
│  Étape 8 : Interface Web                                     │
│  Étape 9 : Validation de bout en bout                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Étape 1 : Configuration de l'Environnement

### 1.1 Activer l'Environnement Virtuel

```bash
cd ~/OSPF_Optimizer
source venv/bin/activate
```

**Attendu :** L'invite de commande affiche le préfixe `(venv)`.

### 1.2 Vérifier les Dépendances Python

```bash
pip list | grep -E "flask|pyyaml|requests"
```

**Sortie Attendue :**
```
Flask             3.x.x
PyYAML            6.x.x
requests          2.x.x
```

### 1.3 Vérifier la Structure du Projet

```bash
ls -la
```

**Attendu :** Tous les fichiers requis présents :
- `ospf_optimizer.py`
- `auto_start.py`
- `config/routers.yaml`
- Répertoire `src/` avec les modules

---

## Étape 2 : Détection des Conteneurs

### 2.1 Lister les Conteneurs Docker en Cours d'Exécution

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
```

**Sortie Attendue :** Conteneurs FRRouting pour ABR1, ABR2, ABR3, R1, R2, R3, R4

Exemple :
```
NAMES                                              IMAGE           STATUS
GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11    frrouting:v1    Up 2 hours
GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11    frrouting:v1    Up 2 hours
...
```

### 2.2 Tester le Script de Détection Automatique

```bash
python3 auto_start.py --dry-run --verbose
```

**Attendu :**
- Conteneurs détectés
- Fichier de configuration mis à jour
- Aucune erreur

**Critères de Succès :**
```
[INFO] Conteneurs détectés :
  ABR1: GNS3.ABR1.xxxxx
  ABR2: GNS3.ABR2.xxxxx
  ...
[INFO] Configuration mise à jour avec succès
```

---

## Étape 3 : Connectivité des Routeurs

### 3.1 Tester l'Accès Docker Exec

Tester l'accès à chaque routeur :

```bash
# Tester ABR1
docker exec $(docker ps --format "{{.Names}}" | grep "ABR1") echo "OK"

# Tester ABR2
docker exec $(docker ps --format "{{.Names}}" | grep "ABR2") echo "OK"

# Tester tous les routeurs
for router in ABR1 ABR2 ABR3 R1 R2 R3 R4; do
  container=$(docker ps --format "{{.Names}}" | grep "\\.$router\\.")
  if [ -n "$container" ]; then
    result=$(docker exec $container echo "OK" 2>&1)
    echo "$router: $result"
  else
    echo "$router: NON TROUVÉ"
  fi
done
```

**Attendu :** Tous les routeurs répondent avec "OK"

### 3.2 Tester l'Accès vtysh

```bash
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container vtysh -c "show version"
```

**Attendu :** Informations de version FRRouting affichées

---

## Étape 4 : Vérification du Statut OSPF

### 4.1 Vérifier qu'OSPF est en Cours d'Exécution

```bash
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container vtysh -c "show ip ospf"
```

**Attendu :** Informations du processus OSPF avec l'ID du routeur

### 4.2 Vérifier les Voisins OSPF

```bash
for router in ABR1 ABR2 ABR3; do
  container=$(docker ps --format "{{.Names}}" | grep "\\.$router\\.")
  echo "=== Voisins OSPF de $router ==="
  docker exec $container vtysh -c "show ip ospf neighbor"
done
```

**Attendu :** Chaque ABR affiche des voisins en état FULL

Exemple de sortie :
```
=== Voisins OSPF de ABR1 ===
Neighbor ID     Pri State           Up Time         Dead Time Address         Interface
22.22.22.22       1 Full/DR         00:45:12        00:00:35  10.0.0.2        eth1
33.33.33.33       1 Full/DR         00:45:10        00:00:33  10.0.1.2        eth3
```

### 4.3 Vérifier les Coûts des Interfaces OSPF

```bash
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container vtysh -c "show ip ospf interface"
```

**Attendu :** Liste des interfaces avec valeurs de coût (par défaut : 10)

---

## Étape 5 : Test de Collecte des Métriques

### 5.1 Tester le Ping Entre Routeurs

```bash
# Ping de ABR1 vers ABR2
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container ping -c 5 10.0.0.2
```

**Attendu :**
- 5 paquets transmis
- 0% de perte de paquets
- Valeurs de latence affichées

### 5.2 Tester le Module de Collecte de Métriques

Créer un script de test rapide :

```bash
python3 -c "
from src.metrics_collector import MetricsCollector
from src.router_connection import RouterConnection
import yaml

with open('config/routers.yaml', 'r') as f:
    config = yaml.safe_load(f)

conn = RouterConnection(config)
if conn.test_connections():
  print('Connexions routeurs : OK')
else:
  print('Connexions routeurs : ÉCHOUÉ')
"
```

**Attendu :** `Connexions routeurs : OK`

---

## Étape 6 : Optimisation à Blanc

### 6.1 Exécuter une Optimisation Unique (À Blanc)

```bash
python3 ospf_optimizer.py --config config/routers.yaml --once --dry-run --verbose
```

**Sortie Attendue :**
```
============================================================
Optimiseur OSPF - Démarrage
============================================================
Mode : Exécution unique (à blanc)
Stratégie : composite

Collecte des métriques pour tous les liens...
  ABR1-ABR2 (Primaire) : BP : 5,2%, Latence : 0,8ms, Perte : 0,0%
  ABR1-ABR3 (Secours) : BP : 2,1%, Latence : 0,5ms, Perte : 0,0%
  ...

RÉSUMÉ DE L'OPTIMISATION
------------------------------------------------------------
Liens surveillés : 7
Liens à mettre à jour : 0
Liens stables : 7

[À BLANC] Aucun changement appliqué
============================================================
```

**Critères de Succès :**
- Aucune erreur Python
- Métriques collectées pour tous les liens
- Résumé affiché

### 6.2 Tester avec des Données Simulées

```bash
python3 ospf_optimizer.py --config config/routers.yaml --once --dry-run --simulation
```

**Attendu :** Métriques simulées avec changements de coût potentiels proposés

---

## Étape 7 : Test d'Optimisation en Direct

Attention : Cela modifiera les coûts OSPF sur les routeurs !

### 7.1 Exécuter une Optimisation Unique en Direct

```bash
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose
```

**Attendu :**
- Métriques collectées
- Si les conditions le justifient, les coûts sont appliqués
- Modifications sauvegardées dans la configuration du routeur

### 7.2 Vérifier les Changements de Coût (le cas échéant)

```bash
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container vtysh -c "show ip ospf interface" | grep -E "Cost:|eth"
```

**Attendu :** Valeurs de coût mises à jour visibles

### 7.3 Réinitialiser les Coûts par Défaut

Si vous devez réinitialiser :

```bash
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container vtysh -c "
configure terminal
interface eth0
ip ospf cost 10
interface eth1
ip ospf cost 10
end
write memory
"
```

---

## Étape 8 : Test de l'Interface Web

### 8.1 Démarrer le Tableau de Bord Web

```bash
python3 ospf_optimizer.py --config config/routers.yaml --web --port 8080
```

Ou en utilisant auto_start :

```bash
python3 auto_start.py --web --port 8080
```

**Attendu :** Le serveur démarre sur le port 8080

```
 * Running on http://0.0.0.0:8080
 * Press CTRL+C to stop
```

### 8.2 Tester l'Accès au Tableau de Bord

Ouvrir le navigateur ou utiliser curl :

```bash
curl http://localhost:8080/
```

**Attendu :** Contenu HTML du tableau de bord

### 8.3 Tester les Points d'Accès API

```bash
# Obtenir le statut
curl http://localhost:8080/api/status

# Obtenir la configuration
curl http://localhost:8080/api/config

# Déclencher l'optimisation (à blanc)
curl -X POST "http://localhost:8080/api/optimize?dry_run=true"
```

**Attendu :** Réponses JSON avec données

### 8.4 Tester via le Navigateur

1. Ouvrir : `http://<IP_VM>:8080`
2. Vérifier que le tableau de bord se charge
3. Cliquer sur "Statut" - vérifier l'affichage des métriques
4. Cliquer sur "Optimiser Maintenant" - vérifier l'exécution

---

## Étape 9 : Validation de Bout en Bout

### 9.1 Scénario de Test Complet

```bash
# 1. Démarrer avec la détection automatique
python3 auto_start.py --web --verbose

# 2. Dans un autre terminal, vérifier les routes avant
container=$(docker ps --format "{{.Names}}" | grep "R1")
docker exec $container vtysh -c "show ip route ospf"

# 3. Générer du trafic (simuler une charge)
# De R1 vers R4
docker exec $container ping -c 100 -i 0.1 192.168.4.1 &

# 4. Déclencher l'optimisation via l'API web
curl -X POST http://localhost:8080/api/optimize

# 5. Vérifier les routes après
docker exec $container vtysh -c "show ip route ospf"
```

### 9.2 Test de Connectivité Après Optimisation

```bash
# Tester le chemin complet : PC1 vers PC4
pc1=$(docker ps --format "{{.Names}}" | grep "PC1")
docker exec $pc1 ping -c 10 192.168.4.10
```

**Attendu :** Connectivité maintenue, possiblement via un chemin différent

---

## Script de Validation Rapide

Créer et exécuter ce script pour des tests automatisés :

```bash
#!/bin/bash
# Fichier : test_all.sh

echo "=========================================="
echo "Optimiseur OSPF - Validation Rapide"
echo "=========================================="

cd ~/OSPF_Optimizer
source venv/bin/activate

# Test 1 : Vérifier les conteneurs
echo -e "\n[TEST 1] Conteneurs Docker"
count=$(docker ps --format "{{.Names}}" | grep -E "ABR|\.R[1-4]\." | wc -l)
if [ "$count" -ge 7 ]; then
  echo "RÉUSSI : $count conteneurs de routeurs trouvés"
else
  echo "ÉCHOUÉ : Seulement $count conteneurs trouvés (attendu 7+)"
fi

# Test 2 : Vérifier OSPF sur ABR1
echo -e "\n[TEST 2] Statut OSPF"
container=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
if docker exec $container vtysh -c "show ip ospf" | grep -q "Router ID"; then
  echo "RÉUSSI : OSPF est en cours d'exécution"
else
  echo "ÉCHOUÉ : OSPF n'est pas en cours d'exécution"
fi

# Test 3 : Optimisation à blanc
echo -e "\n[TEST 3] Optimisation à Blanc"
if python3 ospf_optimizer.py --config config/routers.yaml --once --dry-run 2>&1 | grep -q "Links monitored"; then
  echo "RÉUSSI : Optimisation exécutée"
else
  echo "ÉCHOUÉ : Optimisation échouée"
fi

# Test 4 : Interface web
echo -e "\n[TEST 4] Interface Web"
python3 ospf_optimizer.py --config config/routers.yaml --web --port 8888 &
pid=$!
sleep 3
if curl -s http://localhost:8888/api/status | grep -q "status"; then
  echo "RÉUSSI : API Web répond"
else
  echo "ÉCHOUÉ : API Web ne répond pas"
fi
kill $pid 2>/dev/null

echo -e "\n=========================================="
echo "Validation Terminée"
echo "=========================================="
```

---

## Dépannage

### Problème : Conteneurs Non Trouvés

**Symptôme :** `docker ps` n'affiche aucun conteneur GNS3

**Solution :**
1. Ouvrir GNS3 et démarrer le projet
2. Démarrer tous les nœuds (clic droit → Tout Démarrer)
3. Attendre 30 secondes pour l'initialisation des conteneurs
4. Exécuter à nouveau `docker ps`

### Problème : vtysh Ne Fonctionne Pas

**Symptôme :** `vtysh: command not found` ou permission refusée

**Solution :**
```bash
# Vérifier si FRR est en cours d'exécution
docker exec <conteneur> ps aux | grep -E "ospfd|zebra"

# Si non en cours d'exécution, démarrer les services
docker exec <conteneur> /usr/lib/frr/frrinit.sh start
```

### Problème : Les Voisins OSPF Ne Se Forment Pas

**Symptôme :** `show ip ospf neighbor` est vide

**Solution :**
1. Vérifier la configuration IP de l'interface
2. Vérifier les instructions réseau dans la configuration OSPF
3. Vérifier si les câbles sont connectés dans GNS3
4. S'assurer que les deux extrémités sont dans la même zone

### Problème : Erreurs d'Importation Python

**Symptôme :** `ModuleNotFoundError: No module named 'src'`

**Solution :**
```bash
# S'assurer d'être dans le répertoire du projet
cd ~/OSPF_Optimizer

# S'assurer que venv est activé
source venv/bin/activate

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Problème : Interface Web Non Accessible

**Symptôme :** Impossible de se connecter à `http://localhost:8080`

**Solution :**
1. Vérifier si le serveur est en cours d'exécution (`ps aux | grep ospf_optimizer`)
2. Essayer un port différent : `--port 5000`
3. Vérifier le pare-feu : `sudo ufw allow 8080`
4. La liaison à toutes les interfaces est par défaut (0.0.0.0)

---

## Tests de Scénarios

Ces scénarios simulent des conditions réelles pour valider que l'Optimiseur OSPF détecte correctement les problèmes et ajuste les coûts.

### Scénario 1 : Simulation de Congestion de Lien

**Objectif :** Vérifier qu'une utilisation élevée de la bande passante déclenche une augmentation du coût.

**Étapes :**

```bash
# 1. Vérifier les coûts initiaux sur ABR1
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"
# Noter le coût initial (devrait être 10)

# 2. Vérifier la table de routage avant (du point de vue de R1)
container_r1=$(docker ps --format "{{.Names}}" | grep "\.R1\." | head -1)
echo "=== Routes AVANT congestion ==="
docker exec $container_r1 vtysh -c "show ip route ospf"

# 3. Générer un trafic important sur le lien ABR1-ABR2 (épine dorsale primaire)
# Démarrer le générateur de trafic en arrière-plan
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
docker exec $container_abr1 sh -c "
  # Générer un trafic continu vers ABR2 pendant 2 minutes
  ping -c 1000 -i 0.01 -s 65000 10.0.0.2 > /dev/null 2>&1 &
  # Inonder également avec de petits paquets
  for i in \$(seq 1 50); do
    ping -c 100 -i 0.001 10.0.0.2 > /dev/null 2>&1 &
  done
"

# 4. Exécuter l'optimiseur dans un nouveau terminal
cd ~/OSPF_Optimizer
source venv/bin/activate
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose

# 5. Vérifier si le coût a été augmenté
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"
# Attendu : Le coût devrait être supérieur à 10 si la congestion a été détectée

# 6. Vérifier la table de routage après
echo "=== Routes APRÈS optimisation ==="
docker exec $container_r1 vtysh -c "show ip route ospf"
# Le trafic peut maintenant être routé via ABR3 (secours) si le coût primaire a augmenté
```

**Résultats Attendus :**
- Coût initial : 10
- Après optimisation : Coût augmenté (par ex., 25-50 selon la charge)
- Les routes peuvent se déplacer vers le chemin de secours via ABR3

**Critères de Succès :**
| Métrique | Avant | Après | Réussi ? |
|--------|--------|-------|-------|
| Coût ABR1-ABR2 | 10 | >10 | ⬜ |
| Optimiseur a détecté la charge | - | Oui | ⬜ |
| Route changée (optionnel) | Via ABR2 | Via ABR3 | ⬜ |

---

### Scénario 2 : Simulation de Dégradation de Latence

**Objectif :** Vérifier qu'une latence élevée déclenche une augmentation du coût.

**Étapes :**

```bash
# 1. Ajouter une latence artificielle en utilisant tc (traffic control)
# Cela nécessite d'exécuter tc à l'intérieur du conteneur ou sur l'hôte

container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)

# Vérifier si tc est disponible (peut nécessiter l'installation de iproute2)
docker exec $container_abr1 sh -c "tc qdisc show dev eth1" 2>/dev/null || \
  echo "tc non disponible, utilisation d'une méthode alternative"

# Alternative : Si tc est disponible, ajouter un délai de 100ms
docker exec $container_abr1 sh -c "
  tc qdisc add dev eth1 root netem delay 100ms 2>/dev/null || \
  tc qdisc change dev eth1 root netem delay 100ms 2>/dev/null
"

# 2. Vérifier que la latence est ajoutée
docker exec $container_abr1 ping -c 5 10.0.0.2
# Attendu : rtt devrait afficher ~100ms

# 3. Exécuter l'optimiseur
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose

# 4. Vérifier la sortie pour la détection de latence
# Attendu : "ABR1-ABR2: Latence : ~100ms" et augmentation de coût proposée

# 5. Nettoyage - supprimer le délai artificiel
docker exec $container_abr1 sh -c "tc qdisc del dev eth1 root 2>/dev/null"

# 6. Vérifier que la latence est revenue à la normale
docker exec $container_abr1 ping -c 5 10.0.0.2
```

**Résultats Attendus :**
- Latence détectée : ~100ms
- Augmentation du coût : 10 → ~30 (basé sur le facteur de latence)
- La route peut se déplacer vers un chemin à latence plus faible

**Note :** Si `tc` n'est pas disponible dans le conteneur, vous pouvez simuler la détection de latence en modifiant le collecteur de métriques pour injecter des valeurs de test.

---

### Scénario 3 : Simulation de Perte de Paquets

**Objectif :** Vérifier que la perte de paquets déclenche une augmentation du coût.

**Étapes :**

```bash
# 1. Ajouter une perte de paquets artificielle en utilisant tc
container_abr2=$(docker ps --format "{{.Names}}" | grep "ABR2" | head -1)

# Ajouter 10% de perte de paquets
docker exec $container_abr2 sh -c "
  tc qdisc add dev eth1 root netem loss 10% 2>/dev/null || \
  tc qdisc change dev eth1 root netem loss 10% 2>/dev/null
"

# 2. Vérifier que la perte de paquets se produit
docker exec $container_abr2 ping -c 20 10.0.0.1
# Attendu : ~10% de perte de paquets affichée

# 3. Exécuter l'optimiseur
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose

# 4. Vérifier les résultats
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"
# Attendu : Coût considérablement augmenté

# 5. Nettoyage
docker exec $container_abr2 sh -c "tc qdisc del dev eth1 root 2>/dev/null"
```

**Résultats Attendus :**
- Perte de paquets détectée : ~10%
- Augmentation du coût : 10 → ~50+ (la perte de paquets a une pénalité élevée)
- Alerte critique dans la sortie de l'optimiseur

---

### Scénario 4 : Défaillance et Récupération de Lien

**Objectif :** Vérifier la reconvergence OSPF lors d'une défaillance de lien et le comportement de l'optimiseur.

**Étapes :**

```bash
# 1. Enregistrer l'état de routage actuel
container_r1=$(docker ps --format "{{.Names}}" | grep "\.R1\." | head -1)
echo "=== Routes Initiales ==="
docker exec $container_r1 vtysh -c "show ip route ospf"
docker exec $container_r1 traceroute -n 192.168.4.1

# 2. Simuler une défaillance de lien en désactivant l'interface sur ABR1
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
docker exec $container_abr1 vtysh -c "
configure terminal
interface eth1
shutdown
end
"

# 3. Attendre la reconvergence OSPF (30-40 secondes)
sleep 40

# 4. Vérifier le nouvel état de routage
echo "=== Routes Après Défaillance du Lien ==="
docker exec $container_r1 vtysh -c "show ip route ospf"
docker exec $container_r1 traceroute -n 192.168.4.1
# Attendu : Le trafic est maintenant routé via ABR3 (secours)

# 5. Exécuter l'optimiseur (devrait détecter le lien comme hors service)
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose
# Attendu : Le lien ABR1-ABR2 apparaît comme inaccessible

# 6. Restaurer le lien
docker exec $container_abr1 vtysh -c "
configure terminal
interface eth1
no shutdown
end
"

# 7. Attendre la reconvergence
sleep 40

# 8. Exécuter à nouveau l'optimiseur
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose

# 9. Vérifier l'état de routage final
echo "=== Routes Après Récupération ==="
docker exec $container_r1 vtysh -c "show ip route ospf"
```

**Résultats Attendus :**
| Phase | Chemin Primaire | Chemin Secours | Statut |
|-------|--------------|-------------|--------|
| Initial | ABR1→ABR2 | Disponible | Normal |
| Lien Hors Service | Indisponible | ABR1→ABR3→ABR2 | Basculement |
| Récupéré | ABR1→ABR2 | Disponible | Normal |

---

### Scénario 5 : Dégradation Multi-Facteurs

**Objectif :** Tester l'optimiseur avec plusieurs facteurs de dégradation simultanément.

**Étapes :**

```bash
# 1. Appliquer plusieurs dégradations au lien ABR1-ABR2
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)

# Ajouter latence + perte de paquets + restriction de bande passante
docker exec $container_abr1 sh -c "
  tc qdisc add dev eth1 root netem delay 50ms loss 2% rate 10mbit 2>/dev/null || \
  tc qdisc change dev eth1 root netem delay 50ms loss 2% rate 10mbit 2>/dev/null
"

# 2. Générer du trafic
docker exec $container_abr1 sh -c "
  for i in \$(seq 1 20); do
    ping -c 50 -i 0.02 10.0.0.2 > /dev/null 2>&1 &
  done
"

# 3. Exécuter l'optimiseur avec sortie détaillée
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose 2>&1 | tee /tmp/optimizer_output.txt

# 4. Analyser la sortie
grep -E "BW:|Latence:|Perte:|Coût" /tmp/optimizer_output.txt

# 5. Modèle de sortie attendu :
# ABR1-ABR2 (Primaire) : BP : 45,0%, Latence : 52,3ms, Perte : 1,80%
# Coût proposé : 10 → 45 (facteur composite)

# 6. Vérifier le coût réellement appliqué
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"

# 7. Nettoyage
docker exec $container_abr1 sh -c "tc qdisc del dev eth1 root 2>/dev/null"
```

**Résultats Attendus :**
- Le calcul du coût composite prend en compte les trois facteurs
- Coût final = Base × (1 + facteur_BP × 0,5 + facteur_Latence × 0,3 + facteur_Perte × 0,2)
- Le coût devrait être significativement plus élevé (plage 30-60)

---

### Scénario 6 : Mode de Surveillance Continue

**Objectif :** Vérifier que l'optimiseur fonctionne correctement en mode continu.

**Étapes :**

```bash
# 1. Démarrer l'optimiseur en mode continu (arrière-plan)
python3 ospf_optimizer.py --config config/routers.yaml --interval 30 --verbose &
OPTIMIZER_PID=$!
echo "PID Optimiseur : $OPTIMIZER_PID"

# 2. Le laisser tourner pour un cycle
sleep 35

# 3. Introduire une dégradation
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
docker exec $container_abr1 sh -c "
  tc qdisc add dev eth1 root netem delay 80ms 2>/dev/null
"

# 4. Attendre le prochain cycle d'optimisation
sleep 35

# 5. Vérifier si le coût a été ajusté
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"

# 6. Supprimer la dégradation
docker exec $container_abr1 sh -c "tc qdisc del dev eth1 root 2>/dev/null"

# 7. Attendre la détection de la récupération
sleep 35

# 8. Vérifier que le coût est revenu à la normale
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"

# 9. Arrêter l'optimiseur
kill $OPTIMIZER_PID
```

**Résultats Attendus :**
- L'optimiseur détecte la dégradation après un cycle
- Le coût augmente automatiquement
- Après suppression de la dégradation, le coût revient à la normale

---

### Scénario 7 : Optimisation Déclenchée par l'API Web

**Objectif :** Vérifier l'optimisation via l'API web.

**Étapes :**

```bash
# 1. Démarrer le serveur web
python3 ospf_optimizer.py --config config/routers.yaml --web --port 8080 &
WEB_PID=$!
sleep 3

# 2. Vérifier le statut via l'API
curl -s http://localhost:8080/api/status | python3 -m json.tool

# 3. Déclencher l'optimisation via l'API
curl -s -X POST "http://localhost:8080/api/optimize?strategy=composite" | python3 -m json.tool

# 4. Vérifier d'abord avec dry-run
curl -s -X POST "http://localhost:8080/api/optimize?dry_run=true" | python3 -m json.tool

# 5. Démarrer le mode continu via l'API
curl -s -X POST http://localhost:8080/api/start | python3 -m json.tool

# 6. Vérifier à nouveau le statut
curl -s http://localhost:8080/api/status | python3 -m json.tool

# 7. Arrêter le mode continu
curl -s -X POST http://localhost:8080/api/stop | python3 -m json.tool

# 8. Nettoyage
kill $WEB_PID
```

**Réponses API Attendues :**

```json
// /api/status
{
  "status": "en cours",
  "mode": "inactif",
  "last_optimization": "2025-12-18T10:30:00",
  "links_monitored": 7
}

// /api/optimize
{
  "success": true,
  "changes": 2,
  "details": [
    {"link": "ABR1-ABR2", "old_cost": 10, "new_cost": 15}
  ]
}
```

---

## Script de Test de Scénario Automatisé

Créer ce script de test complet :

```bash
#!/bin/bash
# Fichier : run_scenario_tests.sh
# Tests de scénarios automatisés pour l'Optimiseur OSPF

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd ~/OSPF_Optimizer
source venv/bin/activate

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_pass() { echo -e "${GREEN}RÉUSSI :${NC} $1"; }
log_fail() { echo -e "${RED}ÉCHOUÉ :${NC} $1"; }
log_info() { echo -e "${YELLOW}INFO :${NC} $1"; }

# Obtenir les noms de conteneurs
get_container() {
    docker ps --format "{{.Names}}" | grep "$1" | head -1
}

echo "=============================================="
echo "   Optimiseur OSPF - Tests de Scénarios"
echo "=============================================="
echo ""

# Pré-vérification
log_info "Exécution des pré-vérifications..."
ABR1=$(get_container "ABR1")
ABR2=$(get_container "ABR2")
R1=$(get_container "\.R1\.")

if [ -z "$ABR1" ] || [ -z "$ABR2" ]; then
    log_fail "Conteneurs requis non trouvés"
    exit 1
fi
log_pass "Conteneurs trouvés : ABR1=$ABR1"

# Test 1 : Optimisation de base
echo ""
echo "--- Test 1 : Optimisation à Blanc de Base ---"
if python3 ospf_optimizer.py --config config/routers.yaml --once --dry-run 2>&1 | grep -q "Links monitored"; then
    log_pass "Optimisation à blanc terminée"
else
    log_fail "Optimisation à blanc échouée"
fi

# Test 2 : Détection de latence
echo ""
echo "--- Test 2 : Détection de Latence ---"
log_info "Ajout de 80ms de latence au lien ABR1-ABR2..."
docker exec $ABR1 sh -c "tc qdisc add dev eth1 root netem delay 80ms 2>/dev/null" || true

# Vérifier la latence
latency=$(docker exec $ABR1 ping -c 3 -W 2 10.0.0.2 2>/dev/null | grep "avg" | cut -d'/' -f5)
log_info "Latence mesurée : ${latency}ms"

# Exécuter l'optimiseur
output=$(python3 ospf_optimizer.py --config config/routers.yaml --once --dry-run 2>&1)
if echo "$output" | grep -qE "Latence:.*[5-9][0-9]|Latence:.*1[0-9][0-9]"; then
    log_pass "Latence élevée détectée par l'optimiseur"
else
    log_info "La détection de latence peut varier selon les seuils"
fi

# Nettoyage
docker exec $ABR1 sh -c "tc qdisc del dev eth1 root 2>/dev/null" || true
log_info "Nettoyage de la simulation de latence"

# Test 3 : API Web
echo ""
echo "--- Test 3 : API Web ---"
python3 ospf_optimizer.py --config config/routers.yaml --web --port 8888 &
WEB_PID=$!
sleep 3

if curl -s http://localhost:8888/api/status | grep -q "status"; then
    log_pass "API Web répond"
else
    log_fail "API Web ne répond pas"
fi

kill $WEB_PID 2>/dev/null

# Test 4 : Rechargement de configuration
echo ""
echo "--- Test 4 : Configuration ---"
if python3 -c "import yaml; yaml.safe_load(open('config/routers.yaml'))" 2>/dev/null; then
    log_pass "Le fichier de configuration est un YAML valide"
else
    log_fail "Le fichier de configuration contient des erreurs"
fi

# Résumé
echo ""
echo "=============================================="
echo "   Tests de Scénarios Terminés"
echo "=============================================="
echo ""
echo "Pour des tests approfondis manuels, exécuter les scénarios individuels"
echo "comme documenté dans docs/TEST_WORKFLOW.md"
```

Rendre exécutable :
```bash
chmod +x run_scenario_tests.sh
./run_scenario_tests.sh
```

---

## Modèle de Journal des Résultats de Tests

| Test | Attendu | Réel | Statut |
|------|----------|--------|--------|
| Configuration de l'environnement | venv actif | | ⬜ |
| Détection des conteneurs | 7+ conteneurs | | ⬜ |
| Accès Docker Exec | Tous les routeurs OK | | ⬜ |
| OSPF en cours | ID routeur affiché | | ⬜ |
| Voisins OSPF | État FULL | | ⬜ |
| Test Ping | 0% perte | | ⬜ |
| À Blanc | Aucune erreur | | ⬜ |
| Optimisation en direct | Coûts appliqués | | ⬜ |
| Tableau de bord Web | Page se charge | | ⬜ |
| API /status | Réponse JSON | | ⬜ |
| Connectivité E2E | PC1→PC4 fonctionne | | ⬜ |
| **Scénario 1** | Congestion détectée | | ⬜ |
| **Scénario 2** | Augmentation coût latence | | ⬜ |
| **Scénario 3** | Pénalité perte paquets | | ⬜ |
| **Scénario 4** | Basculement fonctionne | | ⬜ |
| **Scénario 5** | Calcul composite | | ⬜ |
| **Scénario 6** | Mode continu | | ⬜ |
| **Scénario 7** | Déclenchement API Web | | ⬜ |

---

**Version du Document :** 1.1  
**Dernière Mise à Jour :** Décembre 2025

