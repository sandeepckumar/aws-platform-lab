resource "aws_vpc" "this" {
  cidr_block = var.vpc.cidr

  tags = {
    Name = var.vpc.name
  }
}

resource "aws_subnet" "this" {
  for_each                = var.subnets
  vpc_id                  = aws_vpc.this.id
  cidr_block              = each.value.cidr
  map_public_ip_on_launch = each.value.public
  avaiability_zone        = each.value.az
  tags = {
    Name = each.value.name
  }
}

