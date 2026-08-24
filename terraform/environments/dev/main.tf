module "network" {
  source = "../modules/network"
  vpc = var.vpc 
  subnets = var.subnets
}