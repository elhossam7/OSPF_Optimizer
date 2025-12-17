"""
Module de calcul et d'optimisation des coûts OSPF
Implémente différents algorithmes pour calculer les coûts optimaux
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math
import logging

from .metrics_collector import LinkMetrics

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Stratégies d'optimisation disponibles"""
    BANDWIDTH_BASED = "bandwidth"      # Basé uniquement sur la bande passante
    LATENCY_BASED = "latency"          # Basé uniquement sur la latence
    COMPOSITE = "composite"            # Combinaison de plusieurs métriques
    LOAD_BALANCED = "load_balanced"    # Équilibrage de charge
    MINIMAL_DELAY = "minimal_delay"    # Minimiser le délai de bout en bout


@dataclass
class CostThresholds:
    """Seuils pour le calcul des coûts"""
    # Seuils de bande passante (% d'utilisation)
    bw_low: float = 30.0
    bw_medium: float = 60.0
    bw_high: float = 80.0
    bw_critical: float = 90.0
    
    # Seuils de latence (ms)
    latency_low: float = 10.0
    latency_medium: float = 50.0
    latency_high: float = 100.0
    latency_critical: float = 200.0
    
    # Seuils de perte de paquets (%)
    loss_low: float = 0.1
    loss_medium: float = 1.0
    loss_high: float = 5.0
    loss_critical: float = 10.0


@dataclass
class CostCalculationResult:
    """Résultat du calcul de coût pour un lien"""
    link_name: str
    current_cost: int
    calculated_cost: int
    should_update: bool
    reason: str
    metrics_summary: Dict


