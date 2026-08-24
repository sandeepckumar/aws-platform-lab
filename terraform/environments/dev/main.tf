module "network" {
  source     = "../../modules/network"
  vpc        = var.vpc
  subnets    = var.subnets
  create_igw = var.create_igw
  igw_name   = var.igw_name
}