output "public_ip_address" {
  value = azurerm_linux_virtual_machine.main.public_ip_address
}

output "admin_user" {
  value     = azurerm_linux_virtual_machine.main.admin_username
}