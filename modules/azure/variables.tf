variable "zone" {
  default     = "eastus"
  description = "Availability zone where resources will be deployed."
}

variable "prefix" {
  type        = string
  default     = "vtx"
  description = "Prefix of all resources."
}

variable "username" {
  default     = "crow"
  description = "The admin user to be created on the server."
}

variable "public_key" {
  default     = "./pub.key"
  description = "The public key for the admin user."
}