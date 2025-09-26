# Terraform Infrastructure Documentation

## Overview

The Terraform configuration provides Infrastructure as Code (IaC) for deploying the Agentic AI Customer Support system on cloud platforms. Currently, it focuses on AWS EKS (Elastic Kubernetes Service) with plans for multi-cloud expansion to Azure AKS and Google GKE.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Account                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    VPC (10.0.0.0/16)                    │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │   Public    │  │   Private   │  │   Private   │     │ │
│  │  │  Subnet 1   │  │  Subnet 1   │  │  Subnet 2   │     │ │
│  │  │(10.0.1.0/24)│  │(10.0.10.0/24│  │(10.0.20.0/24│     │ │
│  │  │             │  │             │  │             │     │ │
│  │  │  NAT GW 1   │  │  EKS Nodes  │  │  EKS Nodes  │     │ │
│  │  │             │  │             │  │             │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  │                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │   Public    │  │   Private   │  │   Private   │     │ │
│  │  │  Subnet 2   │  │  Subnet 3   │  │  Subnet 4   │     │ │
│  │  │(10.0.2.0/24)│  │(10.0.30.0/24│  │(10.0.40.0/24│     │ │
│  │  │             │  │             │  │             │     │ │
│  │  │  NAT GW 2   │  │ RDS/Storage │  │ RDS/Storage │     │ │
│  │  │             │  │             │  │             │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    EKS Cluster                          │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│  │  │  Node Group │  │  Node Group │  │  Node Group │     │ │
│  │  │   (API/Web) │  │    (AI/ML)  │  │  (Database) │     │ │
│  │  │  m5.large   │  │  c5.xlarge  │  │  r5.large   │     │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
ops/terraform/
└── aws/
    ├── main.tf                    # Main Terraform configuration
    ├── variables.tf               # Input variables
    ├── outputs.tf                 # Output values
    ├── versions.tf                # Provider versions and requirements
    ├── modules/                   # Reusable modules
    │   ├── vpc/                   # VPC module
    │   ├── eks/                   # EKS cluster module
    │   ├── node-groups/           # EKS node groups module
    │   ├── security-groups/       # Security groups module
    │   ├── iam/                   # IAM roles and policies module
    │   └── storage/               # Storage (EBS, EFS) module
    ├── environments/              # Environment-specific configurations
    │   ├── development/
    │   │   ├── main.tf
    │   │   ├── terraform.tfvars
    │   │   └── backend.tf
    │   ├── staging/
    │   │   ├── main.tf
    │   │   ├── terraform.tfvars
    │   │   └── backend.tf
    │   └── production/
    │       ├── main.tf
    │       ├── terraform.tfvars
    │       └── backend.tf
    └── scripts/
        ├── deploy.sh              # Deployment script
        ├── destroy.sh             # Cleanup script
        └── update-kubeconfig.sh   # Kubeconfig update script
```

## Core Terraform Configuration

### Main Configuration (main.tf)

```hcl
# Terraform configuration for AWS EKS cluster
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "agentic-ai-customer-support"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "agentic-ai-team"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

data "aws_caller_identity" "current" {}

# VPC Configuration
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = slice(data.aws_availability_zones.available.names, 0, 3)
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway     = true
  single_nat_gateway     = var.single_nat_gateway
  enable_vpn_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true

  # EKS requirements
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true

  public_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                     = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"           = "1"
  }

  tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = var.cluster_endpoint_public_access

  # OIDC Identity provider
  cluster_identity_providers = {
    sts = {
      client_id = "sts.amazonaws.com"
    }
  }

  # EKS Managed Node Groups
  eks_managed_node_groups = {
    # API/Web workloads
    api = {
      name = "api-nodes"

      instance_types = ["m5.large"]
      
      min_size     = 1
      max_size     = 10
      desired_size = 3

      pre_bootstrap_user_data = <<-EOT
        #!/bin/bash
        /etc/eks/bootstrap.sh ${var.cluster_name}
      EOT

      vpc_security_group_ids = [aws_security_group.node_group_api.id]

      labels = {
        Environment = var.environment
        NodeGroup   = "api"
        Workload    = "web"
      }

      taints = {
        api = {
          key    = "workload"
          value  = "api"
          effect = "NO_SCHEDULE"
        }
      }

      tags = {
        ExtraTag = "api-nodes"
      }
    }

    # AI/ML workloads
    ml = {
      name = "ml-nodes"

      instance_types = ["c5.xlarge"]
      
      min_size     = 1
      max_size     = 5
      desired_size = 2

      vpc_security_group_ids = [aws_security_group.node_group_ml.id]

      labels = {
        Environment = var.environment
        NodeGroup   = "ml"
        Workload    = "ai-ml"
      }

      taints = {
        ml = {
          key    = "workload"
          value  = "ml"
          effect = "NO_SCHEDULE"
        }
      }

      tags = {
        ExtraTag = "ml-nodes"
      }
    }

    # Database workloads
    database = {
      name = "database-nodes"

      instance_types = ["r5.large"]
      
      min_size     = 1
      max_size     = 3
      desired_size = 2

      vpc_security_group_ids = [aws_security_group.node_group_database.id]

      labels = {
        Environment = var.environment
        NodeGroup   = "database"
        Workload    = "database"
      }

      taints = {
        database = {
          key    = "workload"
          value  = "database"
          effect = "NO_SCHEDULE"
        }
      }

      tags = {
        ExtraTag = "database-nodes"
      }
    }
  }

  # Fargate Profiles (optional)
  fargate_profiles = {
    default = {
      name = "default"
      selectors = [
        {
          namespace = "kube-system"
          labels = {
            "app.kubernetes.io/name" = "aws-load-balancer-controller"
          }
        }
      ]
    }
  }

  # aws-auth configmap
  manage_aws_auth_configmap = true

  aws_auth_roles = [
    {
      rolearn  = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/AWSReservedSSO_AdministratorAccess_*"
      username = "admin"
      groups   = ["system:masters"]
    },
  ]

  aws_auth_users = var.aws_auth_users

  tags = {
    Environment = var.environment
    Terraform   = "true"
  }
}

# Security Groups
resource "aws_security_group" "node_group_api" {
  name_prefix = "${var.cluster_name}-api-nodes"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.cluster_name}-api-nodes-sg"
  }
}

