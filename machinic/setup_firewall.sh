#!/bin/bash

# $1 interface name
#
# ./setup_firewall.sh [interface]
#
# example: ./setup_firewall.sh enp0s25

# ifconfig lists interfaces
# wireless prefixed with a 'w'
# ethernet with a 'e'

# Drop all incoming rule may need to change 
# or be modified for consul gossip and zyre 
# protocols...
#

#debian based
sudo apt-get install firewalld
#fedora
sudo dnf install firewalld

#following commands work for either system:


#set default zone to 'drop'
sudo firewall-cmd --permanent --set-default-zone=drop

#set network interface fro drop zone

sudo firewall-cmd --permanent --zone=drop --change-interface=<interface>

#add rule

sudo firewall-cmd --zone=drop  --add-rich-rule='rule family="ipv4" source address="192.168.0.0/24" accept'

#to remove rule:
#sudo firewall-cmd --zone=drop  --remove-rich-rule='rule family="ipv4" source address="192.168.0.0/24" accept'
