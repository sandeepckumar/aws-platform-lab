resource "aws_internet_gateway" "this" {
  count  = var.create_igw ? 1 : 0
  vpc_id = aws_vpc.this.id
  tags = {
    Name = var.ig_name
  }
}

resource "aws_internet_gateway_attachment" {
  count              = var.create_igw ? 1 : 0
  internet_gatway_id = aws_internet_gateway.this.id
  vpc_id             = aws_vpc.this.id
}