resource "aws_security_group" "node_group_ml" {
  name_prefix = "${var.cluster_name}-ml-nodes"
  vpc_id      = module.vpc.vpc_id

  # Internal communication only
  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.cluster_name}-ml-nodes-sg"
  }
}

resource "aws_security_group" "node_group_database" {
  name_prefix = "${var.cluster_name}-database-nodes"
  vpc_id      = module.vpc.vpc_id

  # Database ports
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  ingress {
    from_port   = 6333
    to_port     = 6333
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.cluster_name}-database-nodes-sg"
  }
}
```

### Variables Configuration (variables.tf)

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "agentic-ai-support"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.27"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "single_nat_gateway" {
  description = "Use a single NAT gateway (cost optimization for dev/test)"
  type        = bool
  default     = false
}

variable "cluster_endpoint_public_access" {
  description = "Enable public API server endpoint"
  type        = bool
  default     = true
}

variable "node_groups" {
  description = "EKS node groups configuration"
  type = map(object({
    instance_types = list(string)
    min_size       = number
    max_size       = number
    desired_size   = number
    labels         = map(string)
    taints = map(object({
      key    = string
      value  = string
      effect = string
    }))
  }))
  default = {
    api = {
      instance_types = ["m5.large"]
      min_size       = 1
      max_size       = 10
      desired_size   = 3
      labels = {
        workload = "api"
      }
      taints = {}
    }
    ml = {
      instance_types = ["c5.xlarge"]
      min_size       = 1
      max_size       = 5
      desired_size   = 2
      labels = {
        workload = "ml"
      }
      taints = {
        ml = {
          key    = "workload"
          value  = "ml"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }
}

variable "aws_auth_users" {
  description = "Additional IAM users to add to the aws-auth configmap"
  type = list(object({
    userarn  = string
    username = string
    groups   = list(string)
  }))
  default = []
}

variable "enable_irsa" {
  description = "Enable IAM roles for service accounts"
  type        = bool
  default     = true
}

variable "enable_cluster_autoscaler" {
  description = "Enable cluster autoscaler"
  type        = bool
  default     = true
}

variable "enable_aws_load_balancer_controller" {
  description = "Enable AWS Load Balancer Controller"
  type        = bool
  default     = true
}

variable "enable_external_dns" {
  description = "Enable External DNS"
  type        = bool
  default     = true
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
```

