terraform {
  backend "s3" {
    # Configurado vía backend-config en el pipeline
    encrypt = true
    
    dynamodb_table = "terraform-locks"
    
    # Versionado del state
    versioning = true
  }
  
  required_version = ">= 1.6.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}