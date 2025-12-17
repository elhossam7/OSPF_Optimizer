"""
Module de collecte des métriques réseau pour FRRouting
Collecte: bande passante, latence, perte de paquets, état des interfaces
Adapté pour les conteneurs Docker FRR dans GNS3
"""

import re
import time
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import subprocess
import platform


@dataclass
class InterfaceMetrics:
    """Métriques d'une interface réseau"""
    interface_name: str
    ip_address: str
    status: str  # up/down
    bandwidth: int  # en Kbps (par défaut 100000 pour 100Mbps)
    rx_bytes: int
    tx_bytes: int
    rx_packets: int
    tx_packets: int
    rx_errors: int
    tx_errors: int
    rx_dropped: int
    tx_dropped: int
    utilization_percent: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LinkMetrics:
    """Métriques d'un lien entre deux routeurs"""
    link_name: str
    source_router: str
    dest_router: str
    latency_ms: float
    packet_loss_percent: float
    jitter_ms: float
    bandwidth_utilization: float
    current_ospf_cost: int
    recommended_cost: int
    timestamp: datetime = field(default_factory=datetime.now)


class FRRMetricsCollector:
    """Collecteur de métriques réseau pour FRRouting via Docker"""
    
    def __init__(self, connection_handler):
        """
        Args:
            connection_handler: Instance de FRRRouterConnection
        """
        self.connection = connection_handler
        self.metrics_history: Dict[str, List[LinkMetrics]] = {}
        
        # Cache pour calculer le débit (besoin de 2 mesures)
        self.traffic_cache: Dict[str, Dict] = {}
        self.last_measurement_time: Dict[str, float] = {}
        
    def collect_interface_stats(self, router_name: str, interface: str) -> Optional[InterfaceMetrics]:
        """
        Collecte les statistiques d'une interface via /proc/net/dev
        
        Args:
            router_name: Nom du routeur
            interface: Nom de l'interface
            
        Returns:
            InterfaceMetrics ou None
        """
        # Obtenir les stats de trafic
        traffic = self.connection.get_interface_traffic(router_name, interface)
        
        if not traffic:
            return None
            
        # Obtenir le statut de l'interface
        status_output = self.connection.execute_command(
            router_name, 
            f"ip link show {interface} | grep -o 'state [A-Z]*'"
        )
        status = "up" if status_output and "UP" in status_output else "down"
        
        # Obtenir l'adresse IP
        ip_output = self.connection.execute_command(
            router_name,
            f"ip addr show {interface} | grep 'inet ' | awk '{{print $2}}' | cut -d'/' -f1"
        )
        ip_address = ip_output.strip() if ip_output else "N/A"
        
        # Calculer l'utilisation basée sur le delta de trafic
        utilization = self._calculate_utilization(router_name, interface, traffic)
        
        return InterfaceMetrics(
            interface_name=interface,
            ip_address=ip_address,
            status=status,
            bandwidth=100000,  # 100 Mbps par défaut
            rx_bytes=traffic.get('rx_bytes', 0),
            tx_bytes=traffic.get('tx_bytes', 0),
            rx_packets=traffic.get('rx_packets', 0),
            tx_packets=traffic.get('tx_packets', 0),
            rx_errors=traffic.get('rx_errors', 0),
            tx_errors=traffic.get('tx_errors', 0),
            rx_dropped=traffic.get('rx_dropped', 0),
            tx_dropped=traffic.get('tx_dropped', 0),
            utilization_percent=utilization
        )
        
    def _calculate_utilization(self, router_name: str, interface: str, 
                               current_traffic: Dict) -> float:
        """
        Calcule l'utilisation de bande passante basée sur le delta de trafic
        
        Nécessite deux mesures pour calculer le débit
        """
        cache_key = f"{router_name}:{interface}"
        current_time = time.time()
        
        if cache_key not in self.traffic_cache:
            # Première mesure, stocker et retourner 0
            self.traffic_cache[cache_key] = current_traffic
            self.last_measurement_time[cache_key] = current_time
            return 0.0
            
        # Calculer le delta
        last_traffic = self.traffic_cache[cache_key]
        last_time = self.last_measurement_time[cache_key]
        time_delta = current_time - last_time
        
        if time_delta <= 0:
            return 0.0
            
        # Delta de bytes
        rx_delta = current_traffic.get('rx_bytes', 0) - last_traffic.get('rx_bytes', 0)
        tx_delta = current_traffic.get('tx_bytes', 0) - last_traffic.get('tx_bytes', 0)
        
        # Gérer le cas du compteur qui a été réinitialisé
        if rx_delta < 0:
            rx_delta = current_traffic.get('rx_bytes', 0)
        if tx_delta < 0:
            tx_delta = current_traffic.get('tx_bytes', 0)
            
        # Calculer le débit en bits/sec
        rx_rate = (rx_delta * 8) / time_delta  # bits/sec
        tx_rate = (tx_delta * 8) / time_delta
        
        # Utiliser le max des deux directions
        max_rate = max(rx_rate, tx_rate)
        
        # Calculer le pourcentage (100 Mbps = 100000000 bits/sec)
        bandwidth_bps = 100000000  # 100 Mbps
        utilization = (max_rate / bandwidth_bps) * 100
        
        # Mettre à jour le cache
        self.traffic_cache[cache_key] = current_traffic
        self.last_measurement_time[cache_key] = current_time
        
        return round(min(utilization, 100.0), 2)
        
    def measure_latency(self, source_router: str, dest_ip: str, 
                        count: int = 5) -> Tuple[float, float, float]:
        """
        Mesure la latence vers une destination via ping
        
        Args:
            source_router: Routeur source
            dest_ip: IP de destination
            count: Nombre de pings
            
        Returns:
            Tuple (latence_moyenne_ms, packet_loss_percent, jitter_ms)
        """
        output = self.connection.ping(source_router, dest_ip, count)
        
        if not output:
            return (999.0, 100.0, 0.0)
            
        return self._parse_ping_output(output)
        
    def _parse_ping_output(self, output: str) -> Tuple[float, float, float]:
        """
        Parse la sortie de ping Linux
        
        Formats supportés:
        - "rtt min/avg/max/mdev = 1.234/2.345/3.456/0.567 ms"
        - "X packets transmitted, Y received, Z% packet loss"
        """
        # Extraire les stats RTT
        rtt_match = re.search(
            r'rtt min/avg/max/mdev\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', 
            output
        )
        
        if rtt_match:
            min_rtt = float(rtt_match.group(1))
            avg_rtt = float(rtt_match.group(2))
            max_rtt = float(rtt_match.group(3))
            mdev = float(rtt_match.group(4))  # jitter approximatif
        else:
            # Essayer de parser les temps individuels
            times = re.findall(r'time[=<]([\d.]+)', output)
            if times:
                times_float = [float(t) for t in times]
                avg_rtt = statistics.mean(times_float)
                mdev = max(times_float) - min(times_float) if len(times_float) > 1 else 0
            else:
                avg_rtt = 999.0
                mdev = 0.0
                
        # Extraire la perte de paquets
        loss_match = re.search(r'(\d+)%\s*packet loss', output)
        if loss_match:
            packet_loss = float(loss_match.group(1))
        else:
            # Calculer à partir de transmitted/received
            stats_match = re.search(r'(\d+)\s*packets transmitted,\s*(\d+)\s*received', output)
            if stats_match:
                transmitted = int(stats_match.group(1))
                received = int(stats_match.group(2))
                packet_loss = ((transmitted - received) / transmitted) * 100 if transmitted > 0 else 100.0
            else:
                packet_loss = 0.0
                
        return (avg_rtt, packet_loss, mdev)
        
    def get_ospf_cost(self, router_name: str, interface: str) -> int:
        """
        Récupère le coût OSPF actuel d'une interface
        """
        return self.connection.get_ospf_cost(router_name, interface)
        
    def get_ospf_neighbors(self, router_name: str) -> List[Dict]:
        """
        Récupère la liste des voisins OSPF
        
        Returns:
            Liste des voisins avec leurs états
        """
        neighbors = []
        output = self.connection.get_ospf_neighbors(router_name)
        
        if not output:
            return neighbors
            
        # Parser la sortie FRR
        # Format: Neighbor ID  Pri State  Dead Time Address  Interface  RXmtL RqstL DBsmL
        lines = output.strip().split('\n')
        
        for line in lines:
            # Ignorer les lignes d'en-tête
            if 'Neighbor ID' in line or not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 5:
                neighbors.append({
                    'neighbor_id': parts[0],
                    'priority': parts[1],
                    'state': parts[2],
                    'dead_time': parts[3],
                    'address': parts[4],
                    'interface': parts[5] if len(parts) > 5 else 'N/A'
                })
                
        return neighbors
        
    def collect_link_metrics(self, link_config: Dict) -> LinkMetrics:
        """
        Collecte toutes les métriques pour un lien spécifique
        
        Args:
            link_config: Configuration du lien depuis routers.yaml
            
        Returns:
            LinkMetrics avec toutes les métriques collectées
        """
        source_router = link_config['source_router']
        dest_router = link_config['dest_router']
        source_interface = link_config['source_interface']
        dest_ip = link_config.get('dest_ip', '')
        
        # Obtenir les stats de l'interface source
        interface_stats = self.collect_interface_stats(source_router, source_interface)
        
        # Calculer l'utilisation de bande passante
        if interface_stats:
            bandwidth_util = interface_stats.utilization_percent
        else:
            bandwidth_util = 0.0
        
        # Mesurer la latence et la perte de paquets
        if dest_ip:
            latency, packet_loss, jitter = self.measure_latency(source_router, dest_ip)
        else:
            latency, packet_loss, jitter = 0.0, 0.0, 0.0
        
        # Obtenir le coût OSPF actuel
        current_cost = self.get_ospf_cost(source_router, source_interface)
        
        return LinkMetrics(
            link_name=link_config['name'],
            source_router=source_router,
            dest_router=dest_router,
            latency_ms=latency,
            packet_loss_percent=packet_loss,
            jitter_ms=jitter,
            bandwidth_utilization=bandwidth_util,
            current_ospf_cost=current_cost,
            recommended_cost=current_cost  # Sera calculé par l'optimiseur
        )
        
    def collect_all_metrics(self, monitored_links: List[Dict]) -> List[LinkMetrics]:
        """
        Collecte les métriques pour tous les liens surveillés
        
        Args:
            monitored_links: Liste des liens à surveiller
            
        Returns:
            Liste de LinkMetrics pour chaque lien
        """
        all_metrics = []
        
        for link in monitored_links:
            try:
                metrics = self.collect_link_metrics(link)
                all_metrics.append(metrics)
                
                # Stocker dans l'historique
                if link['name'] not in self.metrics_history:
                    self.metrics_history[link['name']] = []
                self.metrics_history[link['name']].append(metrics)
                
                # Garder seulement les 100 dernières mesures
                if len(self.metrics_history[link['name']]) > 100:
                    self.metrics_history[link['name']] = self.metrics_history[link['name']][-100:]
                    
            except Exception as e:
                print(f"Erreur lors de la collecte des métriques pour {link['name']}: {e}")
                
        return all_metrics
        
    def get_average_metrics(self, link_name: str, window: int = 10) -> Optional[LinkMetrics]:
        """
        Calcule les métriques moyennes sur une fenêtre glissante
        """
        if link_name not in self.metrics_history:
            return None
            
        history = self.metrics_history[link_name][-window:]
        if not history:
            return None
            
        return LinkMetrics(
            link_name=link_name,
            source_router=history[-1].source_router,
            dest_router=history[-1].dest_router,
            latency_ms=statistics.mean([m.latency_ms for m in history]),
            packet_loss_percent=statistics.mean([m.packet_loss_percent for m in history]),
            jitter_ms=statistics.mean([m.jitter_ms for m in history]),
            bandwidth_utilization=statistics.mean([m.bandwidth_utilization for m in history]),
            current_ospf_cost=history[-1].current_ospf_cost,
            recommended_cost=history[-1].recommended_cost
        )