### Outputs Configuration (outputs.tf)

```hcl
output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = module.eks.cluster_arn
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_version" {
  description = "The Kubernetes version for the EKS cluster"
  value       = module.eks.cluster_version
}

output "cluster_platform_version" {
  description = "Platform version for the EKS cluster"
  value       = module.eks.cluster_platform_version
}

output "cluster_security_group_id" {
  description = "Security group ids attached to the cluster control plane"
  value       = module.eks.cluster_security_group_id
}

output "vpc_id" {
  description = "ID of the VPC where the cluster is deployed"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnets" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnets
}

output "node_security_group_id" {
  description = "ID of the node shared security group"
  value       = module.eks.node_security_group_id
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Identity Provider if enabled"
  value       = module.eks.oidc_provider_arn
}

output "cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = module.eks.cluster_iam_role_name
}

output "cluster_iam_role_arn" {
  description = "IAM role ARN associated with EKS cluster"
  value       = module.eks.cluster_iam_role_arn
}

output "node_groups" {
  description = "EKS node groups"
  value       = module.eks.eks_managed_node_groups
  sensitive   = true
}

output "aws_auth_configmap_yaml" {
  description = "Formatted yaml output for aws-auth configmap"
  value       = module.eks.aws_auth_configmap_yaml
}

# Storage outputs
output "ebs_csi_driver_arn" {
  description = "The Amazon Resource Name (ARN) of the EBS CSI driver"
  value       = module.eks.cluster_addons.aws-ebs-csi-driver.addon_arn
}

# Load Balancer Controller outputs
output "aws_load_balancer_controller_role_arn" {
  description = "ARN of the AWS Load Balancer Controller IAM role"
  value       = try(module.aws_load_balancer_controller.iam_role_arn, null)
}

# External DNS outputs
output "external_dns_role_arn" {
  description = "ARN of the External DNS IAM role"
  value       = try(module.external_dns.iam_role_arn, null)
}

# Cluster Autoscaler outputs
output "cluster_autoscaler_role_arn" {
  description = "ARN of the Cluster Autoscaler IAM role"
  value       = try(module.cluster_autoscaler.iam_role_arn, null)
}

# Kubeconfig
output "kubeconfig_update_command" {
  description = "Command to update kubeconfig"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_id}"
}
```

## Environment-Specific Configurations

### Development Environment

```hcl
# environments/development/terraform.tfvars
aws_region     = "us-east-1"
cluster_name   = "agentic-ai-dev"
environment    = "development"
kubernetes_version = "1.27"

# Cost optimization
single_nat_gateway = true

# Smaller node groups
node_groups = {
  general = {
    instance_types = ["t3.medium"]
    min_size       = 1
    max_size       = 3
    desired_size   = 2
    labels = {
      workload = "general"
    }
    taints = {}
  }
}

# Simplified networking
vpc_cidr = "10.10.0.0/16"
private_subnets = ["10.10.1.0/24", "10.10.2.0/24"]
public_subnets  = ["10.10.101.0/24", "10.10.102.0/24"]

# Disable some features for cost
enable_external_dns = false
enable_aws_load_balancer_controller = false

tags = {
  Environment = "development"
  Purpose     = "testing"
}
```

### Staging Environment

