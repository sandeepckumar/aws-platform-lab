resource "aws_internet_gateway" "this" {
  count  = var.create_igw ? 1 : 0
  vpc_id = aws_vpc.this.id
  tags = {
    Name = var.igw_name
  }
}
