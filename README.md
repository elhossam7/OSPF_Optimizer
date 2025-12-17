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

cd C:\OSPF_Optimizer
pip install -r requirements.txt

## Utilisation

### Mode Simulation
python ospf_optimizer.py --simulation --once

### Mode Production
python ospf_optimizer.py --once

### Dashboard Web
python src/web_interface.py --simulation

## Commandes FRRouting

docker exec R1 vtysh -c "show ip ospf neighbor"
docker exec R1 vtysh -c "show ip ospf interface"
docker exec R1 vtysh -c "show ip route ospf"
