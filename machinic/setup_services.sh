#!/bin/bash
#move in machine_core environment?
sudo cp nomad.service /etc/systemd/system/
sudo cp consul.service /etc/systemd/system/

sudo systemctl daemon-reload

sudo systemctl enable consul
sudo systemctl enable nomad

sudo systemctl start consul
sudo systemctl start nomad
(sudo mkdir /var/lib/nomad/data/ -p)
(sudo cp nomad_config.hcl /usr/local/etc/)

sudo systemctl status