class CostCalculator:
    """Calcule les coûts OSPF optimaux basés sur les métriques réseau"""
    
    def __init__(self, config: Dict):
        """
        Args:
            config: Configuration depuis routers.yaml (section cost_factors et thresholds)
        """
        self.base_cost = config.get('base_cost', 10)
        self.min_cost = config.get('min_cost', 1)
        self.max_cost = config.get('max_cost', 65535)
        
        # Poids des différentes métriques
        multipliers = config.get('multipliers', {})
        self.bw_weight = multipliers.get('bandwidth_weight', 0.5)
        self.latency_weight = multipliers.get('latency_weight', 0.3)
        self.loss_weight = multipliers.get('packet_loss_weight', 0.2)
        
        # Charger les seuils
        thresholds_config = config.get('thresholds', {})
        self.thresholds = self._load_thresholds(thresholds_config)
        
        # Seuil de changement minimum (évite les oscillations)
        self.min_change_threshold = config.get('min_change_threshold', 5)
        
        # Historique des coûts pour détecter les oscillations
        self.cost_history: Dict[str, List[int]] = {}
        
    def _load_thresholds(self, config: Dict) -> CostThresholds:
        """Charge les seuils depuis la configuration"""
        bw = config.get('bandwidth', {})
        latency = config.get('latency', {})
        loss = config.get('packet_loss', {})
        
        return CostThresholds(
            bw_low=bw.get('low', 30),
            bw_medium=bw.get('medium', 60),
            bw_high=bw.get('high', 80),
            bw_critical=bw.get('critical', 90),
            latency_low=latency.get('low', 10),
            latency_medium=latency.get('medium', 50),
            latency_high=latency.get('high', 100),
            latency_critical=latency.get('critical', 200),
            loss_low=loss.get('low', 0.1),
            loss_medium=loss.get('medium', 1),
            loss_high=loss.get('high', 5),
            loss_critical=loss.get('critical', 10)
        )
        
    def calculate_bandwidth_factor(self, utilization: float) -> float:
        """
        Calcule le facteur de coût basé sur l'utilisation de la bande passante
        
        Args:
            utilization: Pourcentage d'utilisation (0-100)
            
        Returns:
            Facteur multiplicateur (1.0 = normal, >1.0 = pénalité)
        """
        if utilization < self.thresholds.bw_low:
            return 1.0  # Pas de pénalité
        elif utilization < self.thresholds.bw_medium:
            # Augmentation linéaire légère
            return 1.0 + (utilization - self.thresholds.bw_low) / 100
        elif utilization < self.thresholds.bw_high:
            # Augmentation modérée
            return 1.5 + (utilization - self.thresholds.bw_medium) / 50
        elif utilization < self.thresholds.bw_critical:
            # Augmentation importante
            return 2.5 + (utilization - self.thresholds.bw_high) / 20
        else:
            # Pénalité maximale pour éviter le lien
            return 5.0 + (utilization - self.thresholds.bw_critical) / 10
            
    def calculate_latency_factor(self, latency_ms: float) -> float:
        """
        Calcule le facteur de coût basé sur la latence
        
        Args:
            latency_ms: Latence en millisecondes
            
        Returns:
            Facteur multiplicateur
        """
        if latency_ms < self.thresholds.latency_low:
            return 1.0
        elif latency_ms < self.thresholds.latency_medium:
            return 1.0 + (latency_ms - self.thresholds.latency_low) / 100
        elif latency_ms < self.thresholds.latency_high:
            return 1.5 + (latency_ms - self.thresholds.latency_medium) / 50
        elif latency_ms < self.thresholds.latency_critical:
            return 2.5 + (latency_ms - self.thresholds.latency_high) / 25
        else:
            return 5.0 + (latency_ms - self.thresholds.latency_critical) / 50
            
    def calculate_packet_loss_factor(self, loss_percent: float) -> float:
        """
        Calcule le facteur de coût basé sur la perte de paquets
        
        Args:
            loss_percent: Pourcentage de perte de paquets
            
        Returns:
            Facteur multiplicateur (perte = forte pénalité)
        """
        if loss_percent < self.thresholds.loss_low:
            return 1.0
        elif loss_percent < self.thresholds.loss_medium:
            # Perte légère mais notable
            return 1.5
        elif loss_percent < self.thresholds.loss_high:
            # Perte significative
            return 3.0
        elif loss_percent < self.thresholds.loss_critical:
            # Perte importante
            return 6.0
        else:
            # Lien très dégradé
            return 10.0
            
    def calculate_composite_cost(self, metrics: LinkMetrics) -> int:
        """
        Calcule le coût OSPF en utilisant toutes les métriques pondérées
        
        Formule: cost = base_cost * (bw_factor * bw_weight + latency_factor * latency_weight + loss_factor * loss_weight)
        
        Args:
            metrics: Métriques du lien
            
        Returns:
            Coût OSPF calculé
        """
        # Calculer les facteurs individuels
        bw_factor = self.calculate_bandwidth_factor(metrics.bandwidth_utilization)
        latency_factor = self.calculate_latency_factor(metrics.latency_ms)
        loss_factor = self.calculate_packet_loss_factor(metrics.packet_loss_percent)
        
        # Calculer le facteur composite pondéré
        composite_factor = (
            bw_factor * self.bw_weight +
            latency_factor * self.latency_weight +
            loss_factor * self.loss_weight
        )
        
        # Calculer le coût final
        cost = int(self.base_cost * composite_factor)
        
        # Appliquer les limites min/max
        cost = max(self.min_cost, min(self.max_cost, cost))
        
        return cost
        
    def calculate_bandwidth_only_cost(self, metrics: LinkMetrics) -> int:
        """Calcule le coût basé uniquement sur la bande passante"""
        factor = self.calculate_bandwidth_factor(metrics.bandwidth_utilization)
        cost = int(self.base_cost * factor)
        return max(self.min_cost, min(self.max_cost, cost))
        
    def calculate_latency_only_cost(self, metrics: LinkMetrics) -> int:
        """Calcule le coût basé uniquement sur la latence"""
        factor = self.calculate_latency_factor(metrics.latency_ms)
        cost = int(self.base_cost * factor)
        return max(self.min_cost, min(self.max_cost, cost))
        
    def calculate_cost(self, metrics: LinkMetrics, 
                       strategy: OptimizationStrategy = OptimizationStrategy.COMPOSITE) -> CostCalculationResult:
        """
        Calcule le coût OSPF optimal selon la stratégie choisie
        
        Args:
            metrics: Métriques du lien
            strategy: Stratégie d'optimisation à utiliser
            
        Returns:
            CostCalculationResult avec le coût recommandé
        """
        # Calculer le coût selon la stratégie
        if strategy == OptimizationStrategy.BANDWIDTH_BASED:
            new_cost = self.calculate_bandwidth_only_cost(metrics)
            reason_detail = f"Utilisation BW: {metrics.bandwidth_utilization:.1f}%"
        elif strategy == OptimizationStrategy.LATENCY_BASED:
            new_cost = self.calculate_latency_only_cost(metrics)
            reason_detail = f"Latence: {metrics.latency_ms:.1f}ms"
        else:  # COMPOSITE par défaut
            new_cost = self.calculate_composite_cost(metrics)
            reason_detail = (f"BW: {metrics.bandwidth_utilization:.1f}%, "
                           f"Latence: {metrics.latency_ms:.1f}ms, "
                           f"Perte: {metrics.packet_loss_percent:.2f}%")
        
        # Vérifier si le changement est significatif
        current_cost = metrics.current_ospf_cost
        cost_diff = abs(new_cost - current_cost)
        should_update = cost_diff >= self.min_change_threshold
        
        # Vérifier les oscillations
        if should_update and self._detect_oscillation(metrics.link_name, new_cost):
            should_update = False
            reason = f"Oscillation détectée, pas de changement"
        elif should_update:
            reason = f"Changement de {current_cost} → {new_cost} ({reason_detail})"
        else:
            reason = f"Changement insuffisant ({cost_diff} < {self.min_change_threshold})"
            
        # Enregistrer dans l'historique
        if metrics.link_name not in self.cost_history:
            self.cost_history[metrics.link_name] = []
        self.cost_history[metrics.link_name].append(new_cost)
        if len(self.cost_history[metrics.link_name]) > 10:
            self.cost_history[metrics.link_name] = self.cost_history[metrics.link_name][-10:]
            
        return CostCalculationResult(
            link_name=metrics.link_name,
            current_cost=current_cost,
            calculated_cost=new_cost,
            should_update=should_update,
            reason=reason,
            metrics_summary={
                'bandwidth_utilization': metrics.bandwidth_utilization,
                'latency_ms': metrics.latency_ms,
                'packet_loss_percent': metrics.packet_loss_percent,
                'jitter_ms': metrics.jitter_ms
            }
        )
        
    def _detect_oscillation(self, link_name: str, new_cost: int, window: int = 5) -> bool:
        """
        Détecte si le coût oscille (augmente puis diminue répétitivement)
        
        Args:
            link_name: Nom du lien
            new_cost: Nouveau coût proposé
            window: Nombre de valeurs à considérer
            
        Returns:
            True si oscillation détectée
        """
        if link_name not in self.cost_history:
            return False
            
        history = self.cost_history[link_name][-window:]
        if len(history) < 4:
            return False
            
        # Compter les changements de direction
        directions = []
        for i in range(1, len(history)):
            if history[i] > history[i-1]:
                directions.append(1)  # Augmentation
            elif history[i] < history[i-1]:
                directions.append(-1)  # Diminution
            else:
                directions.append(0)
                
        # Si on a plus de 2 changements de direction, c'est une oscillation
        direction_changes = 0
        for i in range(1, len(directions)):
            if directions[i] != 0 and directions[i-1] != 0 and directions[i] != directions[i-1]:
                direction_changes += 1
                
        return direction_changes >= 2
        
    def calculate_all_costs(self, metrics_list: List[LinkMetrics],
                           strategy: OptimizationStrategy = OptimizationStrategy.COMPOSITE) -> List[CostCalculationResult]:
        """
        Calcule les coûts pour tous les liens
        
        Args:
            metrics_list: Liste des métriques de tous les liens
            strategy: Stratégie d'optimisation
            
        Returns:
            Liste des résultats de calcul
        """
        results = []
        for metrics in metrics_list:
            result = self.calculate_cost(metrics, strategy)
            results.append(result)
        return results
        
    def get_optimization_summary(self, results: List[CostCalculationResult]) -> Dict:
        """
        Génère un résumé des optimisations proposées
        
        Args:
            results: Liste des résultats de calcul
            
        Returns:
            Dictionnaire avec le résumé
        """
        updates_needed = [r for r in results if r.should_update]
        
        return {
            'total_links': len(results),
            'links_to_update': len(updates_needed),
            'links_stable': len(results) - len(updates_needed),
            'updates': [
                {
                    'link': r.link_name,
                    'current': r.current_cost,
                    'new': r.calculated_cost,
                    'reason': r.reason
                }
                for r in updates_needed
            ],
            'all_results': [
                {
                    'link': r.link_name,
                    'current': r.current_cost,
                    'calculated': r.calculated_cost,
                    'will_update': r.should_update,
                    'metrics': r.metrics_summary
                }
                for r in results
            ]
        }
