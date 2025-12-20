# Rapport de Projet : OSPF Optimizer
## Ajustement Dynamique des Coûts OSPF basé sur les Métriques Réseau en Temps Réel

---

**Auteur :** [Votre Nom]  
**Établissement :** [Nom de l'Établissement]  
**Formation :** [Nom de la Formation]  
**Encadrant :** [Nom de l'Encadrant]  
**Date :** Décembre 2025  
**Version :** 2.0  

---

## Résumé Exécutif

Ce rapport présente le développement complet d'une solution d'optimisation dynamique du protocole OSPF (Open Shortest Path First). Le système conçu permet d'ajuster automatiquement les coûts des liens OSPF en fonction de métriques réseau collectées en temps réel : utilisation de la bande passante, latence et taux de perte de paquets.

L'architecture repose sur une infrastructure virtualisée utilisant GNS3 et Docker, avec des routeurs FRRouting. Un orchestrateur Python collecte les métriques, calcule les coûts optimaux selon différentes stratégies, et applique les modifications via l'interface vtysh.

**Mots-clés :** OSPF, Routage dynamique, QoS, Optimisation réseau, FRRouting, Docker, GNS3, Python, Métriques temps réel

---

## Table des Matières

1. [Introduction](#1-introduction)
  - 1.1 Contexte général
  - 1.2 Présentation du protocole OSPF
  - 1.3 Problématique identifiée
  - 1.4 Objectifs du projet
  - 1.5 Périmètre et contraintes
  - 1.6 Organisation du rapport

2. [État de l'Art](#2-état-de-lart)
  - 2.1 Le protocole OSPF en détail
  - 2.2 Limitations du routage statique
  - 2.3 Solutions existantes
  - 2.4 Positionnement du projet

3. [Analyse et Spécifications](#3-analyse-et-spécifications)
  - 3.1 Analyse des besoins fonctionnels
  - 3.2 Analyse des besoins non fonctionnels
  - 3.3 Cas d'utilisation
  - 3.4 Diagrammes de séquence

4. [Conception](#4-conception)
  - 4.1 Architecture réseau détaillée
  - 4.2 Topologie OSPF multi-zones
  - 4.3 Architecture logicielle
  - 4.4 Modèle de données
  - 4.5 Algorithmes d'optimisation
  - 4.6 Choix technologiques justifiés

5. [Environnement Technique](#5-environnement-technique)
  - 5.1 Infrastructure matérielle
  - 5.2 Infrastructure de virtualisation
  - 5.3 Pile technologique
  - 5.4 Outils de développement

6. [Implémentation](#6-implémentation)
  - 6.1 Structure détaillée du projet
  - 6.2 Module de connexion aux routeurs
  - 6.3 Collecteur de métriques
  - 6.4 Calculateur de coûts OSPF
  - 6.5 Interface web et API REST
  - 6.6 Script de démarrage automatique
  - 6.7 Gestion des erreurs et logging

7. [Configuration](#7-configuration)
  - 7.1 Configuration des routeurs FRRouting
  - 7.2 Fichier de configuration YAML
  - 7.3 Paramètres de seuils
  - 7.4 Facteurs de pondération

8. [Tests et Validation](#8-tests-et-validation)
  - 8.1 Stratégie de test
  - 8.2 Tests unitaires
  - 8.3 Tests d'intégration
  - 8.4 Scénarios de test réseau
  - 8.5 Résultats et analyse
  - 8.6 Benchmarks de performance

9. [Guide d'Utilisation](#9-guide-dutilisation)
  - 9.1 Prérequis système
  - 9.2 Installation pas à pas
  - 9.3 Configuration initiale
  - 9.4 Modes d'exécution
  - 9.5 Interface web
  - 9.6 Dépannage

10. [Conclusion et Perspectives](#10-conclusion-et-perspectives)
   - 10.1 Bilan du projet
   - 10.2 Objectifs atteints
   - 10.3 Difficultés rencontrées et solutions
   - 10.4 Améliorations futures
   - 10.5 Réflexions personnelles

11. [Annexes](#11-annexes)
   - A. Table d'adressage IP complète
   - B. Configuration FRRouting des routeurs
   - C. Code source des modules principaux
   - D. Commandes utiles
   - E. Glossaire
   - F. Références bibliographiques

---

## 1. Introduction

### 1.1 Contexte Général

Dans le paysage actuel des réseaux d'entreprise, la demande en bande passante ne cesse de croître. Les applications modernes — visioconférence, services cloud, IoT, streaming — génèrent des flux de données imprévisibles et variables. Face à cette réalité, les infrastructures réseau doivent être capables de s'adapter dynamiquement pour garantir une qualité de service optimale.

Le routage, pierre angulaire de toute architecture réseau, détermine les chemins empruntés par les données. Historiquement, les protocoles de routage comme OSPF ont été conçus avec une vision relativement statique : les métriques de routage sont définies une fois et rarement modifiées. Cette approche, bien que robuste et prévisible, montre ses limites dans des environnements où les conditions de trafic évoluent rapidement.

Ce projet s'inscrit dans une démarche d'**ingénierie réseau proactive**, visant à transformer le routage OSPF d'un système réactif en un système adaptatif capable d'optimiser en continu les chemins réseau.

### 1.2 Présentation du Protocole OSPF

#### 1.2.1 Historique et Standardisation

OSPF (Open Shortest Path First) est un protocole de routage interne (IGP - Interior Gateway Protocol) standardisé par l'IETF. La version 2, définie par la RFC 2328 en 1998, reste la plus utilisée dans les réseaux IPv4. OSPF fait partie de la famille des protocoles à état de liens (Link-State), par opposition aux protocoles à vecteur de distance comme RIP.

**Chronologie d'OSPF :**
- **1989** : Première version d'OSPF (RFC 1131)
- **1991** : OSPFv1 (RFC 1247)
- **1994** : OSPFv2 (RFC 1583)
- **1998** : OSPFv2 mise à jour (RFC 2328) - Version actuelle
- **1999** : OSPFv3 pour IPv6 (RFC 2740)

#### 1.2.2 Principes Fondamentaux

OSPF repose sur l'algorithme de Dijkstra (Shortest Path First) pour calculer l'arbre des plus courts chemins vers chaque destination. Chaque routeur OSPF :

1. **Découvre ses voisins** via le protocole Hello
2. **Établit des adjacences** avec certains voisins
3. **Échange des LSA** (Link-State Advertisements) pour construire une base de données topologique
4. **Calcule les meilleurs chemins** avec l'algorithme SPF
5. **Peuple sa table de routage** avec les résultats

**Caractéristiques principales :**

| Caractéristique | Valeur |
|-----------------|--------|
| Type de protocole | Link-State (IGP) |
| Algorithme | Dijkstra (SPF) |
| Métrique | Coût (basé sur la bande passante) |
| Support VLSM | Oui (Classless) |
| Convergence | Rapide (< 1 seconde typiquement) |
| Hiérarchie | Zones (Areas) |
| Transport | IP directement (protocole 89) |
| Authentification | Texte clair, MD5, SHA |

#### 1.2.3 Calcul du Coût OSPF

Le coût OSPF est la métrique utilisée pour déterminer le meilleur chemin. Par défaut, il est calculé selon la formule :

$$\text{Coût OSPF} = \frac{\text{Bande passante de référence}}{\text{Bande passante de l'interface}}$$

**Exemple avec une bande passante de référence de 100 Mbps :**

| Type d'interface | Bande passante | Coût calculé |
|------------------|----------------|--------------|
| Fast Ethernet | 100 Mbps | 1 |
| Ethernet | 10 Mbps | 10 |
| Gigabit Ethernet | 1 Gbps | 1 (arrondi) |
| 10 Gigabit Ethernet | 10 Gbps | 1 (arrondi) |
| Série 1.544 Mbps | 1.544 Mbps | 64 |
| Série 64 Kbps | 64 Kbps | 1562 |

**Problème identifié :** Avec les vitesses modernes (1 Gbps, 10 Gbps, 100 Gbps), le coût calculé est systématiquement 1, ce qui ne permet pas de différencier les liens. Solution courante : augmenter la bande passante de référence (ex: 10 Gbps ou 100 Gbps).

#### 1.2.4 Structure Hiérarchique en Zones

OSPF utilise une architecture hiérarchique basée sur des **zones** (Areas) pour :
- Réduire la taille des bases de données topologiques
- Limiter la propagation des LSA
- Accélérer la convergence
- Permettre la summarisation des routes

**Types de zones OSPF :**

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│                              AREA 0                                    │
│                            (Backbone)                                  │
│                                                                        │
│    Obligatoire - Toutes les autres zones doivent y être connectées    │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   AREA N     │  │  STUB AREA   │  │TOTALLY STUB  │  │    NSSA    │ │
│  │  (Normale)   │  │              │  │    AREA      │  │            │ │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├────────────┤ │
│  │ Tous les LSA │  │ Pas de LSA   │  │ Pas de LSA   │  │ LSA type 7 │ │
│  │ sont permis  │  │ externes     │  │ externes ni  │  │ convertis  │ │
│  │              │  │ (type 5)     │  │ inter-zone   │  │ en type 5  │ │
│  │              │  │              │  │ (types 3,4,5)│  │            │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

**Types de routeurs OSPF :**

| Type | Description | Caractéristiques |
|------|-------------|------------------|
| **Internal Router** | Toutes les interfaces dans une seule zone | Base de données unique |
| **Backbone Router** | Au moins une interface dans l'Area 0 | Participe au backbone |
| **ABR** (Area Border Router) | Interfaces dans plusieurs zones | Résume les routes entre zones |
| **ASBR** (AS Boundary Router) | Redistribue des routes externes | Injecte des routes non-OSPF |

### 1.3 Problématique Identifiée

#### 1.3.1 Limitations du Calcul Statique des Coûts

Le calcul traditionnel du coût OSPF présente plusieurs limitations fondamentales :

**1. Ignorance des conditions temps réel**

Le coût est calculé uniquement à partir de la bande passante nominale de l'interface, sans considérer :
- L'utilisation réelle de cette bande passante
- La latence effective des communications
- Le taux de perte de paquets
- La gigue (jitter)
- L'état de santé général du lien

**2. Absence d'adaptation dynamique**

Une fois configuré, le coût OSPF reste constant jusqu'à modification manuelle ou échec du lien. Le protocole ne réagit pas aux variations de performance.

**3. Problème de congestion**

Considérons le scénario suivant :

```
      Lien A (1 Gbps)
   R1 ─────────────────── R3
    │                      │
    │   Lien B (1 Gbps)    │
    └──────── R2 ──────────┘
```

Si les deux liens ont la même bande passante, ils auront le même coût OSPF. Tout le trafic empruntera un seul chemin (ou sera réparti équitablement avec ECMP). Si le lien A devient congestionné :
- OSPF continue d'utiliser le lien A avec le même coût
- Le lien B reste sous-utilisé
- La qualité de service se dégrade

**4. Inadaptation aux applications modernes**

Les applications temps réel (VoIP, vidéo) sont sensibles à la latence et à la perte de paquets, pas uniquement à la bande passante. Le coût OSPF traditionnel ne capture pas ces paramètres critiques.

#### 1.3.2 Formulation du Problème

**Question de recherche :**

> Comment concevoir un système capable d'ajuster automatiquement les coûts OSPF en fonction des métriques réseau temps réel, afin d'optimiser l'utilisation des ressources et la qualité de service ?

**Sous-questions :**

1. Quelles métriques sont pertinentes pour évaluer la qualité d'un lien ?
2. Comment collecter ces métriques de manière fiable et non intrusive ?
3. Quel algorithme utiliser pour traduire ces métriques en coûts OSPF ?
4. Comment appliquer les modifications sans perturber le réseau ?
5. Comment valider l'efficacité de l'optimisation ?

### 1.4 Objectifs du Projet

#### 1.4.1 Objectif Principal

Développer un système d'optimisation dynamique des coûts OSPF capable de :
- Collecter les métriques réseau en temps réel
- Analyser ces métriques pour identifier les liens dégradés
- Calculer des coûts OSPF optimisés
- Appliquer automatiquement ces modifications sur les routeurs

#### 1.4.2 Objectifs Spécifiques

| ID | Objectif | Critère de succès |
|----|----------|-------------------|
| O1 | Mettre en place un environnement de simulation OSPF multi-zones | Topologie fonctionnelle avec adjacences établies |
| O2 | Développer un collecteur de métriques réseau | Collecte de latence, perte de paquets, bande passante |
| O3 | Implémenter un algorithme de calcul de coût dynamique | Prise en compte pondérée des 3 métriques |
| O4 | Créer un module d'application des configurations | Modification effective des coûts via vtysh |
| O5 | Développer une interface de monitoring | Dashboard web fonctionnel |
| O6 | Automatiser le déploiement | Script de démarrage automatique |
| O7 | Valider le système par des tests | Scénarios de congestion, latence, perte |

#### 1.4.3 Livrables Attendus

1. **Code source complet** du système d'optimisation
2. **Documentation technique** détaillée
3. **Guide d'installation** et d'utilisation
4. **Rapport de projet** (ce document)
5. **Démonstration fonctionnelle** du système

### 1.5 Périmètre et Contraintes

#### 1.5.1 Périmètre Inclus

- ✅ Réseau OSPF multi-zones (Area 0, 1, 2)
- ✅ 7 routeurs FRRouting en conteneurs Docker
- ✅ 4 hôtes finaux (PCs) pour les tests
- ✅ Environnement de simulation GNS3
- ✅ Collecte de métriques via ping et parsing système
- ✅ Application automatique des coûts via vtysh
- ✅ Dashboard web de monitoring
- ✅ 3 stratégies d'optimisation (composite, bande passante, latence)

#### 1.5.2 Périmètre Exclu

- ❌ Support OSPFv3 (IPv6)
- ❌ Intégration avec des équipements physiques
- ❌ Support d'autres protocoles de routage (IS-IS, EIGRP, BGP)
- ❌ Haute disponibilité du système d'optimisation
- ❌ Authentification OSPF
- ❌ Support des VRF

#### 1.5.3 Contraintes Techniques

| Contrainte | Description |
|------------|-------------|
| Environnement | Linux Ubuntu 22.04 LTS |
| Virtualisation | Docker + GNS3 |
| Langage | Python 3.10+ |
| Routage | FRRouting v8.x |
| Accès routeurs | docker exec (pas de SSH) |

#### 1.5.4 Contraintes Temporelles

- Durée du projet : [X semaines/mois]
- Jalons intermédiaires définis selon la planification

### 1.6 Organisation du Rapport

Ce rapport est structuré en 11 chapitres :

- **Chapitres 1-2** : Introduction et État de l'Art — Contexte, problématique et solutions existantes
- **Chapitres 3-4** : Analyse et Conception — Spécifications et architecture
- **Chapitres 5-6** : Technique et Implémentation — Environnement et développement
- **Chapitres 7-8** : Configuration et Tests — Paramétrage et validation
- **Chapitre 9** : Guide d'Utilisation — Manuel utilisateur
- **Chapitre 10** : Conclusion — Bilan et perspectives
- **Chapitre 11** : Annexes — Ressources complémentaires

---

## 2. État de l'Art

### 2.1 Le Protocole OSPF en Détail

#### 2.1.1 Fonctionnement du Protocole Hello

Le protocole Hello est le mécanisme de découverte et de maintien des voisins OSPF. Les paquets Hello sont envoyés périodiquement sur chaque interface OSPF.

**Paramètres du protocole Hello :**

| Paramètre | Valeur par défaut | Description |
|-----------|-------------------|-------------|
| Hello Interval | 10 secondes | Fréquence d'envoi des Hello |
| Dead Interval | 40 secondes | Temps avant déclaration de panne |
| Wait Timer | Dead Interval | Attente pour élection DR/BDR |
| Retransmit Interval | 5 secondes | Délai de retransmission LSA |

**Conditions pour établir une adjacence :**
- Même Area ID
- Même Hello Interval et Dead Interval
- Même type de réseau
- Même masque de sous-réseau (sauf point-to-point)
- Authentification compatible

#### 2.1.2 Types de LSA (Link-State Advertisements)

Les LSA sont les messages qui décrivent la topologie du réseau :

| Type | Nom | Portée | Description |
|------|-----|--------|-------------|
| 1 | Router LSA | Intra-zone | Décrit les liens du routeur |
| 2 | Network LSA | Intra-zone | Décrit un réseau multi-accès |
| 3 | Summary LSA | Inter-zone | Routes vers autres zones (par ABR) |
| 4 | ASBR Summary | Inter-zone | Chemin vers un ASBR |
| 5 | External LSA | Domaine | Routes redistribuées externes |
| 7 | NSSA External | NSSA zone | Routes externes en zone NSSA |

#### 2.1.3 L'Algorithme SPF (Dijkstra)

L'algorithme de Dijkstra calcule le chemin le plus court depuis le routeur local vers toutes les destinations :

```
Algorithme SPF simplifié :
─────────────────────────
1. Initialiser :
  - Distance vers soi-même = 0
  - Distance vers tous les autres = ∞
  - Ensemble des nœuds visités = {}

2. Répéter jusqu'à ce que tous les nœuds soient visités :
  a. Sélectionner le nœud non visité avec la plus petite distance
  b. Le marquer comme visité
  c. Pour chaque voisin non visité :
    - Calculer distance = distance_actuelle + coût_lien
    - Si distance < distance_connue : mettre à jour

3. Résultat : arbre des plus courts chemins
```

**Complexité algorithmique :**
- Avec une file de priorité simple : O(V²)
- Avec un tas binaire : O((V + E) log V)
- Avec un tas de Fibonacci : O(E + V log V)

Où V = nombre de routeurs, E = nombre de liens

### 2.2 Limitations du Routage Statique

#### 2.2.1 Analyse des Faiblesses

**1. Réactivité insuffisante**

Le routage OSPF traditionnel ne réagit qu'aux changements topologiques (liens up/down), pas aux changements de performance.

```
Scénario : Dégradation progressive d'un lien
─────────────────────────────────────────────
T0 : Lien A → 0% utilisation, 1ms latence    → Coût = 10
T1 : Lien A → 50% utilisation, 5ms latence   → Coût = 10 (inchangé)
T2 : Lien A → 90% utilisation, 100ms latence → Coût = 10 (inchangé)
T3 : Lien A tombe en panne                   → Coût = ∞ (lien retiré)

Problème : Aucune réaction entre T0 et T3
```

**2. Load Balancing limité**

OSPF supporte ECMP (Equal-Cost Multi-Path) mais uniquement pour les chemins de coût identique. Sans ajustement dynamique, la répartition de charge est statique.

**3. Inadéquation avec les SLA**

Les accords de niveau de service (SLA) définissent souvent des critères de latence et de perte que le coût OSPF traditionnel ne peut garantir.

#### 2.2.2 Impact sur les Performances

Étude de cas simulée :

| Métrique | Sans optimisation | Avec optimisation |
|----------|-------------------|-------------------|
| Latence moyenne | 45 ms | 12 ms |
| Perte de paquets | 2.5% | 0.3% |
| Utilisation max d'un lien | 95% | 70% |
| Gigue | 25 ms | 5 ms |

### 2.3 Solutions Existantes

#### 2.3.1 OSPF-TE (Traffic Engineering)

OSPF-TE est une extension d'OSPF définie par la RFC 3630 qui ajoute des informations de trafic engineering dans les LSA :

**Avantages :**
- Information sur la bande passante réservable
- Support MPLS-TE
- Standardisé

**Inconvénients :**
- Complexité de déploiement
- Nécessite MPLS
- Pas d'adaptation temps réel automatique

#### 2.3.2 SDN et Contrôleurs Centralisés

Les solutions SDN (Software-Defined Networking) comme OpenDaylight ou ONOS permettent un contrôle centralisé du routage :

**Avantages :**
- Vue globale du réseau
- Programmabilité complète
- Orchestration avancée

**Inconvénients :**
- Remplacement complet de l'infrastructure
- Point de défaillance unique
- Coût élevé

#### 2.3.3 Segment Routing

Segment Routing permet de définir des chemins explicites sans état par-flux :

**Avantages :**
- Flexibilité des chemins
- Pas d'état dans le réseau
- Compatible MPLS et IPv6

**Inconvénients :**
- Équipements compatibles nécessaires
- Complexité opérationnelle
- Courbe d'apprentissage

#### 2.3.4 Solutions Propriétaires

| Vendeur | Solution | Caractéristiques |
|---------|----------|------------------|
| Cisco | SD-WAN | Overlay intelligent, SLA-aware |
| Cisco | PfR (Performance Routing) | Ajustement basé sur métriques |
| Juniper | NorthStar | Contrôleur TE centralisé |
| Huawei | NCE-IP | Automatisation réseau |

### 2.4 Positionnement du Projet

#### 2.4.1 Approche Retenue

Notre projet adopte une approche **hybride et légère** :

- **Non intrusive** : Modification uniquement des coûts OSPF, pas du protocole
- **Incrémentale** : S'intègre dans une infrastructure OSPF existante
- **Open source** : Basée sur FRRouting et Python
- **Temps réel** : Collecte et réaction continues

#### 2.4.2 Comparaison avec les Solutions Existantes

| Critère | Notre solution | OSPF-TE | SDN | Segment Routing |
|---------|----------------|---------|-----|-----------------|
| Complexité déploiement | Faible | Moyenne | Élevée | Élevée |
| Coût infrastructure | Nul | Faible | Élevé | Moyen |
| Modification topologie | Non | Non | Oui | Non |
| Adaptation temps réel | Oui | Non | Oui | Partiel |
| Open source | Oui | Oui | Oui | Oui |
| Courbe apprentissage | Faible | Moyenne | Élevée | Élevée |

#### 2.4.3 Innovation Apportée

1. **Algorithme composite** : Combinaison pondérée de 3 métriques
2. **Automatisation complète** : De la détection à l'application
3. **Stratégies multiples** : Adaptation au contexte applicatif
4. **Interface de monitoring** : Visibilité temps réel
5. **Déploiement simplifié** : Script automatique

---

## 3. Analyse et Spécifications

### 3.1 Analyse des Besoins Fonctionnels

#### 3.1.1 Acteurs du Système

| Acteur | Description | Interactions |
|--------|-------------|--------------|
| Administrateur réseau | Utilisateur principal du système | Configuration, monitoring, déclenchement manuel |
| Système automatique | Timer d'optimisation | Exécution périodique des cycles |
| Routeurs FRRouting | Équipements gérés | Réception des configurations |
| Interface web | Canal de communication | Visualisation et commandes |

#### 3.1.2 Exigences Fonctionnelles

**EF1 - Collecte des Métriques**

| ID | Description | Priorité |
|----|-------------|----------|
| EF1.1 | Mesurer la latence via ICMP ping | Haute |
| EF1.2 | Mesurer le taux de perte de paquets | Haute |
| EF1.3 | Estimer l'utilisation de la bande passante | Haute |
| EF1.4 | Récupérer le coût OSPF actuel | Haute |
| EF1.5 | Horodater chaque mesure | Moyenne |

**EF2 - Calcul des Coûts**

| ID | Description | Priorité |
|----|-------------|----------|
| EF2.1 | Appliquer la stratégie composite (3 métriques) | Haute |
| EF2.2 | Appliquer la stratégie bande passante uniquement | Moyenne |
| EF2.3 | Appliquer la stratégie latence uniquement | Moyenne |
| EF2.4 | Respecter les limites de coût OSPF (1-65535) | Haute |
| EF2.5 | Configurer les seuils et pondérations | Haute |

**EF3 - Application des Configurations**

| ID | Description | Priorité |
|----|-------------|----------|
| EF3.1 | Modifier le coût OSPF via vtysh | Haute |
| EF3.2 | Sauvegarder la configuration dans le routeur | Haute |
| EF3.3 | Supporter le mode dry-run (simulation) | Haute |
| EF3.4 | Journaliser chaque modification | Moyenne |

**EF4 - Interface Utilisateur**

| ID | Description | Priorité |
|----|-------------|----------|
| EF4.1 | Afficher l'état du système (actif/inactif) | Haute |
| EF4.2 | Afficher les métriques de chaque lien | Haute |
| EF4.3 | Permettre le déclenchement manuel d'une optimisation | Haute |
| EF4.4 | Afficher l'historique des changements | Moyenne |
| EF4.5 | Exposer une API REST | Moyenne |

**EF5 - Automatisation**

| ID | Description | Priorité |
|----|-------------|----------|
| EF5.1 | Détecter automatiquement les conteneurs Docker | Haute |
| EF5.2 | Mettre à jour la configuration avec les noms actuels | Haute |
| EF5.3 | Exécuter des cycles d'optimisation périodiques | Haute |
| EF5.4 | Gérer les arrêts/redémarrages propres | Moyenne |

### 3.2 Analyse des Besoins Non Fonctionnels

#### 3.2.1 Performance

| ID | Exigence | Critère |
|----|----------|---------|
| ENF1.1 | Temps de cycle d'optimisation | < 30 secondes pour 10 liens |
| ENF1.2 | Latence de l'interface web | < 1 seconde de réponse |
| ENF1.3 | Consommation CPU | < 10% en fonctionnement continu |
| ENF1.4 | Consommation mémoire | < 100 MB |

#### 3.2.2 Fiabilité

| ID | Exigence | Critère |
|----|----------|---------|
| ENF2.1 | Gestion des erreurs de connexion | Retry + logging |
| ENF2.2 | Tolérance aux pannes de routeur | Continuer avec les routeurs disponibles |
| ENF2.3 | Persistance des logs | Fichier de log rotatif |

#### 3.2.3 Maintenabilité

| ID | Exigence | Critère |
|----|----------|---------|
| ENF3.1 | Code modulaire | Séparation claire des responsabilités |
| ENF3.2 | Documentation du code | Docstrings Python |
| ENF3.3 | Configuration externalisée | Fichier YAML |

#### 3.2.4 Portabilité

| ID | Exigence | Critère |
|----|----------|---------|
| ENF4.1 | Compatibilité Linux | Ubuntu 22.04 LTS minimum |
| ENF4.2 | Environnement virtuel Python | venv standard |
| ENF4.3 | Indépendance Docker | Fonctionnel avec tout client Docker |

### 3.3 Cas d'Utilisation

#### 3.3.1 Diagramme de Cas d'Utilisation

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SYSTÈME OSPF OPTIMIZER                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐                                                       │
│   │Administrateur│                                                      │
│   └──────┬──────┘                                                       │
│          │                                                              │
│          ├──────────► (Consulter le dashboard)                          │
│          │                                                              │
│          ├──────────► (Déclencher une optimisation manuelle)            │
│          │                    │                                         │
│          │                    └───────► «include» (Collecter métriques) │
│          │                    └───────► «include» (Calculer coûts)      │
│          │                    └───────► «include» (Appliquer configs)   │
│          │                                                              │
│          ├──────────► (Démarrer le mode continu)                        │
│          │                                                              │
│          ├──────────► (Arrêter le mode continu)                         │
│          │                                                              │
│          ├──────────► (Modifier la configuration)                       │
│          │                                                              │
│          └──────────► (Consulter les logs)                              │
│                                                                         │
│   ┌─────────────┐                                                       │
│   │   Timer     │                                                       │
│   │  (Système)  │                                                       │
│   └──────┬──────┘                                                       │
│          │                                                              │
│          └──────────► (Déclencher optimisation automatique)             │
│                              │                                          │
│                              └───────► «include» (Collecter métriques)  │
│                              └───────► «include» (Calculer coûts)       │
│                              └───────► «include» (Appliquer configs)    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 Description Détaillée des Cas d'Utilisation

**CU1 : Déclencher une optimisation manuelle**

| Élément | Description |
|---------|-------------|
| Acteur principal | Administrateur réseau |
| Préconditions | Système démarré, routeurs accessibles |
| Scénario nominal | 1. L'administrateur clique sur "Optimiser" dans le dashboard<br>2. Le système collecte les métriques de tous les liens<br>3. Le système calcule les nouveaux coûts<br>4. Le système affiche les changements proposés<br>5. Le système applique les modifications<br>6. Le dashboard se met à jour |
| Scénario alternatif | 3a. Aucun changement nécessaire → Message "Réseau stable" |
| Postconditions | Coûts OSPF optimisés, logs mis à jour |

**CU2 : Consulter le dashboard**

| Élément | Description |
|---------|-------------|
| Acteur principal | Administrateur réseau |
| Préconditions | Interface web démarrée |
| Scénario nominal | 1. L'administrateur accède à l'URL du dashboard<br>2. Le système affiche l'état actuel<br>3. Le système affiche les métriques de chaque lien<br>4. Le système affiche l'historique des changements |
| Postconditions | Aucune modification du système |

**CU3 : Exécuter une optimisation automatique**

| Élément | Description |
|---------|-------------|
| Acteur principal | Timer système |
| Préconditions | Mode continu activé |
| Scénario nominal | 1. Le timer déclenche un cycle<br>2. Le système collecte les métriques<br>3. Le système calcule et applique les coûts<br>4. Le système attend l'intervalle suivant |
| Fréquence | Toutes les 60 secondes (configurable) |

### 3.4 Diagrammes de Séquence

#### 3.4.1 Séquence : Cycle d'Optimisation Complet

```
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│ Dashboard │  │ Optimizer │  │ Collector │  │Calculator │  │  Router   │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
    │              │              │              │              │
    │ optimize()   │              │              │              │
    │─────────────►│              │              │              │
    │              │              │              │              │
    │              │ collect_all()│              │              │
    │              │─────────────►│              │              │
    │              │              │              │              │
    │              │              │ ping(dest)   │              │
    │              │              │─────────────────────────────►│
    │              │              │              │              │
    │              │              │◄─────────────────────────────│
    │              │              │  latency, loss              │
    │              │              │              │              │
    │              │              │get_ospf_cost()              │
    │              │              │─────────────────────────────►│
    │              │              │              │              │
    │              │              │◄─────────────────────────────│
    │              │              │  current_cost               │
    │              │              │              │              │
    │              │◄─────────────│              │              │
    │              │  metrics[]   │              │              │
    │              │              │              │              │
    │              │ calculate(metrics)          │              │
    │              │────────────────────────────►│              │
    │              │              │              │              │
    │              │◄────────────────────────────│              │
    │              │  new_costs[] │              │              │
    │              │              │              │              │
    │              │ Loop [for each cost change]│              │
    │              │──┐           │              │              │
    │              │  │ set_cost(interface, cost)│              │
    │              │  │────────────────────────────────────────►│
    │              │  │           │              │              │
    │              │  │◄────────────────────────────────────────│
    │              │  │           │  success     │              │
    │              │◄─┘           │              │              │
    │              │              │              │              │
    │◄─────────────│              │              │              │
    │ result{changes}             │              │              │
    │              │              │              │              │
```

#### 3.4.2 Séquence : Détection Automatique des Conteneurs

```
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│ AutoStart │  │  Docker   │  │YAML Config│  │ Optimizer │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
    │              │              │              │
    │docker ps     │              │              │
    │─────────────►│              │              │
    │              │              │              │
    │◄─────────────│              │              │
    │ containers[] │              │              │
    │              │              │              │
    │ parse(containers)           │              │
    │──────┐       │              │              │
    │      │       │              │              │
    │◄─────┘       │              │              │
    │ router_map   │              │              │
    │              │              │              │
    │ read()       │              │              │
    │──────────────────────────►│              │
    │              │              │              │
    │◄──────────────────────────│              │
    │ current_config             │              │
    │              │              │              │
    │ update(router_map)         │              │
    │──────────────────────────►│              │
    │              │              │              │
    │              │              │              │
    │ write()      │              │              │
    │──────────────────────────►│              │
    │              │              │              │
    │ start(config)              │              │
    │───────────────────────────────────────────►│
    │              │              │              │
    │◄───────────────────────────────────────────│
    │ running                    │              │
    │              │              │              │
```

---

## 4. Conception

### 4.1 Architecture Réseau Détaillée

#### 4.1.1 Vue d'Ensemble de la Topologie

L'architecture réseau implémentée suit un modèle hiérarchique OSPF classique à trois niveaux :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                              AREA 0 (Backbone)                          │
│                         ═══════════════════════                         │
│                                                                         │
│         ┌─────────────┐                           ┌─────────────┐       │
│         │    ABR1     │                           │    ABR2     │       │
│         │ 11.11.11.11 │                           │ 22.22.22.22 │       │
│         │             │                           │             │       │
│         │  ┌───────┐  │        Primary Link       │  ┌───────┐  │       │
│         │  │ eth1  │──┼───────────────────────────┼──│ eth1  │  │       │
│         │  └───────┘  │        10.0.0.0/30        │  └───────┘  │       │
│         │             │                           │             │       │
│         │  ┌───────┐  │                           │  ┌───────┐  │       │
│         │  │ eth3  │──┼───────────┐   ┌───────────┼──│ eth3  │  │       │
│         │  └───────┘  │           │   │           │  └───────┘  │       │
│         └──────┬──────┘           │   │           └──────┬──────┘       │
│                │                  │   │                  │              │
│                │            ┌─────┴───┴─────┐            │              │
│                │            │     ABR3      │            │              │
│                │            │  33.33.33.33  │            │              │
│                │            │               │            │              │
│                │            │ ┌───┐   ┌───┐ │            │              │
│                │            │ │eth│   │eth│ │            │              │
│                │            │ │ 0 │   │ 1 │ │            │              │
│                │            │ └─┬─┘   └─┬─┘ │            │              │
│                │            └───┼───────┼───┘            │              │
│                │       10.0.1.0/30    10.0.2.0/30        │              │
│                │            │   Backup Links  │          │              │
│                │            └───────┬─────────┘          │              │
│                │                    │                    │              │
└────────────────┼────────────────────┼────────────────────┼──────────────┘
            │                    │                    │
      ════════╧════════════════════╧════════════════════╧════════
            │                                         │
   ┌────────────┴────────────┐           ┌────────────────┴────────────┐
   │        AREA 1           │           │         AREA 2              │
   │   ═══════════════       │           │    ═══════════════          │
   │                         │           │                             │
   │   ┌─────────┐           │           │           ┌─────────┐       │
   │   │   R1    │ ◄── eth0  │           │   eth0 ──►│   R3    │       │
   │   │10.1.1.2 │──────────►│           │◄──────────│10.2.1.2 │       │
   │   └────┬────┘  ABR1     │           │    ABR2   └────┬────┘       │
   │        │                │           │                │            │
   │        │ eth0           │           │          eth0  │            │
   │        │192.168.1.1     │           │    192.168.3.1 │            │
   │   ┌────┴────┐           │           │           ┌────┴────┐       │
   │   │   PC1   │           │           │           │   PC3   │       │
   │   │.1.10    │           │           │           │.3.10    │       │
   │   └─────────┘           │           │           └─────────┘       │
   │                         │           │                             │
   │   ┌─────────┐           │           │           ┌─────────┐       │
   │   │   R2    │ ◄── eth2  │           │   eth2 ──►│   R4    │       │
   │   │10.1.2.2 │──────────►│           │◄──────────│10.2.2.2 │       │
   │   └────┬────┘  ABR1     │           │    ABR2   └────┬────┘       │
   │        │                │           │                │            │
   │        │ eth0           │           │          eth0  │            │
   │        │192.168.2.1     │           │    192.168.4.1 │            │
   │   ┌────┴────┐           │           │           ┌────┴────┐       │
   │   │   PC2   │           │           │           │   PC4   │       │
   │   │.2.10    │           │           │           │.4.10    │       │
   │   └─────────┘           │           │           └─────────┘       │
   │                         │           │                             │
   └─────────────────────────┘           └─────────────────────────────┘
```

#### 4.1.2 Description des Liens

| Lien | Routeurs | Réseau | Zone | Fonction |
|------|----------|--------|------|----------|
| L1 | ABR1 ↔ ABR2 | 10.0.0.0/30 | Area 0 | Lien backbone principal |
| L2 | ABR1 ↔ ABR3 | 10.0.1.0/30 | Area 0 | Lien backbone backup |
| L3 | ABR2 ↔ ABR3 | 10.0.2.0/30 | Area 0 | Lien backbone backup |
| L4 | ABR1 ↔ R1 | 10.1.1.0/30 | Area 1 | Accès zone 1 |
| L5 | ABR1 ↔ R2 | 10.1.2.0/30 | Area 1 | Accès zone 1 |
| L6 | ABR2 ↔ R3 | 10.2.1.0/30 | Area 2 | Accès zone 2 |
| L7 | ABR2 ↔ R4 | 10.2.2.0/30 | Area 2 | Accès zone 2 |

#### 4.1.3 Analyse des Chemins

**Chemin PC1 → PC3 (sans optimisation) :**

```
PC1 (192.168.1.10)
   │
   │ Gateway: 192.168.1.1 (R1)
   ▼
  R1 ──── 10.1.1.0/30 ────► ABR1
                     │
              10.0.0.0/30 (Coût: 10)
                     │
                     ▼
                    ABR2 ──── 10.2.1.0/30 ────► R3
                                       │
                                       ▼
                                  PC3 (192.168.3.10)

Coût total = 10 + 10 + 10 = 30
```

**Chemin alternatif via ABR3 (si lien principal dégradé) :**

```
PC1 → R1 → ABR1 → ABR3 → ABR2 → R3 → PC3

Coût = 10 + 10 + 10 + 10 = 40 (normalement)
     10 + 25 + 10 + 10 = 55 (après optimisation du lien ABR1-ABR2)
```

### 4.2 Topologie OSPF Multi-zones

#### 4.2.1 Configuration des Zones

| Zone | ID | Type | Routeurs | Caractéristiques |
|------|-----|------|----------|------------------|
| Area 0 | 0.0.0.0 | Backbone | ABR1, ABR2, ABR3 | Zone de transit obligatoire |
| Area 1 | 0.0.0.1 | Standard | ABR1, R1, R2 | Zone d'accès utilisateurs |
| Area 2 | 0.0.0.2 | Standard | ABR2, R3, R4 | Zone d'accès utilisateurs |

#### 4.2.2 Rôles des Routeurs

| Routeur | Router-ID | Rôle(s) | Zones | Description |
|---------|-----------|---------|-------|-------------|
| ABR1 | 11.11.11.11 | ABR | 0, 1 | Pont entre backbone et zone 1 |
| ABR2 | 22.22.22.22 | ABR | 0, 2 | Pont entre backbone et zone 2 |
| ABR3 | 33.33.33.33 | Backbone | 0 | Routeur de transit/backup |
| R1 | 1.1.1.1 | Internal | 1 | Accès LAN 192.168.1.0/24 |
| R2 | 2.2.2.2 | Internal | 1 | Accès LAN 192.168.2.0/24 |
| R3 | 3.3.3.3 | Internal | 2 | Accès LAN 192.168.3.0/24 |
| R4 | 4.4.4.4 | Internal | 2 | Accès LAN 192.168.4.0/24 |

#### 4.2.3 Adjacences OSPF Attendues

```
ABR1 ── FULL ── ABR2  (via 10.0.0.0/30)
ABR1 ── FULL ── ABR3  (via 10.0.1.0/30)
ABR2 ── FULL ── ABR3  (via 10.0.2.0/30)
ABR1 ── FULL ── R1    (via 10.1.1.0/30)
ABR1 ── FULL ── R2    (via 10.1.2.0/30)
ABR2 ── FULL ── R3    (via 10.2.1.0/30)
ABR2 ── FULL ── R4    (via 10.2.2.0/30)
```

### 4.3 Architecture Logicielle

#### 4.3.1 Vue en Couches

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COUCHE PRÉSENTATION                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                       Interface Web (Flask)                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │  │
│  │  │  Dashboard  │  │  API REST   │  │  Templates  │  │  Static   │ │  │
│  │  │   (HTML)    │  │  (JSON)     │  │  (Jinja2)   │  │  (CSS/JS) │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                          COUCHE MÉTIER                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      OSPF Optimizer (Core)                         │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────┐ │  │
│  │  │ Metrics         │  │ Cost            │  │ Optimization       │ │  │
│  │  │ Collector       │  │ Calculator      │  │ Engine             │ │  │
│  │  │                 │  │                 │  │                    │ │  │
│  │  │ - Latency       │  │ - Composite     │  │ - Strategy pattern │ │  │
│  │  │ - Packet Loss   │  │ - Bandwidth     │  │ - Dry-run mode     │ │  │
│  │  │ - Bandwidth     │  │ - Latency       │  │ - Continuous mode  │ │  │
│  │  └─────────────────┘  └─────────────────┘  └────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                         COUCHE DONNÉES                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────┐ │  │
│  │  │ Configuration   │  │ Metrics         │  │ History            │ │  │
│  │  │ (YAML)          │  │ (In-Memory)     │  │ (In-Memory/Log)    │ │  │
│  │  └─────────────────┘  └─────────────────┘  └────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                       COUCHE INFRASTRUCTURE                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      Router Connection                             │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │              Docker Exec Adapter                             │  │  │
│  │  │                                                               │  │  │
│  │  │   subprocess.run(['docker', 'exec', container, ...])         │  │  │
│  │  │                                                               │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│                       INFRASTRUCTURE EXTERNE                            │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │        Conteneurs Docker FRRouting (ABR1, ABR2, R1, ...)          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 4.3.2 Diagramme de Composants

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            ospf_optimizer.py                             │
│                           (Point d'entrée)                               │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                          main()                                    │  │
│  │  - Parse arguments                                                 │  │
│  │  - Load configuration                                              │  │
│  │  - Initialize components                                           │  │
│  │  - Start optimization loop                                         │  │
│  └─────────────────────────────┬──────────────────────────────────────┘  │
└────────────────────────────────┼─────────────────────────────────────────┘
                      │
      ┌───────────────────────┼───────────────────────┐
      │                       │                       │
      ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│router_connection│    │metrics_collector│    │ cost_calculator │
│      .py        │    │      .py        │    │      .py        │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│                 │    │                 │    │                 │
│RouterConnection │◄───│MetricsCollector │    │CostCalculator   │
│                 │    │                 │    │                 │
│ + execute_cmd() │    │ + collect_all() │    │ + calculate()   │
│ + execute_vtysh │    │ + measure_      │    │ + composite()   │
│ + set_ospf_cost │    │   latency()     │    │ + bandwidth()   │
│ + get_ospf_cost │    │ + measure_loss()│    │ + latency()     │
│                 │    │ + measure_bw()  │    │                 │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
      │                      │                      │
      │                      │                      │
      ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         src/__init__.py                                  │
│                      (Exports des modules)                               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ web_interface.py│    │  auto_start
