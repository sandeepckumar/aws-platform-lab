resource "aws_internet_gateway" "this" {
  count  = var.create_igw ? 1 : 0
  vpc_id = aws_vpc.this.id
  tags = {
    Name = var.igw_name
  }
}

resource "aws_internet_gateway_attachment" "this" {
  count              = var.create_igw ? 1 : 0
  internet_gateway_id = aws_internet_gateway.this[0].id
  vpc_id             = aws_vpc.this.id
}
