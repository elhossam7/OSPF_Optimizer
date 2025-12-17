"""
Script principal d'optimisation OSPF
Orchestre la collecte des métriques et l'ajustement dynamique des coûts
"""

import os
import sys
import time
import yaml
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent))

from src.router_connection import RouterConnection, MockRouterConnection
from src.metrics_collector import MetricsCollector, LinkMetrics
from src.cost_calculator import CostCalculator, OptimizationStrategy, CostCalculationResult

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ospf_optimizer.log')
    ]
)
logger = logging.getLogger(__name__)


class OSPFOptimizer:
    """
    Optimiseur OSPF principal
    Collecte les métriques et ajuste dynamiquement les coûts OSPF
    """
    
    def __init__(self, config_path: str, simulation_mode: bool = False):
        """
        Args:
            config_path: Chemin vers le fichier de configuration YAML
            simulation_mode: Si True, utilise des données simulées (pas de connexion réelle)
        """
        self.config = self._load_config(config_path)
        self.simulation_mode = simulation_mode
        
        # Initialiser les composants
        if simulation_mode:
            logger.info("Mode simulation activé - pas de connexion réelle aux routeurs")
            self.connection = MockRouterConnection(self.config.get('global', {}))
        else:
            self.connection = RouterConnection(self.config.get('global', {}))
            
        self.metrics_collector = MetricsCollector(self.connection)
        
        # Initialiser le calculateur de coûts
        cost_config = {
            **self.config.get('cost_factors', {}),
            'thresholds': self.config.get('thresholds', {})
        }
        self.cost_calculator = CostCalculator(cost_config)
        
        # Configurer les routeurs
        self._setup_routers()
        
        # État
        self.running = False
        self.last_optimization = None
        self.optimization_count = 0
        
    def _load_config(self, config_path: str) -> Dict:
        """Charge la configuration depuis le fichier YAML"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration chargée depuis {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Fichier de configuration non trouvé: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Erreur de parsing YAML: {e}")
            raise
            
    def _setup_routers(self):
        """Configure les routeurs depuis la configuration"""
        routers = self.config.get('routers', {})
        for name, config in routers.items():
            self.connection.add_router(name, config)
            logger.debug(f"Routeur {name} ajouté")
        logger.info(f"{len(routers)} routeurs configurés")
        
    def collect_metrics(self) -> List[LinkMetrics]:
        """
        Collecte les métriques de tous les liens surveillés
        
        Returns:
            Liste des métriques collectées
        """
        monitored_links = self.config.get('monitored_links', [])
        
        if not monitored_links:
            logger.warning("Aucun lien configuré pour le monitoring")
            return []
            
        logger.info(f"Collecte des métriques pour {len(monitored_links)} liens...")
        
        all_metrics = []
        for link in monitored_links:
            try:
                # Enrichir la config du lien avec les infos des routeurs
                link_config = self._enrich_link_config(link)
                metrics = self.metrics_collector.collect_link_metrics(link_config)
                all_metrics.append(metrics)
                logger.debug(f"Métriques collectées pour {link['name']}")
            except Exception as e:
                logger.error(f"Erreur lors de la collecte pour {link['name']}: {e}")
                
        return all_metrics
        
    def _enrich_link_config(self, link: Dict) -> Dict:
        """Enrichit la configuration d'un lien avec les IPs des routeurs"""
        enriched = link.copy()
        
        # Obtenir les infos du routeur destination
        dest_router = link.get('dest_router')
        dest_interface = link.get('dest_interface')
        
        if dest_router in self.config.get('routers', {}):
            router_config = self.config['routers'][dest_router]
            for iface in router_config.get('interfaces', []):
                if iface['name'] == dest_interface:
                    enriched['dest_ip'] = iface.get('ip', '')
                    break
                    
        return enriched
        
    def calculate_optimal_costs(self, metrics: List[LinkMetrics],
                                strategy: OptimizationStrategy = OptimizationStrategy.COMPOSITE
                               ) -> List[CostCalculationResult]:
        """
        Calcule les coûts OSPF optimaux pour tous les liens
        
        Args:
            metrics: Métriques collectées
            strategy: Stratégie d'optimisation
            
        Returns:
            Résultats des calculs de coûts
        """
        return self.cost_calculator.calculate_all_costs(metrics, strategy)
        
    def apply_cost_changes(self, results: List[CostCalculationResult], 
                          dry_run: bool = False) -> int:
        """
        Applique les changements de coûts OSPF sur les routeurs
        
        Args:
            results: Résultats des calculs
            dry_run: Si True, n'applique pas réellement les changements
            
        Returns:
            Nombre de changements appliqués
        """
        changes_applied = 0
        
        for result in results:
            if not result.should_update:
                continue
                
            # Trouver le lien dans la configuration
            link_config = None
            for link in self.config.get('monitored_links', []):
                if link['name'] == result.link_name:
                    link_config = link
                    break
                    
            if not link_config:
                logger.warning(f"Configuration non trouvée pour {result.link_name}")
                continue
                
            router = link_config['source_router']
            interface = link_config['source_interface']
            new_cost = result.calculated_cost
            
            if dry_run:
                logger.info(f"[DRY-RUN] {router}.{interface}: coût {result.current_cost} → {new_cost}")
            else:
                success = self.connection.set_ospf_cost(router, interface, new_cost)
                if success:
                    changes_applied += 1
                    logger.info(f"✓ {router}.{interface}: coût modifié à {new_cost}")
                else:
                    logger.error(f"✗ Échec de modification du coût sur {router}.{interface}")
                    
        return changes_applied
        
    def optimize_once(self, strategy: OptimizationStrategy = OptimizationStrategy.COMPOSITE,
                      dry_run: bool = False) -> Dict:
        """
        Effectue un cycle d'optimisation complet
        
        Args:
            strategy: Stratégie d'optimisation
            dry_run: Mode simulation sans appliquer les changements
            
        Returns:
            Résumé de l'optimisation
        """
        start_time = datetime.now()
        
        logger.info("="*60)
        logger.info(f"Début du cycle d'optimisation - {start_time}")
        logger.info(f"Stratégie: {strategy.value}")
        logger.info("="*60)
        
        # 1. Collecter les métriques
        metrics = self.collect_metrics()
        if not metrics:
            return {'error': 'Aucune métrique collectée', 'success': False}
            
        # 2. Calculer les coûts optimaux
        results = self.calculate_optimal_costs(metrics, strategy)
        
        # 3. Afficher le résumé
        summary = self.cost_calculator.get_optimization_summary(results)
        self._print_summary(summary)
        
        # 4. Appliquer les changements
        changes = self.apply_cost_changes(results, dry_run)
        
        # 5. Mettre à jour l'état
        self.last_optimization = datetime.now()
        self.optimization_count += 1
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info("-"*60)
        logger.info(f"Cycle terminé en {duration:.2f}s - {changes} changements appliqués")
        logger.info("="*60)
        
        return {
            'success': True,
            'timestamp': start_time.isoformat(),
            'duration_seconds': duration,
            'changes_applied': changes,
            'summary': summary
        }
        
    def _print_summary(self, summary: Dict):
        """Affiche un résumé formaté des optimisations"""
        print("\n" + "="*60)
        print("RÉSUMÉ DE L'OPTIMISATION OSPF")
        print("="*60)
        print(f"Liens surveillés: {summary['total_links']}")
        print(f"Liens à mettre à jour: {summary['links_to_update']}")
        print(f"Liens stables: {summary['links_stable']}")
        print("-"*60)
        
        if summary['updates']:
            print("\nCHANGEMENTS PROPOSÉS:")
            print("-"*60)
            for update in summary['updates']:
                print(f"  {update['link']}: {update['current']} → {update['new']}")
                print(f"    Raison: {update['reason']}")
            print()
        else:
            print("\n✓ Aucun changement nécessaire\n")
            
        print("ÉTAT DES LIENS:")
        print("-"*60)
        for result in summary['all_results']:
            status = "⚡" if result['will_update'] else "✓"
            metrics = result['metrics']
            print(f"  {status} {result['link']}:")
            print(f"      Coût: {result['current']} → {result['calculated']}")
            print(f"      BW: {metrics['bandwidth_utilization']:.1f}% | "
                  f"Latence: {metrics['latency_ms']:.1f}ms | "
                  f"Perte: {metrics['packet_loss_percent']:.2f}%")
        print("="*60 + "\n")
        
    def run_continuous(self, interval: int = 60, 
                       strategy: OptimizationStrategy = OptimizationStrategy.COMPOSITE,
                       dry_run: bool = False):
        """
        Exécute l'optimisation en continu
        
        Args:
            interval: Intervalle entre les optimisations (secondes)
            strategy: Stratégie d'optimisation
            dry_run: Mode simulation
        """
        self.running = True
        logger.info(f"Démarrage de l'optimisation continue (intervalle: {interval}s)")
        
        try:
            while self.running:
                self.optimize_once(strategy, dry_run)
                logger.info(f"Prochaine optimisation dans {interval} secondes...")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Arrêt demandé par l'utilisateur")
        finally:
            self.stop()
            
    def stop(self):
        """Arrête l'optimisation et ferme les connexions"""
        self.running = False
        self.connection.disconnect_all()
        logger.info("Optimiseur arrêté")
        
    def get_status(self) -> Dict:
        """Retourne l'état actuel de l'optimiseur"""
        return {
            'running': self.running,
            'simulation_mode': self.simulation_mode,
            'optimization_count': self.optimization_count,
            'last_optimization': self.last_optimization.isoformat() if self.last_optimization else None,
            'configured_routers': list(self.connection.routers.keys()),
            'monitored_links': len(self.config.get('monitored_links', []))
        }


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description='OSPF Optimizer - Ajustement dynamique des coûts OSPF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python ospf_optimizer.py --config config/routers.yaml --once
  python ospf_optimizer.py --config config/routers.yaml --interval 30
  python ospf_optimizer.py --simulation --once
  python ospf_optimizer.py --dry-run --once
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config/routers.yaml',
        help='Chemin vers le fichier de configuration YAML'
    )
    
    parser.add_argument(
        '--simulation', '-s',
        action='store_true',
        help='Mode simulation (données simulées, pas de connexion réelle)'
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Mode dry-run (affiche les changements sans les appliquer)'
    )
    
    parser.add_argument(
        '--once', '-1',
        action='store_true',
        help='Exécute un seul cycle d\'optimisation puis quitte'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=60,
        help='Intervalle entre les optimisations en secondes (défaut: 60)'
    )
    
    parser.add_argument(
        '--strategy',
        choices=['composite', 'bandwidth', 'latency'],
        default='composite',
        help='Stratégie d\'optimisation (défaut: composite)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mode verbose (affiche plus de détails)'
    )
    
    parser.add_argument(
        '--web', '-w',
        action='store_true',
        help='Lance le dashboard web interactif'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='Port pour le serveur web (défaut: 5000)'
    )
    
    args = parser.parse_args()
    
    # Configurer le niveau de log
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Mapper la stratégie
    strategy_map = {
        'composite': OptimizationStrategy.COMPOSITE,
        'bandwidth': OptimizationStrategy.BANDWIDTH_BASED,
        'latency': OptimizationStrategy.LATENCY_BASED
    }
    strategy = strategy_map[args.strategy]
    
    # Créer l'optimiseur
    try:
        optimizer = OSPFOptimizer(
            config_path=args.config,
            simulation_mode=args.simulation
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation: {e}")
        sys.exit(1)
        
    # Afficher le statut initial
    status = optimizer.get_status()
    logger.info(f"Optimiseur initialisé:")
    logger.info(f"  - Mode: {'Simulation' if status['simulation_mode'] else 'Production'}")
    logger.info(f"  - Routeurs: {len(status['configured_routers'])}")
    logger.info(f"  - Liens surveillés: {status['monitored_links']}")
    
    # Exécuter
    try:
        if args.web:
            # Mode dashboard web
            from src.web_interface import create_app, run_server
            logger.info(f"Démarrage du dashboard web sur http://0.0.0.0:{args.port}")
            app = create_app(optimizer)
            run_server(app, port=args.port, debug=args.verbose)
        elif args.once:
            optimizer.optimize_once(strategy, args.dry_run)
        else:
            optimizer.run_continuous(args.interval, strategy, args.dry_run)
    except Exception as e:
        logger.error(f"Erreur durant l'exécution: {e}")
        raise
    finally:
        optimizer.stop()


if __name__ == '__main__':
    main()
