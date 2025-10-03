resource "aws_security_group" "ec2_sg" {
  vpc_id      = aws_vpc.main.id
  name        = "${var.project_name}-ec2-sg"
  description = "Allows HTTP traffic to the ECS host and SSH for management"

  # Ingress Rule: Allow HTTP traffic (Port 8000 for Django) from anywhere
  ingress {
    from_port   = 8000 # Your Django Port
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Ingress Rule: Allow SSH access (Port 22) - Best to restrict to your IP
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # NOTE: Replace with your public IP for better security!
  }

  # Egress Rule: Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ec2-sg"
  }
}

# ----------------------------------------------------
# 2. EC2 Instance (The Zero-Cost Host)
# ----------------------------------------------------
resource "aws_instance" "ecs_host" {
  # Use the t2.micro instance type for the AWS Free Tier
  instance_type          = "t2.micro" 
  
  # Find the latest Amazon Linux 2 AMI (optimized for ECS)
  ami                    = data.aws_ami.ecs_optimized.id 

  # Place the EC2 in one of the public subnets we created in network.tf
  subnet_id              = aws_subnet.public_a.id 
  
  # Since it's in a public subnet, assign a public IP
  associate_public_ip_address = true 
  
  # Attach the security group we defined above
  security_groups        = [aws_security_group.ec2_sg.id]

  iam_instance_profile  = aws_iam_instance_profile.ecs_instance_profile.name

  # User data script to install the ECS Agent and join the cluster
  user_data = templatefile("user_data.sh", {
    ecs_cluster_name = aws_ecs_cluster.main.name
  })

  tags = {
    Name        = "${var.project_name}-ecs-host"
    Project     = var.project_name
    Environment = "Demo-Zero-Cost"
  }
}

# ----------------------------------------------------
# 3. Data Source: Find the latest ECS-Optimized AMI
# ----------------------------------------------------
data "aws_ami" "ecs_optimized" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    # This filters for the latest ECS-optimized AMI for Amazon Linux 2 (best practice)
    values = ["amzn2-ami-ecs-hvm-*-x86_64-ebs"] 
  }
}