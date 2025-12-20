# Prompt pour Générer une Présentation OSPF Optimizer

Utilisez ce prompt avec un agent IA (ChatGPT, Claude, Copilot, etc.) pour générer une présentation PowerPoint détaillée.

---

## 🎯 PROMPT À COPIER

```
Génère une présentation PowerPoint professionnelle et détaillée (15-20 slides) pour un projet de fin d'études intitulé "OSPF Optimizer" - un outil d'optimisation dynamique des coûts OSPF basé sur les métriques réseau en temps réel.

## INFORMATIONS DU PROJET

### Contexte et Problématique
- Les réseaux OSPF traditionnels utilisent des coûts statiques basés uniquement sur la bande passante
- Ces coûts ne reflètent pas les conditions réseau réelles (latence, congestion, pertes)
- Résultat : routage sous-optimal, congestion non détectée, pas d'adaptation automatique

### Solution Proposée
OSPF Optimizer est un outil Python qui :
1. Collecte les métriques réseau en temps réel (latence, bande passante, perte de paquets)
2. Calcule dynamiquement les coûts OSPF optimaux
3. Applique automatiquement les changements sur les routeurs FRRouting
4. Fournit une interface web pour la visualisation et le contrôle

### Architecture Technique

#### Stack Technologique
- **Langage** : Python 3.10+
- **Routeurs** : FRRouting (FRR) dans conteneurs Docker
- **Simulation** : GNS3 avec topologie multi-zones OSPF
- **Interface Web** : Flask + HTML/CSS/JavaScript
- **Configuration** : YAML

#### Modules Principaux
1. **router_connection.py** : Connexion aux routeurs via Docker exec + vtysh
2. **metrics_collector.py** : Collecte des métriques (ping, statistiques interfaces)
3. **cost_calculator.py** : Algorithmes de calcul des coûts (composite, latency, bandwidth)
4. **web_interface.py** : Dashboard web temps réel avec API REST
5. **ospf_optimizer.py** : Orchestrateur principal
6. **auto_start.py** : Détection automatique des conteneurs GNS3

### Topologie Réseau de Test
```
                    ┌─────────────────────────────────────┐
                    │           AREA 0 (Backbone)         │
                    │                                     │
    AREA 1          │    ABR1 ──────────── ABR2          │         AREA 2
    ┌───────────┐   │     │ \            / │             │   ┌───────────┐
    │ R1 ── PC1 │───│─────┘  \          /  └─────────────│───│ R3 ── PC3 │
    │ R2 ── PC2 │───│─────────ABR3─────┘                 │───│ R4 ── PC4 │
    └───────────┘   │                                     │   └───────────┘
                    └─────────────────────────────────────┘

- 7 routeurs FRRouting (ABR1, ABR2, ABR3, R1, R2, R3, R4)
- 4 PCs Alpine Linux (PC1, PC2, PC3, PC4)
- 3 zones OSPF (Area 0, Area 1, Area 2)
```

### Algorithme de Calcul des Coûts

#### Stratégie Composite (par défaut)
```
cost = base_cost × (bw_factor × 0.5 + latency_factor × 0.3 + loss_factor × 0.2)
```

#### Facteurs de Pénalité
| Métrique | Normal | Moyen | Élevé | Critique |
|----------|--------|-------|-------|----------|
| Latence | <10ms | <50ms | <100ms | >200ms |
| Bande passante | <30% | <60% | <80% | >90% |
| Perte paquets | <0.1% | <1% | <5% | >10% |

### Fonctionnalités Clés

1. **Détection Automatique** : Découverte des conteneurs Docker GNS3
2. **Multi-Stratégies** : composite, latency-only, bandwidth-only
3. **Mode Dry-Run** : Test sans modification
4. **Dashboard Web** : Visualisation temps réel, déclenchement manuel
5. **API REST** : /api/status, /api/optimize, /api/start, /api/stop
6. **Anti-Oscillation** : Seuil minimum de changement pour éviter le flapping

### Scénario de Démonstration Réussi

#### Test de Congestion (100ms de délai ajouté)
| Étape | Action | Résultat |
|-------|--------|----------|
| 1 | État initial | Route via ABR2, latence 2ms |
| 2 | Ajout 100ms délai sur ABR1-ABR2 | Latence mesurée 101ms |
| 3 | Optimisation déclenchée | Coût ABR1-ABR2 : 15 → 68 |
| 4 | Rerouting automatique | Route via ABR3 |
| 5 | Test trafic PC1→PC3 | Latence 1.4ms (évite lien congestionné!) |
| 6 | Suppression délai | Latence normale |
| 7 | Optimisation inverse | Coût restauré : 68 → 15 |
| 8 | Route rétablie | Retour via ABR2 |

### Résultats et Métriques

- **Temps de détection** : ~35 secondes par cycle
- **Précision mesure latence** : ±1ms
- **Réactivité rerouting** : <5 secondes après changement coût
- **Nombre de routeurs supportés** : Testé avec 7, extensible

### Points Forts du Projet

1. **Automatisation complète** : Pas d'intervention manuelle requise
2. **Intégration GNS3/Docker** : Environnement de test réaliste
3. **Extensibilité** : Architecture modulaire, facile à étendre
4. **Interface utilisateur** : Dashboard web intuitif
5. **Open Source** : Code Python maintenable

### Améliorations Futures

1. Support SNMP pour routeurs physiques
2. Machine Learning pour prédiction de congestion
3. Intégration Prometheus/Grafana
4. Support multi-protocoles (BGP, EIGRP)
5. Haute disponibilité (clustering)

### Technologies et Compétences Démontrées

- Réseaux : OSPF, routage dynamique, métriques
- Virtualisation : Docker, GNS3
- Programmation : Python, Flask, API REST
- DevOps : Automatisation, scripting
- Linux : FRRouting, commandes réseau

## FORMAT DE LA PRÉSENTATION

### Structure des Slides
1. **Page de titre** : Titre, auteur, date, logo université
2. **Sommaire** : Plan de la présentation
3. **Contexte et problématique** : 2 slides
4. **Objectifs du projet** : 1 slide
5. **Architecture technique** : 2-3 slides avec diagrammes
6. **Topologie réseau** : 1 slide avec schéma
7. **Modules et code** : 2-3 slides
8. **Algorithmes** : 2 slides avec formules
9. **Interface web** : 1-2 slides avec captures d'écran
10. **Démonstration** : 2-3 slides avec résultats des tests
11. **Résultats et métriques** : 1 slide
12. **Conclusion** : 1 slide
13. **Perspectives** : 1 slide
14. **Questions** : 1 slide

### Style Visuel
- Thème moderne et professionnel
- Couleurs : Bleu foncé (#1a1a2e), Cyan (#00d4ff), Blanc
- Icônes pour les points clés
- Diagrammes et schémas techniques
- Code snippets avec coloration syntaxique
- Animations subtiles pour les transitions

### Informations Auteur
- Nom : [À COMPLÉTER]
- Formation : [À COMPLÉTER]  
- Établissement : [À COMPLÉTER]
- Encadrant : [À COMPLÉTER]
- Date : Décembre 2025
```

