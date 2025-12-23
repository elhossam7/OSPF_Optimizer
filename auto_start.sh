#!/bin/bash
#
# Script de démarrage automatique de l'OSPF Optimizer
# Détecte les conteneurs GNS3 et lance l'optimiseur
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config/routers.yaml"
VENV_PATH="${SCRIPT_DIR}/venv"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "============================================================"
echo -e "${BLUE}OSPF Optimizer - Démarrage Automatique${NC}"
echo "============================================================"

# Vérifier que Docker est disponible
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker n'est pas installé ou pas dans le PATH${NC}"
    exit 1
fi

# Vérifier que Python est disponible
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 n'est pas installé${NC}"
    exit 1
fi

# Activer l'environnement virtuel si présent
if [ -d "$VENV_PATH" ]; then
    echo -e "${BLUE}Activation de l'environnement virtuel...${NC}"
    source "${VENV_PATH}/bin/activate"
fi

# Détecter les conteneurs
echo -e "\n${BLUE}Détection des conteneurs Docker GNS3...${NC}"

# Récupérer les conteneurs FRR
declare -A CONTAINERS

while IFS=$'\t' read -r name image; do
    # Chercher les routeurs
    for router in ABR1 ABR2 ABR3 R1 R2 R3 R4; do
        if [[ "$name" == *".$router."* ]] || [[ "$name" == *"-$router-"* ]]; then
            if [[ "$image" == *"frr"* ]] || [[ "$image" == *"frrouting"* ]]; then
                CONTAINERS[$router]="$name"
            fi
        fi
    done
    # Chercher les PCs
    for pc in PC1 PC2 PC3 PC4; do
        if [[ "$name" == *".$pc."* ]] || [[ "$name" == *"-$pc-"* ]]; then
            if [[ "$image" == *"alpine"* ]]; then
                CONTAINERS[$pc]="$name"
            fi
        fi
    done
done < <(docker ps --format "{{.Names}}\t{{.Image}}")

# Afficher les conteneurs détectés
if [ ${#CONTAINERS[@]} -eq 0 ]; then
    echo -e "${YELLOW}Aucun conteneur FRR détecté!${NC}"
    echo "   Vérifiez que:"
    echo "   1. GNS3 est lancé avec un projet ouvert"
    echo "   2. Les routeurs sont démarrés"
    echo "   3. Docker est accessible (docker ps)"
else
    echo -e "${GREEN}${#CONTAINERS[@]} conteneurs détectés:${NC}"
    for router in "${!CONTAINERS[@]}"; do
        echo "   $router: ${CONTAINERS[$router]}"
    done
fi

# Mettre à jour le fichier YAML
if [ ${#CONTAINERS[@]} -gt 0 ]; then
    echo -e "\n${BLUE}Mise à jour de $CONFIG_FILE...${NC}"
    
    UPDATED=0
    for router in "${!CONTAINERS[@]}"; do
        container_name="${CONTAINERS[$router]}"
        # Utiliser sed pour remplacer le container_name
        if grep -q "container_name:.*$router" "$CONFIG_FILE" 2>/dev/null; then
            # Remplacer le pattern GNS3.ROUTER.uuid ou juste ROUTER
            sed -i "s|container_name:.*GNS3\.$router\.[a-f0-9-]*|container_name: $container_name|g" "$CONFIG_FILE"
            sed -i "s|container_name: $router$|container_name: $container_name|g" "$CONFIG_FILE"
            UPDATED=$((UPDATED + 1))
        fi
    done
    
    if [ $UPDATED -gt 0 ]; then
        echo -e "${GREEN}Configuration mise à jour ($UPDATED routeurs)${NC}"
    else
        echo -e "${GREEN}Configuration déjà à jour${NC}"
    fi
fi

# Lancer l'optimiseur
echo -e "\n${BLUE}Démarrage de l'optimiseur...${NC}"
echo "============================================================"

cd "$SCRIPT_DIR"

# Passer tous les arguments au script Python
python3 ospf_optimizer.py --config "$CONFIG_FILE" "$@"
