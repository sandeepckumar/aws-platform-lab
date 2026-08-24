variable "vpc" {
  description = "Name and CIDR for VPC"
  type = object(
    { name = string
    cidr = string }
  )
}

variable "subnets" {
  description = "Subnet configuration"
  type = map(object({
    cidr   = string
    public = optional(bool, false)
    az     = string
    name   = string
    }
  ))
}

variable "create_igw" {
  description = "Need internet gateway?"
  type        = bool
  default     = false
}

variable "igw_name" {
  description = "Name for the IGW"
  type        = string
  default     = ""

  validation {
    condition     = var.create_igw ? var.igw_name != "" : true
    error_message = "igw_name is required when create_igw is set to true."
  }
}
