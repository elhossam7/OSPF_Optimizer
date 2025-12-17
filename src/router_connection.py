"""
Module de connexion aux routeurs FRRouting via Docker exec ou SSH
Supporte les conteneurs Docker FRR dans GNS3
"""

import subprocess
import time
import re
from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RouterCredentials:
    """Informations de connexion pour un routeur FRR"""
    hostname: str
    container_name: str
    username: str = "root"
    password: str = ""
    device_type: str = "linux"
    port: int = 22


class FRRRouterConnection:
    """
    Gestionnaire de connexions vers les routeurs FRRouting
    Supporte docker exec (recommandé pour GNS3) et SSH
    """
    
    def __init__(self, global_config: Dict):
        """
        Args:
            global_config: Configuration globale depuis routers.yaml
        """
        self.connection_method = global_config.get('connection_method', 'docker_exec')
        self.default_username = global_config.get('username', 'root')
        self.default_password = global_config.get('password', '')
        self.timeout = global_config.get('timeout', 30)
        
        # Cache des routeurs configurés
        self.routers: Dict[str, RouterCredentials] = {}
        
        # Pour SSH (optionnel)
        self.ssh_connections = {}
        
    def add_router(self, name: str, config: Dict):
        """
        Ajoute un routeur à la liste des routeurs gérés
        
        Args:
            name: Nom du routeur
            config: Configuration du routeur
        """
        self.routers[name] = RouterCredentials(
            hostname=config.get('hostname', name),
            container_name=config.get('container_name', name),
            username=config.get('username', self.default_username),
            password=config.get('password', self.default_password)
        )
        logger.debug(f"Routeur {name} ajouté (container: {config.get('container_name', name)})")
        
    def connect(self, router_name: str) -> bool:
        """
        Vérifie la connexion à un routeur
        Pour docker_exec, vérifie que le conteneur est accessible
        
        Args:
            router_name: Nom du routeur
            
        Returns:
            True si connexion possible, False sinon
        """
        if router_name not in self.routers:
            logger.error(f"Routeur {router_name} non configuré")
            return False
            
        if self.connection_method == 'docker_exec':
            # Vérifier que le conteneur répond
            result = self._docker_exec(router_name, "echo ok", timeout=5)
            return result is not None and "ok" in result
        else:
            # SSH - à implémenter si nécessaire
            return self._ssh_connect(router_name)
            
    def disconnect(self, router_name: str):
        """Ferme la connexion à un routeur (principalement pour SSH)"""
        if router_name in self.ssh_connections:
            try:
                self.ssh_connections[router_name].disconnect()
            except:
                pass
            del self.ssh_connections[router_name]
            
    def disconnect_all(self):
        """Ferme toutes les connexions SSH"""
        for router_name in list(self.ssh_connections.keys()):
            self.disconnect(router_name)
            
    def _docker_exec(self, router_name: str, command: str, timeout: int = None) -> Optional[str]:
        """
        Exécute une commande dans un conteneur Docker via docker exec
        
        Args:
            router_name: Nom du routeur
            command: Commande à exécuter
            timeout: Timeout en secondes
            
        Returns:
            Sortie de la commande ou None en cas d'erreur
        """
        if router_name not in self.routers:
            return None
            
        container = self.routers[router_name].container_name
        timeout = timeout or self.timeout
        
        try:
            # Construire la commande docker exec
            docker_cmd = ['docker', 'exec', container, 'sh', '-c', command]
            
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                logger.warning(f"Commande échouée sur {router_name}: {result.stderr}")
                
            return result.stdout
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout lors de l'exécution sur {router_name}")
            return None
        except FileNotFoundError:
            logger.error("Docker n'est pas installé ou pas dans le PATH")
            return None
        except Exception as e:
            logger.error(f"Erreur docker exec sur {router_name}: {e}")
            return None
            
    def _ssh_connect(self, router_name: str) -> bool:
        """Connexion SSH (fallback si docker exec non disponible)"""
        try:
            from netmiko import ConnectHandler
            
            creds = self.routers[router_name]
            device_params = {
                'device_type': 'linux',
                'host': creds.hostname,
                'username': creds.username,
                'password': creds.password,
                'port': creds.port,
                'timeout': self.timeout,
            }
            
            connection = ConnectHandler(**device_params)
            self.ssh_connections[router_name] = connection
            return True
            
        except Exception as e:
            logger.error(f"Erreur SSH vers {router_name}: {e}")
            return False
            
    def execute_command(self, router_name: str, command: str) -> Optional[str]:
        """
        Exécute une commande sur un routeur FRR
        
        Args:
            router_name: Nom du routeur
            command: Commande à exécuter (shell ou vtysh)
            
        Returns:
            Sortie de la commande ou None en cas d'erreur
        """
        if self.connection_method == 'docker_exec':
            return self._docker_exec(router_name, command)
        else:
            if router_name not in self.ssh_connections:
                if not self._ssh_connect(router_name):
                    return None
            return self.ssh_connections[router_name].send_command(command)
            
    def execute_vtysh(self, router_name: str, commands: List[str]) -> Optional[str]:
        """
        Exécute des commandes vtysh sur un routeur FRR
        
        Args:
            router_name: Nom du routeur
            commands: Liste de commandes vtysh
            
        Returns:
            Sortie des commandes
        """
        # Construire la commande vtysh
        vtysh_cmd = 'vtysh'
        for cmd in commands:
            vtysh_cmd += f' -c "{cmd}"'
            
        return self.execute_command(router_name, vtysh_cmd)
        
    def get_ospf_neighbors(self, router_name: str) -> Optional[str]:
        """Récupère les voisins OSPF via vtysh"""
        return self.execute_vtysh(router_name, ['show ip ospf neighbor'])
        
    def get_ospf_interface(self, router_name: str, interface: str = None) -> Optional[str]:
        """Récupère les infos OSPF d'une interface"""
        if interface:
            return self.execute_vtysh(router_name, [f'show ip ospf interface {interface}'])
        return self.execute_vtysh(router_name, ['show ip ospf interface'])
        
    def get_interface_stats(self, router_name: str, interface: str = None) -> Optional[str]:
        """
        Récupère les statistiques d'interface via /proc ou ip
        FRR n'a pas de commande 'show interfaces' comme Cisco
        """
        if interface:
            # Utiliser ip -s link show
            cmd = f"ip -s link show {interface}"
        else:
            cmd = "ip -s link show"
        return self.execute_command(router_name, cmd)
        
    def get_interface_traffic(self, router_name: str, interface: str) -> Dict:
        """
        Récupère le trafic d'une interface depuis /proc/net/dev
        
        Returns:
            Dict avec rx_bytes, tx_bytes, rx_packets, tx_packets, etc.
        """
        cmd = f"cat /proc/net/dev | grep {interface}"
        output = self.execute_command(router_name, cmd)
        
        if not output:
            return {}
            
        # Parser la sortie de /proc/net/dev
        # Format: iface: rx_bytes rx_packets rx_errs rx_drop ... tx_bytes tx_packets tx_errs tx_drop ...
        try:
            parts = output.split()
            if len(parts) >= 17:
                return {
                    'rx_bytes': int(parts[1]),
                    'rx_packets': int(parts[2]),
                    'rx_errors': int(parts[3]),
                    'rx_dropped': int(parts[4]),
                    'tx_bytes': int(parts[9]),
                    'tx_packets': int(parts[10]),
                    'tx_errors': int(parts[11]),
                    'tx_dropped': int(parts[12])
                }
        except (IndexError, ValueError) as e:
            logger.error(f"Erreur parsing traffic stats: {e}")
            
        return {}
        
    def ping(self, router_name: str, dest_ip: str, count: int = 5) -> Optional[str]:
        """Exécute un ping depuis un routeur"""
        cmd = f"ping -c {count} -W 2 {dest_ip}"
        return self.execute_command(router_name, cmd)
        
    def set_ospf_cost(self, router_name: str, interface: str, cost: int) -> bool:
        """
        Modifie le coût OSPF d'une interface via vtysh
        
        Args:
            router_name: Nom du routeur
            interface: Nom de l'interface
            cost: Nouveau coût OSPF
            
        Returns:
            True si succès, False sinon
        """
        commands = [
            'configure terminal',
            f'interface {interface}',
            f'ip ospf cost {cost}',
            'exit',
            'exit'
        ]
        
        result = self.execute_vtysh(router_name, commands)
        
        if result is not None:
            logger.info(f"✓ Coût OSPF de {interface} sur {router_name} modifié à {cost}")
            return True
        else:
            logger.error(f"✗ Échec modification coût OSPF sur {router_name}.{interface}")
            return False
            
    def get_ospf_cost(self, router_name: str, interface: str) -> int:
        """
        Récupère le coût OSPF actuel d'une interface
        
        Args:
            router_name: Nom du routeur
            interface: Nom de l'interface
            
        Returns:
            Coût OSPF actuel ou 0 si non trouvé
        """
        output = self.get_ospf_interface(router_name, interface)
        
        if not output:
            return 0
            
        # Parser la sortie pour trouver le coût
        # Format FRR: "Cost: 10"
        cost_match = re.search(r'Cost:\s*(\d+)', output)
        if cost_match:
            return int(cost_match.group(1))
            
        return 0
        
    def save_config(self, router_name: str) -> bool:
        """
        Sauvegarde la configuration FRR
        Note: Dans Docker, la config est perdue au redémarrage
        sauf si un volume est monté
        
        Returns:
            True si succès
        """
        result = self.execute_vtysh(router_name, ['write memory'])
        if result is not None:
            logger.info(f"✓ Configuration sauvegardée sur {router_name}")
            return True
        return False


