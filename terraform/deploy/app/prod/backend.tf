terraform {
  cloud {
    organization = "exaf-epfl"
    workspaces {
      name = "unite-compression-prod"
    }
  }
}
