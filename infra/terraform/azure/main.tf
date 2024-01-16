locals {
  prefix = var.prefix
  username = var.username
  public_key = var.public_key
  private_key = var.private_key
}

resource "random_pet" "main" {
  prefix = local.prefix
  length = 1
}

# Create a resource group
resource "azurerm_resource_group" "main" {
  location = var.zone
  name     = random_pet.main.id
}

# Create virtual network
resource "azurerm_virtual_network" "main" {
  name                = random_pet.main.id
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

# Create subnet
resource "azurerm_subnet" "main" {
  name                 = random_pet.main.id
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.0.0/24"]
}

# Create public IPs
resource "azurerm_public_ip" "main" {
  name                = random_pet.main.id
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Dynamic"
}

# Create Network Security Group and rules
resource "azurerm_network_security_group" "main" {
  name                = random_pet.main.id
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "SSH"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

# Create network interface
resource "azurerm_network_interface" "main" {
  name                = random_pet.main.id
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {
    name                          = random_pet.main.id
    subnet_id                     = azurerm_subnet.main.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.main.id
  }
}

# Connect the security group to the network interface
resource "azurerm_network_interface_security_group_association" "main" {
  network_interface_id      = azurerm_network_interface.main.id
  network_security_group_id = azurerm_network_security_group.main.id
}

# Create virtual machine
resource "azurerm_linux_virtual_machine" "main" {
  name                = random_pet.main.id
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = "Standard_NC4as_T4_v3"
  admin_username      = local.username
  network_interface_ids = [
    azurerm_network_interface.main.id,
  ]

  admin_ssh_key {
    username   = local.username
    public_key = file(local.public_key)
  }

  os_disk {
    caching              = "ReadOnly"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 64

    diff_disk_settings {
      option = "Local"
    }
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }

  connection {
    type        = "ssh"
    user        = local.username
    private_key = "${file(local.private_key)}"
    host        = azurerm_linux_virtual_machine.main.public_ip_address
  }

  provisioner "file" {
    source      = "./infra/salt"
    destination = "/home/${local.username}"
  }

  provisioner "remote-exec" {
    on_failure = fail
    inline = [
      "set -o errexit",
      "sudo curl -fsSL -o /etc/apt/keyrings/salt-archive-keyring.gpg https://repo.saltproject.io/salt/py3/ubuntu/22.04/amd64/3005/salt-archive-keyring.gpg",
      "echo 'deb [signed-by=/etc/apt/keyrings/salt-archive-keyring.gpg arch=amd64] https://repo.saltproject.io/salt/py3/ubuntu/22.04/amd64/3005 jammy main' | sudo tee /etc/apt/sources.list.d/salt.list",
      "export DEBIAN_FRONTEND='noninteractive'",
      "sudo apt-get update",
      "echo 'pausing until cloud-init is complete",
      "sleep 90",
      "sudo apt-get update",
      "sudo apt-get install -y salt-minion salt-ssh",
      "sudo mkdir -p /etc/salt",
      "sudo mkdir -p /srv/salt",
      "sudo rm /etc/salt/minion",
      "sudo mv salt/etc/* /etc/salt/",
      "sudo mv salt/srv/* /srv/salt/",
      "sudo rm -rf salt",
      "sudo systemctl enable salt-minion && sudo systemctl start salt-minion",
      "sudo salt-call --local state.apply"
    ]
  }
}