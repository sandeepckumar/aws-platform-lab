terraform {
    backend "s3" {
      bucket = "skchenna-tflab-state-220828-sat"
      key = "tf-lab/state/dev/tf-lab.tfstate"
      region = "ap-south-2"
    }
}