---

## 📋 INFORMATIONS COMPLÉMENTAIRES À FOURNIR

Ajoutez ces informations personnelles au prompt :

```
INFORMATIONS PERSONNELLES :
- Nom complet : 
- Filière/Formation : 
- Université/École : 
- Année académique : 2024-2025
- Encadrant(s) : 
- Module/Cours : 
```

---

## 🖼️ CAPTURES D'ÉCRAN À INCLURE

Pour une meilleure présentation, prenez ces captures :

1. **Dashboard Web** : Interface principale sur http://localhost:8080
2. **Terminal** : Sortie de `python3 ospf_optimizer.py --verbose`
3. **GNS3** : Vue de la topologie réseau
4. **Résultats** : Avant/après optimisation (`show ip route`)
5. **Code** : Extrait du module principal

---

## 🎬 SCRIPT DÉMONSTRATION LIVE (optionnel)

Si vous faites une démo en direct :

```bash
# 1. Montrer l'état initial
docker exec GNS3.ABR1.xxx vtysh -c "show ip route 192.168.3.0"

# 2. Démarrer le dashboard
python3 src/web_interface.py --port 8080 --config config/routers.yaml

# 3. Simuler congestion
docker exec GNS3.ABR1.xxx tc qdisc add dev eth1 root netem delay 100ms

# 4. Déclencher optimisation (via web ou CLI)
python3 ospf_optimizer.py --config config/routers.yaml --strategy latency --once

# 5. Vérifier le rerouting
docker exec GNS3.ABR1.xxx vtysh -c "show ip route 192.168.3.0"

# 6. Tester le trafic
docker exec GNS3.PC1.xxx ping -c 5 192.168.3.10

# 7. Supprimer la congestion (retour à l'état normal)
docker exec GNS3.ABR1.xxx tc qdisc del dev eth1 root

# 8. Vérifier que la latence est revenue à la normale entre ABR1 et ABR2
docker exec GNS3.ABR1.xxx ping -c 5 <IP_ABR2>

# 9. Relancer l'optimisation pour restaurer les coûts
python3 ospf_optimizer.py --config config/routers.yaml --strategy latency --once

# 10. Vérifier que le lien ABR1-ABR2 est de nouveau utilisé
docker exec GNS3.ABR1.xxx vtysh -c "show ip route 192.168.3.0"
docker exec GNS3.ABR1.xxx vtysh -c "show ip ospf interface"
```

---

## 📚 RÉFÉRENCES SUGGÉRÉES

- RFC 2328 - OSPF Version 2
- FRRouting Documentation (https://docs.frrouting.org)
- GNS3 Documentation (https://docs.gns3.com)
- Flask Documentation (https://flask.palletsprojects.com)
