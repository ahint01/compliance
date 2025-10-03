# ECS Task Execution Role
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.project_name}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Attach the standard ECS Task Execution Policy
resource "aws_iam_role_policy_attachment" "ecs_exec_attach" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Data source to reference the manually created IAM Role
data "aws_iam_role" "existing_ecs_instance_role" {
  name = "ecsInstanceRole"
}

# Create the Instance Profile that links the role to the EC2 host
resource "aws_iam_instance_profile" "ecs_instance_profile" {
  name = "${var.project_name}-ecs-instance-profile"
  role = data.aws_iam_role.existing_ecs_instance_role.name
}

# ECS Cluster Definition
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled" # Optional, but helpful for monitoring
  }

  tags = {
    Name = "${var.project_name}-cluster"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "django_logs" {
  name              = "/ecs/${var.project_name}-django-app"
  retention_in_days = 7 # Keep logs for a week

  tags = {
    Name = "${var.project_name}-logs"
  }
}

resource "aws_ecs_task_definition" "django_app" {
  family                   = "${var.project_name}-task"
  requires_compatibilities = ["EC2"]
  network_mode             = "bridge"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  cpu                      = 256 # Minimum CPU (1/4 vCPU)
  memory                   = 512 # Minimum RAM (512 MB)

  container_definitions = jsonencode([
    {
      name      = "${var.project_name}-django-container",
      image     = "576366844090.dkr.ecr.us-east-2.amazonaws.com/compliance_checker:latest",
      cpu       = 256,
      memory    = 512,
      essential = true,
      portMappings = [
        {
          containerPort = 8000,
          hostPort      = 8000
        }
      ],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"       = aws_cloudwatch_log_group.django_logs.name,
          "awslogs-region"      = var.aws_region,
          "awslogs-stream-prefix" = "ecs"
        }
      }
      "environment": [
        {
          "name": "ALLOWED_HOSTS_ENV",
          # Use the identified EC2 resource name 'ecs_host'
          "value": "${aws_instance.ecs_host.public_ip},localhost,127.0.0.1"
        },
        {
          "name": "DJANGO_SETTINGS_MODULE",
          "value": "compliance.settings"
        }
      ]
    }
  ])

  tags = {
    Name = "${var.project_name}-task"
  }
}

resource "aws_ecs_service" "django_service" {
  name            = "${var.project_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.django_app.arn
  scheduling_strategy = "REPLICA"
  desired_count       = 1

  tags = {
    Name = "${var.project_name}-service"
  }
}