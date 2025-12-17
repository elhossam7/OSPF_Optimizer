#!/bin/bash
# =============================================================================
# GNS3 FRRouting Startup Commands
# Topology: OSPF_Optimisation_lab_env
# 
# UTILISATION:
# Copier-coller ces commandes dans le champ "Start command" de chaque nœud
# dans GNS3 (Edit -> Properties -> Start command)
#
# STRUCTURE OSPF:
#   Area 0 (Backbone): ABR1 <-> ABR2, ABR1 <-> ABR3, ABR2 <-> ABR3
#   Area 1: R1, R2 connectés via ABR1
#   Area 2: R3, R4 connectés via ABR2
# =============================================================================


# =============================================================================
# ABR1 - Area Border Router (Area 0 <-> Area 1)
# Interfaces:
#   eth0: 10.1.1.1/30 -> R1 (Area 1)
#   eth1: 10.0.0.1/30 -> ABR2 (Area 0)
#   eth2: 10.1.2.1/30 -> R2 (Area 1)
#   eth3: 10.0.1.1/30 -> ABR3 (Area 0)
# =============================================================================
# GNS3 Start Command pour ABR1:

ip addr add 10.1.1.1/30 dev eth0 && \
ip addr add 10.0.0.1/30 dev eth1 && \
ip addr add 10.1.2.1/30 dev eth2 && \
ip addr add 10.0.1.1/30 dev eth3 && \
ip link set eth0 up && \
ip link set eth1 up && \
ip link set eth2 up && \
ip link set eth3 up && \
sysctl -w net.ipv4.ip_forward=1 && \
cat > /etc/frr/frr.conf << 'EOF'
frr version 8.1
frr defaults traditional
hostname ABR1
log syslog informational
!
router ospf
 ospf router-id 11.11.11.11
 network 10.1.1.0/30 area 1
 network 10.0.0.0/30 area 0
 network 10.1.2.0/30 area 1
 network 10.0.1.0/30 area 0
!
line vty
!
EOF
/usr/lib/frr/frrinit.sh start


# =============================================================================
# ABR2 - Area Border Router (Area 0 <-> Area 2)
# Interfaces:
#   eth0: 10.2.1.1/30 -> R3 (Area 2)
#   eth1: 10.0.0.2/30 -> ABR1 (Area 0)
#   eth2: 10.2.2.1/30 -> R4 (Area 2)
#   eth3: 10.0.2.2/30 -> ABR3 (Area 0)
# =============================================================================
# GNS3 Start Command pour ABR2:

ip addr add 10.2.1.1/30 dev eth0 && \
ip addr add 10.0.0.2/30 dev eth1 && \
ip addr add 10.2.2.1/30 dev eth2 && \
ip addr add 10.0.2.2/30 dev eth3 && \
ip link set eth0 up && \
ip link set eth1 up && \
ip link set eth2 up && \
ip link set eth3 up && \
sysctl -w net.ipv4.ip_forward=1 && \
cat > /etc/frr/frr.conf << 'EOF'
frr version 8.1
frr defaults traditional
hostname ABR2
log syslog informational
!
router ospf
 ospf router-id 22.22.22.22
 network 10.2.1.0/30 area 2
 network 10.0.0.0/30 area 0
 network 10.2.2.0/30 area 2
 network 10.0.2.0/30 area 0
!
line vty
!
EOF
/usr/lib/frr/frrinit.sh start


# =============================================================================
# ABR3 - Backbone Transit Router (Area 0 only)
# Interfaces:
#   eth0: 10.0.1.2/30 -> ABR1 (Area 0)
#   eth1: 10.0.2.1/30 -> ABR2 (Area 0)
# =============================================================================
# GNS3 Start Command pour ABR3:

ip addr add 10.0.1.2/30 dev eth0 && \
ip addr add 10.0.2.1/30 dev eth1 && \
ip link set eth0 up && \
ip link set eth1 up && \
sysctl -w net.ipv4.ip_forward=1 && \
cat > /etc/frr/frr.conf << 'EOF'
frr version 8.1
frr defaults traditional
hostname ABR3
log syslog informational
!
router ospf
 ospf router-id 33.33.33.33
 network 10.0.1.0/30 area 0
 network 10.0.2.0/30 area 0
!
line vty
!
EOF
/usr/lib/frr/frrinit.sh start


# =============================================================================
# R1 - Internal Router (Area 1)
# Interfaces:
#   eth0: 192.168.1.1/24 -> PC1 (LAN)
#   eth1: 10.1.1.2/30 -> ABR1 (Area 1)
# =============================================================================
# GNS3 Start Command pour R1:

ip addr add 192.168.1.1/24 dev eth0 && \
ip addr add 10.1.1.2/30 dev eth1 && \
ip link set eth0 up && \
ip link set eth1 up && \
sysctl -w net.ipv4.ip_forward=1 && \
cat > /etc/frr/frr.conf << 'EOF'
frr version 8.1
frr defaults traditional
hostname R1
log syslog informational
!
router ospf
 ospf router-id 1.1.1.1
 network 192.168.1.0/24 area 1
 network 10.1.1.0/30 area 1
