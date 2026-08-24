resource "aws_route_table" "public" {
  count  = var.create_igw ? 1 : 0
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }
}

resource "aws_route_table_association" "public" {
  for_each = var.create_igw ? {
    for key, subnet in var.subnets : key => subnet
    if subnet.public == true
  } : {}
  subnet_id      = aws_subnet.this[each.key].id
  route_table_id = aws_route_table.public[0].id
}