class LocalMetricsCollector:
    """
    Collecteur de métriques local pour tests sans connexion aux routeurs
    Utilise ping depuis la machine locale
    """
    
    def __init__(self):
        self.is_windows = platform.system().lower() == 'windows'
        
    def ping(self, host: str, count: int = 4) -> Tuple[float, float, float]:
        """
        Effectue un ping local vers un hôte
        
        Returns:
            Tuple (latence_ms, packet_loss_percent, jitter_ms)
        """
        if self.is_windows:
            cmd = ['ping', '-n', str(count), host]
        else:
            cmd = ['ping', '-c', str(count), host]
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = result.stdout
            
            # Parser la sortie
            if self.is_windows:
                # Windows: "Minimum = Xms, Maximum = Yms, Moyenne = Zms"
                avg_match = re.search(r'(Moyenne|Average)\s*=\s*(\d+)', output)
                latency = float(avg_match.group(2)) if avg_match else 999.0
                
                loss_match = re.search(r'\((\d+)%\s*(perte|loss)', output)
                packet_loss = float(loss_match.group(1)) if loss_match else 0.0
            else:
                # Linux
                rtt_match = re.search(
                    r'rtt min/avg/max/mdev\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', 
                    output
                )
                if rtt_match:
                    latency = float(rtt_match.group(2))
                    jitter = float(rtt_match.group(4))
                else:
                    latency = 999.0
                    jitter = 0.0
                    
                loss_match = re.search(r'(\d+)%\s*packet loss', output)
                packet_loss = float(loss_match.group(1)) if loss_match else 0.0
                
                return (latency, packet_loss, jitter)
                
            return (latency, packet_loss, 0.0)
            
        except subprocess.TimeoutExpired:
            return (999.0, 100.0, 0.0)
        except Exception as e:
            print(f"Erreur ping vers {host}: {e}")
            return (999.0, 100.0, 0.0)


# Alias pour compatibilité
MetricsCollector = FRRMetricsCollector
