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