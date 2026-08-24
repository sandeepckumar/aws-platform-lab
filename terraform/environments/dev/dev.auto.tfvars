vpc = {
  name = "dev-vpc"
  cidr = "10.10.0.0/16"
}

subnets = {
  private_a = {
    cidr = "10.10.1.0/24"
    az   = "ap-south-2a"
    name = "dev-private-ap-south-2a"
  }
  private_b = {
    cidr = "10.10.2.0/24"
    az   = "ap-south-2b"
    name = "dev-private-ap-south-2b"
  }
  public_a = {
    cidr = "10.10.40.0/24"
    az   = "ap-south-2a"
    name = "dev-public-ap-south-2a"
  }
  public_b = {
    cidr = "10.10.41.0/24"
    az   = "ap-south-2b"
    name = "dev-public-ap-south-2b"
  }
}