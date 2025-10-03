#!/bin/bash
# Install Docker
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo chkconfig docker on

# Configure the ECS Agent
# This tells the ECS agent which cluster to join upon startup
sudo echo "ECS_CLUSTER=${ecs_cluster_name}" >> /etc/ecs/ecs.config
sudo systemctl enable --now --no-block ecs