```hcl
# environments/staging/terraform.tfvars
aws_region     = "us-east-1"
cluster_name   = "agentic-ai-staging"
environment    = "staging"
kubernetes_version = "1.27"

# Production-like setup but smaller
node_groups = {
  api = {
    instance_types = ["m5.large"]
    min_size       = 1
    max_size       = 5
    desired_size   = 2
    labels = {
      workload = "api"
    }
    taints = {}
  }
  ml = {
    instance_types = ["c5.large"]
    min_size       = 1
    max_size       = 3
    desired_size   = 1
    labels = {
      workload = "ml"
    }
    taints = {
      ml = {
        key    = "workload"
        value  = "ml"
        effect = "NO_SCHEDULE"
      }
    }
  }
}

# Full networking
vpc_cidr = "10.1.0.0/16"
private_subnets = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
public_subnets  = ["10.1.101.0/24", "10.1.102.0/24", "10.1.103.0/24"]

# Enable most features
enable_external_dns = true
enable_aws_load_balancer_controller = true
enable_cluster_autoscaler = true

domain_name = "staging.agentic-ai-support.com"

tags = {
  Environment = "staging"
  Purpose     = "integration-testing"
}
```

### Production Environment

```hcl
# environments/production/terraform.tfvars
aws_region     = "us-east-1"
cluster_name   = "agentic-ai-prod"
environment    = "production"
kubernetes_version = "1.27"

# Full production setup
node_groups = {
  api = {
    instance_types = ["m5.xlarge"]
    min_size       = 3
    max_size       = 20
    desired_size   = 5
    labels = {
      workload = "api"
    }
    taints = {}
  }
  ml = {
    instance_types = ["c5.2xlarge"]
    min_size       = 2
    max_size       = 10
    desired_size   = 3
    labels = {
      workload = "ml"
    }
    taints = {
      ml = {
        key    = "workload"
        value  = "ml"
        effect = "NO_SCHEDULE"
      }
    }
  }
  database = {
    instance_types = ["r5.xlarge"]
    min_size       = 2
    max_size       = 5
    desired_size   = 3
    labels = {
      workload = "database"
    }
    taints = {
      database = {
        key    = "workload"
        value  = "database"
        effect = "NO_SCHEDULE"
      }
    }
  }
}

# Production networking
vpc_cidr = "10.0.0.0/16"
private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

# Enable all features
enable_external_dns = true
enable_aws_load_balancer_controller = true
enable_cluster_autoscaler = true
enable_irsa = true

domain_name = "api.agentic-ai-support.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"

# Multi-AZ for high availability
single_nat_gateway = false

tags = {
  Environment = "production"
  Purpose     = "live-service"
  Backup      = "required"
  Monitoring  = "critical"
}
```

## Kubernetes Add-ons

### AWS Load Balancer Controller

```hcl
# AWS Load Balancer Controller
module "aws_load_balancer_controller" {
  source = "terraform-aws-modules/eks/aws//modules/aws-load-balancer-controller"

  cluster_name                           = module.eks.cluster_id
  cluster_endpoint                       = module.eks.cluster_endpoint
  cluster_version                        = module.eks.cluster_version
  vpc_id                                = module.vpc.vpc_id
  
  # IRSA
  create_role                           = true
  role_name                             = "${var.cluster_name}-aws-load-balancer-controller"
  attach_load_balancer_controller_policy = true

  oidc_provider_arn = module.eks.oidc_provider_arn

  tags = var.tags
}
```

### Cluster Autoscaler

```hcl
# Cluster Autoscaler
module "cluster_autoscaler" {
  source = "terraform-aws-modules/eks/aws//modules/cluster-autoscaler"

  cluster_name                     = module.eks.cluster_id
  cluster_endpoint                 = module.eks.cluster_endpoint
  cluster_version                  = module.eks.cluster_version
  
  # IRSA
  create_role               = true
  role_name                 = "${var.cluster_name}-cluster-autoscaler"
  attach_cluster_autoscaler_policy = true

  oidc_provider_arn = module.eks.oidc_provider_arn

  tags = var.tags
}
```

### External DNS

```hcl
# External DNS
module "external_dns" {
  source = "terraform-aws-modules/eks/aws//modules/external-dns"

  cluster_name                     = module.eks.cluster_id
  cluster_endpoint                 = module.eks.cluster_endpoint
  cluster_version                  = module.eks.cluster_version
  
  # IRSA
  create_role            = true
  role_name              = "${var.cluster_name}-external-dns"
  attach_external_dns_policy = true

  oidc_provider_arn = module.eks.oidc_provider_arn

  # Route53 hosted zone
  external_dns_route53_zone_arns = [
    "arn:aws:route53:::hostedzone/Z123456789"
  ]

  tags = var.tags
}
```

