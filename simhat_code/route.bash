#!/bin/bash
#title           :route.bash
#description     :RPi as router configuration script, used through init_dial.bash file
#author          :Nicholas Putra Rihandoko, Nauval Chantika
#date            :2024/01/09
#version         :1.2
#usage           :Iot Gateway
#notes           :
#==============================================================================

echo ""
ip_address="$3"
rpi_man_route="$2"
network_address=$(echo $rpi_man_route | cut -d'/' -f1)
cidr_prefix=$(echo $rpi_man_route | cut -d'/' -f2)

# Function to convert CIDR prefix to subnet mask
cidr_to_netmask() {
    local i mask=""
    local full_octets=$(($1/8))
    local partial_octet=$(($1%8))

    for ((i=0; i<4; i++)); do
        if [ $i -lt $full_octets ]; then
            mask+=255
        elif [ $i -eq $full_octets ]; then
            mask+=$((256 - 2**(8-$partial_octet)))
        else
            mask+=0
        fi
        test $i -lt 3 && mask+=.
    done

    echo $mask
}

# Convert CIDR prefix to subnet mask
netmask=$(cidr_to_netmask $cidr_prefix)

dhcp_range_start=$(echo $ip_address | awk -F. '{printf "%d.%d.%d.%d", $1, $2, $3, $4+1}')
dhcp_range_end=$(echo $ip_address | awk -F. '{printf "%d.%d.%d.%d", $1, $2, $3, ($4+20)%256}')
dhcp_time="24h"
dns_server="8.8.8.8"
eth=$(ip -o link show | awk -F': ' '{print $2}' | grep -v lo | grep -i eth)
wwan=$(ip -o link show | awk -F': ' '{print $2}' | grep -v lo | grep -i wwan)
zt=$1

modify_conf() {
    local key=$1
    local value=$2
    local line="$key = $value"
    local file_path=$3

    if grep -q "^${key}" "$file_path"; then
       # key exists (commented or uncommented), modify it
       sed -i "s/^${key}.*/$line/" "$file_path"
       #echo "Modified $key in $file_path"
    else
        # key does not exist, add it
        echo "$line" >> "$file_path"
        #echo "Added $line to $file_path"
    fi
}

#=================================================
# IPTABLES SET UP

## Network routing configuration using iptables
# Allow IP packets to be forwarded
#sudo echo 1 > /proc/sys/net/ipv4/ip_forward
# Also do this if it does not work:
modify_conf "net.ipv4.ip_forward" "1" "/etc/sysctl.conf"
sudo sysctl -p /etc/sysctl.conf
# And/or do this:
#sudo sysctl -w net.ipv4.ip_forward=1    # immediately enable, non persistent
# Start networking service
sudo systemctl start network-online.target
# Flush firewalls and reset rules to default (accept all)
sudo iptables -F
# Flush NAT table and reset port-forwarding and masquerading rules
sudo iptables -t nat -F

add_iptables_rule() {
    local RULE=$1

    # Check if the rule already exists
    if ! iptables -C $RULE 2>/dev/null; then
        # Rule does not exist, add it
        iptables $RULE
        # echo "Rule added: $RULE"
    #else
        # echo "Rule already exists: $RULE"
    fi
}

## NAT rules for port forwarding to/from the internet
# Set rules to match the source's address with wwan's address (masquerading) as the packet leaves network interface (postrouting chain) to internet
add_iptables_rule "-t nat -A POSTROUTING -o $wwan -j MASQUERADE"
# Allow forwarding of network traffic from wwan to eth and vice versa if the network traffic is part of existing connections or sessions
add_iptables_rule "-A FORWARD -i $wwan -o $eth -m state --state RELATED,ESTABLISHED -j ACCEPT"
add_iptables_rule "-A FORWARD -i $eth -o $wwan -j ACCEPT"

## NAT rules for port forwarding to/from the Zerotier virtual LAN
# Set rules to match the source's address with eth's address (masquerading) as the packet leaves network interface (postrouting chain) to ZeroTier virtual LAN
add_iptables_rule "-t nat -A POSTROUTING -o $eth -j MASQUERADE"
# Allow forwarding of network traffic from eth to zt and vice versa if the network traffic is part of existing connections or sessions
add_iptables_rule "-A FORWARD -i $eth -o $zt -m state --state RELATED,ESTABLISHED -j ACCEPT"
add_iptables_rule "-A FORWARD -i $zt -o $eth -j ACCEPT"
# Allow traffic to and from TCP and UDP port 9993 for ZeroTier virtual LAN communication
add_iptables_rule "-A INPUT -p udp --dport 9993 -j ACCEPT"
add_iptables_rule "-A OUTPUT -p udp --dport 9993 -j ACCEPT"
add_iptables_rule "-A FORWARD -p udp --dport 9993 -j ACCEPT"
add_iptables_rule "-A INPUT -p tcp --dport 9993 -j ACCEPT"
add_iptables_rule "-A OUTPUT -p tcp --dport 9993 -j ACCEPT"
add_iptables_rule "-A FORWARD -p tcp --dport 9993 -j ACCEPT"

# Save iptables rules for next boot using iptables-persistent
sudo su -c  "iptables-save > /etc/iptables/rules.v4"

#=================================================
# Function to delete existing routes for a specified interface
del_exist_route() {
    local interface=$1
    # Get all routes for the interface and delete them
    while read -r route; do
        sudo ip route del $route
    done < <(ip route show dev $interface | awk '{print $1}')
}

# DNSMASQ SET UP

## DHCP & DNS settings for router operation using dnsmasq
# Set up static ip address fo Raspberry Pi on ethernet network
# Enable ethernet network interface
sudo ifconfig $eth down && sudo ip link set down $eth
sudo ifconfig $eth up && sudo ip link set up $eth
sudo ifconfig $eth $ip_address netmask $netmask
# Stop dnsmasq service
sudo systemctl stop dnsmasq
# Remove default/previous route created by dhcpcd
del_exist_route "$eth"
sudo rm -rf /etc/dnsmasq.d/*
# Add new routing rules for dnsmasq
sudo echo -e "interface=$eth
bind-interfaces
server=$dns_server
domain-needed
bogus-priv
dhcp-range=$dhcp_range_start,$dhcp_range_end,$dhcp_time" > /tmp/custom-dnsmasq.conf
sudo cp /tmp/custom-dnsmasq.conf /etc/dnsmasq.d/custom-dnsmasq.conf
# Start dnsmasq service
sudo systemctl start dnsmasq