class MockFRRConnection:
    """
    Connexion simulée pour les tests sans routeurs réels
    Simule les réponses FRRouting
    """
    
    def __init__(self, global_config: Dict):
        self.routers = {}
        self.interface_stats = {}
        self.ospf_costs = {}
        self._init_mock_data()
        
    def _init_mock_data(self):
        """Initialise les données simulées"""
        import random
        
        # Stats par interface (simulées)
        interfaces = ['eth0', 'eth1', 'eth2']
        for iface in interfaces:
            self.interface_stats[iface] = {
                'rx_bytes': random.randint(1000000, 100000000),
                'tx_bytes': random.randint(1000000, 100000000),
                'rx_packets': random.randint(1000, 100000),
                'tx_packets': random.randint(1000, 100000),
                'rx_errors': random.randint(0, 10),
                'tx_errors': random.randint(0, 10),
            }
            self.ospf_costs[iface] = 10
            
    def add_router(self, name: str, config: Dict):
        self.routers[name] = config
        
    def connect(self, router_name: str) -> bool:
        return router_name in self.routers
        
    def disconnect(self, router_name: str):
        pass
        
    def disconnect_all(self):
        pass
        
    def execute_command(self, router_name: str, command: str) -> Optional[str]:
        """Retourne des données simulées selon la commande"""
        import random
        
        if 'ip -s link show' in command:
            return self._mock_interface_stats(command)
        elif 'proc/net/dev' in command:
            return self._mock_proc_net_dev(command)
        elif 'ping' in command:
            return self._mock_ping()
        elif 'show ip ospf neighbor' in command:
            return self._mock_ospf_neighbor()
        elif 'show ip ospf interface' in command:
            return self._mock_ospf_interface(command)
        elif 'show ip route' in command:
            return self._mock_ip_route()
            
        return ""
        
    def execute_vtysh(self, router_name: str, commands: List[str]) -> Optional[str]:
        """Simule l'exécution vtysh"""
        cmd_str = ' '.join(commands)
        
        if 'show ip ospf neighbor' in cmd_str:
            return self._mock_ospf_neighbor()
        elif 'show ip ospf interface' in cmd_str:
            return self._mock_ospf_interface(cmd_str)
        elif 'ip ospf cost' in cmd_str:
            # Extraire l'interface et le coût
            match = re.search(r'interface (\S+).*ip ospf cost (\d+)', cmd_str)
            if match:
                iface, cost = match.groups()
                self.ospf_costs[iface] = int(cost)
            return ""
            
        return ""
        
    def _mock_interface_stats(self, command: str) -> str:
        import random
        # Simuler la sortie de 'ip -s link show'
        return f"""2: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP mode DEFAULT
    link/ether 02:42:0a:01:01:01 brd ff:ff:ff:ff:ff:ff
    RX: bytes  packets  errors  dropped overrun mcast
    {random.randint(10000000, 500000000)}  {random.randint(10000, 500000)}  0       0       0       0
    TX: bytes  packets  errors  dropped carrier collsns
    {random.randint(10000000, 500000000)}  {random.randint(10000, 500000)}  0       0       0       0"""
        
    def _mock_proc_net_dev(self, command: str) -> str:
        import random
        # Extraire le nom de l'interface
        match = re.search(r'grep (\S+)', command)
        iface = match.group(1) if match else 'eth1'
        
        rx_bytes = random.randint(10000000, 500000000)
        tx_bytes = random.randint(10000000, 500000000)
        
        return f"  {iface}: {rx_bytes} {random.randint(10000, 100000)} 0 0 0 0 0 0 {tx_bytes} {random.randint(10000, 100000)} 0 0 0 0 0 0"
        
    def _mock_ping(self) -> str:
        import random
        success = random.randint(4, 5)
        avg_time = random.uniform(1, 30)
        
        return f"""PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time={avg_time:.1f} ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time={avg_time+1:.1f} ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time={avg_time-0.5:.1f} ms
64 bytes from 10.0.0.2: icmp_seq=4 ttl=64 time={avg_time+0.3:.1f} ms
64 bytes from 10.0.0.2: icmp_seq=5 ttl=64 time={avg_time:.1f} ms

--- 10.0.0.2 ping statistics ---
5 packets transmitted, {success} received, {(5-success)*20}% packet loss, time 4005ms
rtt min/avg/max/mdev = {avg_time-1:.3f}/{avg_time:.3f}/{avg_time+2:.3f}/0.{random.randint(100,999)} ms"""
        
    def _mock_ospf_neighbor(self) -> str:
        return """
Neighbor ID     Pri State           Dead Time Address         Interface            RXmtL RqstL DBsmL
1.1.1.1           1 Full/DR         00:00:38 10.1.1.1        eth0:10.1.1.2            0     0     0
2.2.2.2           1 Full/Backup     00:00:35 10.0.0.2        eth1:10.0.0.1            0     0     0
3.3.3.3           1 Full/DROther    00:00:32 10.0.1.2        eth2:10.0.1.1            0     0     0"""
        
    def _mock_ospf_interface(self, command: str) -> str:
        import random
        # Extraire le nom de l'interface si spécifié
        match = re.search(r'interface (\S+)', command)
        iface = match.group(1) if match else 'eth1'
        
        cost = self.ospf_costs.get(iface, 10)
        
        return f"""eth1 is up
  ifindex 3, MTU 1500 bytes, BW 100000 Kbit <UP,BROADCAST,RUNNING,MULTICAST>
  Internet Address 10.0.0.1/30, Broadcast 10.0.0.3, Area 0.0.0.0
  MTU mismatch detection: enabled
  Router ID 11.11.11.11, Network Type BROADCAST, Cost: {cost}
  Transmit Delay is 1 sec, State DR, Priority 1
  Designated Router (ID) 11.11.11.11, Interface Address 10.0.0.1
  Backup Designated Router (ID) 22.22.22.22, Interface Address 10.0.0.2
  Multicast group memberships: OSPFAllRouters OSPFDesignatedRouters
  Timer intervals configured, Hello 10s, Dead 40s, Wait 40s, Retransmit 5
    Hello due in 00:00:0{random.randint(1,9)}s
  Neighbor Count is 1, Adjacent neighbor count is 1"""
        
    def _mock_ip_route(self) -> str:
        return """O   192.168.1.0/24 [110/20] via 10.1.1.1, eth0, weight 1, 00:05:23
O   192.168.2.0/24 [110/30] via 10.0.0.2, eth1, weight 1, 00:05:20
O   192.168.3.0/24 [110/40] via 10.0.1.2, eth2, weight 1, 00:05:18"""
        
    def get_ospf_neighbors(self, router_name: str) -> Optional[str]:
        return self._mock_ospf_neighbor()
        
    def get_ospf_interface(self, router_name: str, interface: str = None) -> Optional[str]:
        return self._mock_ospf_interface(f'interface {interface}' if interface else '')
        
    def get_interface_stats(self, router_name: str, interface: str = None) -> Optional[str]:
        return self._mock_interface_stats('')
        
    def get_interface_traffic(self, router_name: str, interface: str) -> Dict:
        import random
        return {
            'rx_bytes': random.randint(10000000, 500000000),
            'rx_packets': random.randint(10000, 100000),
            'rx_errors': random.randint(0, 5),
            'rx_dropped': 0,
            'tx_bytes': random.randint(10000000, 500000000),
            'tx_packets': random.randint(10000, 100000),
            'tx_errors': random.randint(0, 5),
            'tx_dropped': 0
        }
        
    def ping(self, router_name: str, dest_ip: str, count: int = 5) -> Optional[str]:
        return self._mock_ping()
        
    def set_ospf_cost(self, router_name: str, interface: str, cost: int) -> bool:
        self.ospf_costs[interface] = cost
        logger.info(f"[MOCK] ✓ Coût OSPF de {interface} sur {router_name} modifié à {cost}")
        return True
        
    def get_ospf_cost(self, router_name: str, interface: str) -> int:
        return self.ospf_costs.get(interface, 10)
        
    def save_config(self, router_name: str) -> bool:
        logger.info(f"[MOCK] ✓ Configuration sauvegardée sur {router_name}")
        return True


# Alias pour compatibilité
RouterConnection = FRRRouterConnection
MockRouterConnection = MockFRRConnection