## Storage Configuration

### EBS CSI Driver

```hcl
# EBS CSI Driver
resource "aws_eks_addon" "ebs_csi" {
  cluster_name             = module.eks.cluster_id
  addon_name               = "aws-ebs-csi-driver"
  addon_version            = "v1.19.0-eksbuild.2"
  service_account_role_arn = module.ebs_csi_irsa_role.iam_role_arn
  resolve_conflicts        = "OVERWRITE"

  tags = var.tags
}

# EBS CSI Driver IRSA
module "ebs_csi_irsa_role" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"

  role_name             = "${var.cluster_name}-ebs-csi-driver"
  attach_ebs_csi_policy = true

  oidc_providers = {
    ex = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }

  tags = var.tags
}
```

### Storage Classes

```hcl
# Storage Classes
resource "kubernetes_storage_class" "gp3" {
  metadata {
    name = "gp3"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }
  
  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = "Delete"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true
  
  parameters = {
    type       = "gp3"
    fsType     = "ext4"
    encrypted  = "true"
  }
}

resource "kubernetes_storage_class" "gp3_retain" {
  metadata {
    name = "gp3-retain"
  }
  
  storage_provisioner    = "ebs.csi.aws.com"
  reclaim_policy         = "Retain"
  volume_binding_mode    = "WaitForFirstConsumer"
  allow_volume_expansion = true
  
  parameters = {
    type       = "gp3"
    fsType     = "ext4"
    encrypted  = "true"
  }
}
```

## Security Configuration

### IAM Roles and Policies

```hcl
# Additional IAM roles for workload identity
module "workload_identity_roles" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"

  for_each = {
    api = {
      namespace = "agentic-ai-support"
      service_account = "api-service-account"
      policy_statements = [
        {
          effect = "Allow"
          actions = [
            "s3:GetObject",
            "s3:PutObject",
            "s3:DeleteObject"
          ]
          resources = [
            "arn:aws:s3:::agentic-ai-support-data/*"
          ]
        }
      ]
    }
    mcp_aws = {
      namespace = "agentic-ai-support"
      service_account = "mcp-aws-service-account"
      policy_statements = [
        {
          effect = "Allow"
          actions = [
            "lambda:InvokeFunction",
            "sns:Publish",
            "sqs:SendMessage",
            "sqs:ReceiveMessage"
          ]
          resources = ["*"]
        }
      ]
    }
  }

  role_name = "${var.cluster_name}-${each.key}"

  role_policy_arns = {}

  oidc_providers = {
    ex = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["${each.value.namespace}:${each.value.service_account}"]
    }
  }

  tags = var.tags
}
```

### Security Groups

```hcl
# Additional security groups for specific workloads
resource "aws_security_group" "rds_sg" {
  count = var.create_rds ? 1 : 0

  name_prefix = "${var.cluster_name}-rds"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.node_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.cluster_name}-rds-sg"
  }
}
```

## Deployment Scripts

### Deploy Script (scripts/deploy.sh)

```bash
#!/bin/bash

set -e

ENVIRONMENT=${1:-development}
TERRAFORM_DIR="$(dirname "$0")/../environments/$ENVIRONMENT"

echo "🚀 Deploying Agentic AI Support infrastructure for $ENVIRONMENT environment"

# Check if terraform directory exists
if [ ! -d "$TERRAFORM_DIR" ]; then
    echo "❌ Environment directory $TERRAFORM_DIR does not exist"
    exit 1
fi

cd "$TERRAFORM_DIR"

# Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init

# Plan deployment
echo "📋 Planning deployment..."
terraform plan -out=tfplan

# Confirm deployment
echo "🤔 Do you want to apply these changes? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "🔄 Applying changes..."
    terraform apply tfplan
    
    # Update kubeconfig
    echo "🔧 Updating kubeconfig..."
    CLUSTER_NAME=$(terraform output -raw cluster_id)
    AWS_REGION=$(terraform output -raw aws_region || echo "us-east-1")
    
    aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"
    
    # Verify cluster access
    echo "✅ Verifying cluster access..."
    kubectl cluster-info
    
    echo "🎉 Deployment completed successfully!"
    echo "📝 Cluster endpoint: $(terraform output -raw cluster_endpoint)"
    echo "🏷️  Cluster version: $(terraform output -raw cluster_version)"
else
    echo "❌ Deployment cancelled"
    rm -f tfplan
fi
```

