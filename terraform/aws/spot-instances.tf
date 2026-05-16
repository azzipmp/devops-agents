# AWS Spot Instances for Cost-Effective Parallel Test Execution

variable "region" {
  type = string
}

variable "max_spot_instances" {
  type = number
}

variable "environment" {
  type = string
}

# VPC for test infrastructure
resource "aws_vpc" "test_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "test-infrastructure-vpc"
  }
}

resource "aws_subnet" "test_subnet" {
  vpc_id                  = aws_vpc.test_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  
  tags = {
    Name = "test-infrastructure-subnet"
  }
}

resource "aws_internet_gateway" "test_igw" {
  vpc_id = aws_vpc.test_vpc.id
  
  tags = {
    Name = "test-infrastructure-igw"
  }
}

resource "aws_route_table" "test_rt" {
  vpc_id = aws_vpc.test_vpc.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.test_igw.id
  }
  
  tags = {
    Name = "test-infrastructure-rt"
  }
}

resource "aws_route_table_association" "test_rta" {
  subnet_id      = aws_subnet.test_subnet.id
  route_table_id = aws_route_table.test_rt.id
}

# Security group for test runners
resource "aws_security_group" "test_runner_sg" {
  name        = "test-runner-sg"
  description = "Security group for test runner instances"
  vpc_id      = aws_vpc.test_vpc.id
  
  # Allow SSH for management
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Allow test agent communication
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "test-runner-sg"
  }
}

# IAM role for test runners
resource "aws_iam_role" "test_runner_role" {
  name = "test-runner-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "test_runner_ssm" {
  role       = aws_iam_role.test_runner_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "test_runner_profile" {
  name = "test-runner-profile"
  role = aws_iam_role.test_runner_role.name
}

# Launch template for spot instances
resource "aws_launch_template" "test_runner" {
  name_prefix   = "test-runner-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = "t3.large"
  
  iam_instance_profile {
    arn = aws_iam_instance_profile.test_runner_profile.arn
  }
  
  network_interfaces {
    associate_public_ip_address = true
    security_groups            = [aws_security_group.test_runner_sg.id]
  }
  
  user_data = base64encode(<<-EOF
              #!/bin/bash
              set -e
              
              # Update system
              apt-get update
              apt-get install -y docker.io python3-pip git curl
              
              # Install Docker Compose
              curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose
              
              # Start Docker
              systemctl start docker
              systemctl enable docker
              
              # Pull test runner images
              docker pull selenium/standalone-chrome:latest
              docker pull python:3.11-slim
              
              # Install test dependencies
              pip3 install pytest pytest-xdist pytest-cov requests boto3
              
              # Create test workspace
              mkdir -p /opt/test-workspace
              cd /opt/test-workspace
              
              # Clone test repository (customize with your repo)
              # git clone https://github.com/your-org/your-tests.git
              
              # Signal readiness
              echo "Test runner ready" > /tmp/runner-status.txt
              
              # Keep instance alive for test execution
              tail -f /dev/null
              EOF
  )
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "test-runner-spot"
      Type = "ephemeral"
    }
  }
}

# Get latest Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Auto Scaling Group for Spot Instances
resource "aws_autoscaling_group" "test_runners" {
  name                = "test-runners-asg"
  vpc_zone_identifier = [aws_subnet.test_subnet.id]
  min_size            = 0
  max_size            = var.max_spot_instances
  desired_capacity    = 0
  
  mixed_instances_policy {
    instances_distribution {
      on_demand_base_capacity                  = 0
      on_demand_percentage_above_base_capacity = 0
      spot_allocation_strategy                 = "price-capacity-optimized"
    }
    
    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.test_runner.id
        version            = "$Latest"
      }
      
      override {
        instance_type = "t3.large"
      }
      
      override {
        instance_type = "t3.xlarge"
      }
      
      override {
        instance_type = "t3a.large"
      }
    }
  }
  
  tag {
    key                 = "Name"
    value               = "test-runner-spot"
    propagate_at_launch = true
  }
  
  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }
}

# CloudWatch metric for queue-based scaling
resource "aws_cloudwatch_metric_alarm" "test_queue_high" {
  alarm_name          = "test-queue-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Average"
  threshold           = "10"
  alarm_description   = "Scale up when test queue has more than 10 items"
  
  dimensions = {
    QueueName = aws_sqs_queue.test_queue.name
  }
  
  alarm_actions = [aws_autoscaling_policy.scale_up.arn]
}

resource "aws_autoscaling_policy" "scale_up" {
  name                   = "scale-up-test-runners"
  scaling_adjustment     = 5
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 60
  autoscaling_group_name = aws_autoscaling_group.test_runners.name
}

resource "aws_autoscaling_policy" "scale_down" {
  name                   = "scale-down-test-runners"
  scaling_adjustment     = -2
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.test_runners.name
}

# SQS Queue for test distribution
resource "aws_sqs_queue" "test_queue" {
  name                      = "test-execution-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  
  tags = {
    Name = "test-execution-queue"
  }
}

# Outputs
output "launch_template_id" {
  value = aws_launch_template.test_runner.id
}

output "autoscaling_group_name" {
  value = aws_autoscaling_group.test_runners.name
}

output "test_queue_url" {
  value = aws_sqs_queue.test_queue.url
}
