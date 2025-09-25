provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "Terraform"
    }
  }
}

# Example VPC module usage
module "vpc" {
  source = "../../modules/vpc"
  
  environment = var.environment
  vpc_cidr    = var.vpc_cidr
  
  # Add other VPC configuration as needed
}

# Example EC2 module usage
module "ec2" {
  source = "../../modules/ec2"
  
  environment = var.environment
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnet_ids
  
  instance_type = var.instance_type
  
  # Add other EC2 configuration as needed
}

# GitHub OIDC Provider and Role
module "github_oidc" {
  source = "../../modules/github-oidc"
  
  project_name            = var.project_name
  github_org              = var.github_org
  github_repo             = var.github_repo
  terraform_state_bucket  = var.terraform_state_bucket
}