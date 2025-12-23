#!/usr/bin/env python3
"""
Script de démarrage automatique de l'OSPF Optimizer
Détecte automatiquement les noms des conteneurs GNS3 et met à jour la configuration
"""

import subprocess
import re
import sys
import os
import yaml
import argparse
from pathlib import Path


def get_docker_containers():
    """
    Récupère la liste des conteneurs Docker en cours d'exécution
    
    Returns:
        dict: Dictionnaire {nom_routeur: nom_conteneur_complet}
    """
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}\t{{.Image}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"Erreur lors de l'exécution de docker ps: {result.stderr}")
            return {}
            
        containers = {}
        lines = result.stdout.strip().split('\n')
        
        # Patterns pour identifier les routeurs FRR
        router_patterns = ['ABR1', 'ABR2', 'ABR3', 'R1', 'R2', 'R3', 'R4']
        pc_patterns = ['PC1', 'PC2', 'PC3', 'PC4']
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split('\t')
            if len(parts) < 2:
                continue
                
            container_name = parts[0]
            image_name = parts[1]
            
            # Chercher les routeurs FRR
            for router in router_patterns:
                # Match patterns comme: GNS3.ABR1.uuid, OSPF_Optimisation_lab_env-ABR1-1, etc.
                if f'.{router}.' in container_name or f'-{router}-' in container_name or container_name.endswith(f'.{router}'):
                    # Vérifier que c'est une image FRR
                    if 'frr' in image_name.lower() or 'frrouting' in image_name.lower():
                        containers[router] = container_name
                        break
            
            # Chercher les PCs Alpine
            for pc in pc_patterns:
                if f'.{pc}.' in container_name or f'-{pc}-' in container_name or container_name.endswith(f'.{pc}'):
                    if 'alpine' in image_name.lower():
                        containers[pc] = container_name
                        break
        
        return containers
        
    except subprocess.TimeoutExpired:
        print("Timeout lors de l'exécution de docker ps")
        return {}
    except FileNotFoundError:
        print("Docker n'est pas installé ou pas dans le PATH")
        return {}
    except Exception as e:
        print(f"Erreur: {e}")
        return {}


def update_routers_yaml(config_path: str, containers: dict) -> bool:
    """
    Met à jour le fichier routers.yaml avec les noms de conteneurs détectés
    
    Args:
        config_path: Chemin vers le fichier de configuration
        containers: Dictionnaire des conteneurs détectés
        
    Returns:
        bool: True si la mise à jour a réussi
    """
    try:
        # Lire le fichier YAML
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        updated_routers = []
        updated_pcs = []
        
        # Mettre à jour les routeurs
        if 'routers' in config:
            for router_name, router_config in config['routers'].items():
                if router_name in containers:
                    old_name = router_config.get('container_name', 'N/A')
                    new_name = containers[router_name]
                    if old_name != new_name:
                        router_config['container_name'] = new_name
                        updated_routers.append(f"  {router_name}: {old_name} → {new_name}")
        
        # Mettre à jour les PCs
        if 'pcs' in config:
            for pc_name, pc_config in config['pcs'].items():
                if pc_name in containers:
                    old_name = pc_config.get('container_name', 'N/A')
                    new_name = containers[pc_name]
                    if old_name != new_name:
                        pc_config['container_name'] = new_name
                        updated_pcs.append(f"  {pc_name}: {old_name} → {new_name}")
        
        # Écrire le fichier mis à jour
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        # Afficher les modifications
        if updated_routers or updated_pcs:
            print("\nConfiguration mise à jour:")
            if updated_routers:
                print("  Routeurs:")
                for update in updated_routers:
                    print(f"    {update}")
            if updated_pcs:
                print("  PCs:")
                for update in updated_pcs:
                    print(f"    {update}")
        else:
            print("\nConfiguration déjà à jour (aucune modification nécessaire)")
            
        return True
        
    except FileNotFoundError:
        print(f"Fichier de configuration non trouvé: {config_path}")
        return False
    except yaml.YAMLError as e:
        print(f"Erreur de parsing YAML: {e}")
        return False
    except Exception as e:
        print(f"Erreur lors de la mise à jour: {e}")
        return False