### Destroy Script (scripts/destroy.sh)

```bash
#!/bin/bash

set -e

ENVIRONMENT=${1:-development}
TERRAFORM_DIR="$(dirname "$0")/../environments/$ENVIRONMENT"

echo "⚠️  Destroying Agentic AI Support infrastructure for $ENVIRONMENT environment"
echo "🚨 This action is IRREVERSIBLE and will DELETE all resources!"

# Confirmation
echo "🤔 Are you absolutely sure? Type 'destroy' to confirm:"
read -r confirmation
if [ "$confirmation" != "destroy" ]; then
    echo "❌ Destruction cancelled"
    exit 1
fi

cd "$TERRAFORM_DIR"

# Plan destruction
echo "📋 Planning destruction..."
terraform plan -destroy -out=destroy.tfplan

# Final confirmation
echo "🤔 Last chance! Type 'YES' to proceed with destruction:"
read -r final_confirmation
if [ "$final_confirmation" != "YES" ]; then
    echo "❌ Destruction cancelled"
    rm -f destroy.tfplan
    exit 1
fi

# Apply destruction
echo "💥 Destroying infrastructure..."
terraform apply destroy.tfplan

echo "🗑️  Infrastructure destroyed"
```

## Backend Configuration

### S3 Backend

```hcl
# environments/production/backend.tf
terraform {
  backend "s3" {
    bucket         = "agentic-ai-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

### Creating Backend Resources

```bash
# Create S3 bucket for state
aws s3 mb s3://agentic-ai-terraform-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket agentic-ai-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region us-east-1
```

## Cost Optimization

### Development Environment Optimizations

```hcl
# Use spot instances for development
eks_managed_node_groups = {
  spot = {
    capacity_type  = "SPOT"
    instance_types = ["t3.medium", "t3a.medium", "t2.medium"]
    
    min_size     = 1
    max_size     = 3
    desired_size = 2
  }
}

# Single NAT Gateway
single_nat_gateway = true

# Smaller storage allocations
default_storage_size = "10Gi"
```

### Production Cost Management

```hcl
# Reserved instances for predictable workloads
eks_managed_node_groups = {
  api_reserved = {
    capacity_type  = "ON_DEMAND"
    instance_types = ["m5.large"]  # Use reserved instances
    
    min_size     = 3
    max_size     = 10
    desired_size = 5
  }
  
  ml_spot = {
    capacity_type  = "SPOT"
    instance_types = ["c5.xlarge", "c5a.xlarge", "c4.xlarge"]
    
    min_size     = 1
    max_size     = 20
    desired_size = 3
  }
}
```

## Monitoring and Logging

### CloudWatch Configuration

```hcl
# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "eks_cluster" {
  name              = "/aws/eks/${var.cluster_name}/cluster"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Enable EKS cluster logging
cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
```

### Prometheus Integration

```hcl
# Managed Prometheus
resource "aws_prometheus_workspace" "agentic_ai" {
  alias = "${var.cluster_name}-prometheus"

  tags = var.tags
}

