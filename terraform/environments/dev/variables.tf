variable "vpc" {
  description = "The CIDR range for VPC"
  type = object({
    name = string
    cidr = string
    }
  )
}

variable "subnets" {
  description = "Subnets configuration"
  type = map(object({
    cidr   = string
    public = optional(bool, false)
    az     = string
    name   = string
    }
    )
  )
}