def preserve_yaml_format(config_path: str, containers: dict) -> bool:
    """
    Met à jour le fichier routers.yaml en préservant le format et les commentaires
    (Alternative qui préserve mieux le formatage original)
    
    Args:
        config_path: Chemin vers le fichier de configuration
        containers: Dictionnaire des conteneurs détectés
        
    Returns:
        bool: True si la mise à jour a réussi
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated = False
        updates = []
        
        for router_name, new_container_name in containers.items():
            # Pattern pour trouver et remplacer container_name pour ce routeur
            # Cherche: container_name: "GNS3.ROUTEUR.uuid" ou container_name: GNS3.ROUTEUR.uuid
            # Gère les guillemets optionnels autour de la valeur
            pattern = rf'(container_name:\s*)["\']?(GNS3\.{router_name}\.[a-f0-9-]+|{router_name})["\']?(\s*(?:\n|$))'
            
            match = re.search(pattern, content)
            if match:
                old_name = match.group(2).strip()
                if old_name != new_container_name:
                    # Préserver les guillemets si présents dans l'original
                    full_match = match.group(0)
                    has_quotes = '"' in full_match or "'" in full_match
                    if has_quotes:
                        replacement = rf'\g<1>"{new_container_name}"\g<3>'
                    else:
                        replacement = rf'\g<1>{new_container_name}\g<3>'
                    content = re.sub(pattern, replacement, content)
                    updates.append(f"  {router_name}: {old_name} → {new_container_name}")
                    updated = True
        
        if updated:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("\nConfiguration mise à jour:")
            for update in updates:
                print(f"  {update}")
        else:
            print("\nConfiguration déjà à jour (aucune modification nécessaire)")
            
        return True
        
    except Exception as e:
        print(f"Erreur: {e}")
        return False


def start_optimizer(config_path: str, args):
    """
    Lance l'optimiseur OSPF
    
    Args:
        config_path: Chemin vers le fichier de configuration
        args: Arguments de la ligne de commande
    """
    # Construire la commande
    cmd = [sys.executable, 'ospf_optimizer.py', '--config', config_path]
    
    if args.web:
        cmd.extend(['--web', '--port', str(args.port)])
    if args.dry_run:
        cmd.append('--dry-run')
    if args.verbose:
        cmd.append('--verbose')
    if args.simulation:
        cmd.append('--simulation')
    if args.once:
        cmd.append('--once')
    if args.interval:
        cmd.extend(['--interval', str(args.interval)])
    if args.strategy:
        cmd.extend(['--strategy', args.strategy])
    
    print(f"\nDémarrage de l'optimiseur: {' '.join(cmd)}\n")
    print("=" * 60)
    
    # Exécuter l'optimiseur
    try:
        os.execvp(sys.executable, cmd)
    except Exception as e:
        print(f"Erreur lors du démarrage: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Démarrage automatique de l\'OSPF Optimizer avec détection des conteneurs GNS3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python auto_start.py                     # Démarrage standard
  python auto_start.py --web               # Avec dashboard web
  python auto_start.py --dry-run --verbose # Mode test détaillé
  python auto_start.py --detect-only       # Détection sans démarrage
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config/routers.yaml',
        help='Chemin vers le fichier de configuration YAML'
    )
    
    parser.add_argument(
        '--detect-only', '-d',
        action='store_true',
        help='Détecte et met à jour les conteneurs sans démarrer l\'optimiseur'
    )
    
    parser.add_argument(
        '--no-update',
        action='store_true',
        help='Ne pas mettre à jour la configuration (utiliser telle quelle)'
    )
    
    parser.add_argument(
        '--web', '-w',
        action='store_true',
        help='Lance le dashboard web interactif'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8080,
        help='Port pour le serveur web (défaut: 8080)'
    )
    
    parser.add_argument(
        '--simulation', '-s',
        action='store_true',
        help='Mode simulation (données simulées)'
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Mode dry-run (affiche sans appliquer)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mode verbose'
    )
    
    parser.add_argument(
        '--once', '-1',
        action='store_true',
        help='Exécute un seul cycle puis quitte'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=None,
        help='Intervalle entre les optimisations en secondes'
    )
    
    parser.add_argument(
        '--strategy',
        choices=['composite', 'bandwidth', 'latency'],
        default=None,
        help='Stratégie d\'optimisation'
    )
    
    args = parser.parse_args()
    
    # Changer vers le répertoire du script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("=" * 60)
    print("OSPF Optimizer - Démarrage Automatique")
    print("=" * 60)
    
    # Étape 1: Détecter les conteneurs
    print("\nDétection des conteneurs Docker GNS3...")
    containers = get_docker_containers()
    
    if not containers:
        print("\nAucun conteneur FRR détecté!")
        print("   Vérifiez que:")
        print("   1. GNS3 est lancé avec un projet ouvert")
        print("   2. Les routeurs sont démarrés")
        print("   3. Docker est accessible (docker ps)")
        
        if not args.simulation:
            response = input("\n   Continuer quand même? (o/N): ")
            if response.lower() != 'o':
                sys.exit(1)
    else:
        print(f"\n{len(containers)} conteneurs détectés:")
        for name, container in sorted(containers.items()):
            print(f"   {name}: {container}")
    
    # Étape 2: Mettre à jour la configuration
    if not args.no_update and containers:
        print(f"\nMise à jour de {args.config}...")
        if not preserve_yaml_format(args.config, containers):
            print("La mise à jour a échoué, utilisation de la configuration existante")
    
    # Étape 3: Démarrer l'optimiseur (sauf si --detect-only)
    if args.detect_only:
        print("\nDétection terminée (--detect-only)")
        sys.exit(0)
    
    start_optimizer(args.config, args)


if __name__ == '__main__':
    main()