# Managed Grafana
resource "aws_grafana_workspace" "agentic_ai" {
  account_access_type      = "CURRENT_ACCOUNT"
  authentication_providers = ["AWS_SSO"]
  permission_type          = "SERVICE_MANAGED"
  role_arn                = aws_iam_role.grafana.arn

  data_sources = [
    "CLOUDWATCH",
    "PROMETHEUS"
  ]

  name = "${var.cluster_name}-grafana"

  tags = var.tags
}
```

## Backup and Disaster Recovery

### EBS Snapshots

```hcl
# EBS Snapshot lifecycle policy
resource "aws_dlm_lifecycle_policy" "ebs_snapshots" {
  description        = "EBS snapshot policy for ${var.cluster_name}"
  execution_role_arn = aws_iam_role.dlm_lifecycle_role.arn
  state              = "ENABLED"

  policy_details {
    resource_types   = ["VOLUME"]
    target_tags = {
      "kubernetes.io/cluster/${var.cluster_name}" = "owned"
    }

    schedule {
      name = "Daily snapshots"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["03:00"]
      }

      retain_rule {
        count = 7
      }

      copy_tags = true
    }
  }

  tags = var.tags
}
```

### Cross-Region Backup

```hcl
# Cross-region backup for critical data
resource "aws_backup_vault" "agentic_ai" {
  name        = "${var.cluster_name}-backup-vault"
  kms_key_arn = aws_kms_key.backup.arn

  tags = var.tags
}

resource "aws_backup_plan" "agentic_ai" {
  name = "${var.cluster_name}-backup-plan"

  rule {
    rule_name         = "daily_backup"
    target_vault_name = aws_backup_vault.agentic_ai.name
    schedule          = "cron(0 3 ? * * *)"

    recovery_point_tags = {
      Environment = var.environment
      Backup      = "daily"
    }

    lifecycle {
      cold_storage_after = 7
      delete_after       = 30
    }
  }

  tags = var.tags
}
```

## Multi-Region Setup

### Primary Region (us-east-1)

```hcl
# Primary cluster in us-east-1
module "primary_cluster" {
  source = "../modules/eks-cluster"

  providers = {
    aws = aws.primary
  }

  cluster_name = "${var.cluster_name}-primary"
  vpc_cidr     = "10.0.0.0/16"
  region       = "us-east-1"

  # Full configuration for primary region
  node_groups = var.primary_node_groups
  
  tags = merge(var.tags, {
    Region = "primary"
    DR     = "source"
  })
}
```

### DR Region (us-west-2)

```hcl
# DR cluster in us-west-2
module "dr_cluster" {
  source = "../modules/eks-cluster"

  providers = {
    aws = aws.dr
  }

  cluster_name = "${var.cluster_name}-dr"
  vpc_cidr     = "10.1.0.0/16"
  region       = "us-west-2"

  # Smaller configuration for DR
  node_groups = var.dr_node_groups
  
  tags = merge(var.tags, {
    Region = "dr"
    DR     = "target"
  })
}
```

## Troubleshooting

### Common Issues

1. **EKS Cluster Creation Fails**
   ```bash
   # Check IAM permissions
   aws sts get-caller-identity
   
   # Check VPC limits
   aws ec2 describe-vpcs --region us-east-1
   
   # Check available AZs
   aws ec2 describe-availability-zones --region us-east-1
   ```

2. **Node Group Launch Issues**
   ```bash
   # Check node group status
   aws eks describe-nodegroup --cluster-name cluster-name --nodegroup-name nodegroup-name
   
   # Check Auto Scaling Group
   aws autoscaling describe-auto-scaling-groups
   
   # Check EC2 instances
   aws ec2 describe-instances --filters "Name=tag:kubernetes.io/cluster/cluster-name,Values=owned"
   ```

3. **Networking Issues**
   ```bash
   # Check security groups
   aws ec2 describe-security-groups
   
   # Check route tables
   aws ec2 describe-route-tables
   
   # Check NAT gateways
   aws ec2 describe-nat-gateways
   ```

### Debugging Commands

```bash
# Terraform debugging
export TF_LOG=DEBUG
terraform plan

# AWS CLI debugging
aws eks describe-cluster --name cluster-name --region us-east-1

# kubectl debugging
kubectl get nodes -o wide
kubectl describe node node-name
kubectl get pods --all-namespaces
```

This comprehensive Terraform documentation provides a complete Infrastructure as Code solution for deploying the Agentic AI Customer Support system on AWS EKS with production-ready configurations, security best practices, and operational procedures.