!
line vty
!
EOF
/usr/lib/frr/frrinit.sh start


# =============================================================================
# R2 - Internal Router (Area 1)
# Interfaces:
#   eth0: 192.168.2.1/24 -> PC2 (LAN)
#   eth1: 10.1.2.2/30 -> ABR1 (Area 1)
# =============================================================================
# GNS3 Start Command pour R2:

ip addr add 192.168.2.1/24 dev eth0 && \
ip addr add 10.1.2.2/30 dev eth1 && \
ip link set eth0 up && \
ip link set eth1 up && \
sysctl -w net.ipv4.ip_forward=1 && \
cat > /etc/frr/frr.conf << 'EOF'
frr version 8.1
frr defaults traditional
hostname R2
log syslog informational
!
router ospf
 ospf router-id 2.2.2.2
 network 192.168.2.0/24 area 1
 network 10.1.2.0/30 area 1
!
line vty
!
EOF
/usr/lib/frr/frrinit.sh start


# =============================================================================
# R3 - Internal Router (Area 2)
# Interfaces:
#   eth0: 192.168.3.1/24 -> PC3 (LAN)
#   eth1: 10.2.1.2/30 -> ABR2 (Area 2)
# =============================================================================
# GNS3 Start Command pour R3:

ip addr add 192.168.3.1/24 dev eth0 && \
ip addr add 10.2.1.2/30 dev eth1 && \
ip link set eth0 up && \
ip link set eth1 up && \
sysctl -w net.ipv4.ip_forward=1 && \
cat > /etc/frr/frr.conf << 'EOF'
frr version 8.1
frr defaults traditional
hostname R3
log syslog informational
!
router ospf
 ospf router-id 3.3.3.3
 network 192.168.3.0/24 area 2
 network 10.2.1.0/30 area 2
!
line vty
!
EOF
/usr/lib/frr/frrinit.sh start


# =============================================================================
# R4 - Internal Router (Area 2)
# Interfaces:
#   eth0: 192.168.4.1/24 -> PC4 (LAN)
#   eth1: 10.2.2.2/30 -> ABR2 (Area 2)
# =============================================================================
# GNS3 Start Command pour R4:

ip addr add 192.168.4.1/24 dev eth0 && \
ip addr add 10.2.2.2/30 dev eth1 && \
ip link set eth0 up && \
ip link set eth1 up && \
sysctl -w net.ipv4.ip_forward=1 && \
cat > /etc/frr/frr.conf << 'EOF'
frr version 8.1
frr defaults traditional
hostname R4
log syslog informational
!
router ospf
 ospf router-id 4.4.4.4
 network 192.168.4.0/24 area 2
 network 10.2.2.0/30 area 2
!
line vty
!
EOF
/usr/lib/frr/frrinit.sh start


# =============================================================================
# PC1 - Alpine Linux (LAN 192.168.1.0/24)
# =============================================================================
# GNS3 Start Command pour PC1:

ip addr add 192.168.1.10/24 dev eth0 && \
ip link set eth0 up && \
ip route add default via 192.168.1.1


# =============================================================================
# PC2 - Alpine Linux (LAN 192.168.2.0/24)
# =============================================================================
# GNS3 Start Command pour PC2:

ip addr add 192.168.2.10/24 dev eth0 && \
ip link set eth0 up && \
ip route add default via 192.168.2.1


# =============================================================================
# PC3 - Alpine Linux (LAN 192.168.3.0/24)
# =============================================================================
# GNS3 Start Command pour PC3:

ip addr add 192.168.3.10/24 dev eth0 && \
ip link set eth0 up && \
ip route add default via 192.168.3.1


# =============================================================================
# PC4 - Alpine Linux (LAN 192.168.4.0/24)
# =============================================================================
# GNS3 Start Command pour PC4:

ip addr add 192.168.4.10/24 dev eth0 && \
ip link set eth0 up && \
ip route add default via 192.168.4.1


# =============================================================================
# COMMANDES DE VÉRIFICATION (à exécuter manuellement)
# =============================================================================
# 
# Vérifier la configuration OSPF sur un routeur FRR:
#   docker exec -it <container_name> vtysh -c "show ip ospf neighbor"
#   docker exec -it <container_name> vtysh -c "show ip route ospf"
#   docker exec -it <container_name> vtysh -c "show ip ospf database"
#   docker exec -it <container_name> vtysh -c "show ip ospf interface"
#
# Test de connectivité:
#   docker exec -it PC1 ping 192.168.4.10   # PC1 vers PC4
#   docker exec -it PC2 ping 192.168.3.10   # PC2 vers PC3
#
# Vérifier les coûts OSPF:
#   docker exec -it ABR1 vtysh -c "show ip ospf interface eth0"
#
# Modifier le coût OSPF dynamiquement:
#   docker exec -it ABR1 vtysh -c "conf t" -c "interface eth1" -c "ip ospf cost 100"
# =============================================================================
