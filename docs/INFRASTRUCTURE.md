# INFRASTRUCTURE

This guide explains how to provision and configure the production server using Terraform and Ansible.

## Terraform Setup

1. Install [Terraform](https://www.terraform.io/downloads) and the Google Cloud CLI.
2. Edit `infra/terraform/main.tf` with your project ID and service account email.
3. Initialize the working directory:
   ```bash
   cd infra/terraform
   terraform init
   ```
4. Apply the configuration to create the VM and firewall rules:
   ```bash
   terraform apply
   ```
   The public IP output will be used by Ansible.

## Ansible Provisioning

1. Install [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/index.html).
2. Export the environment variables referenced in `infra/ansible/group_vars/all/vault.yml`.
3. Update `infra/ansible/inventory.yml` with the VM IP and your OS login user.
4. Run the playbook:
   ```bash
   cd infra/ansible
   ansible-playbook -i inventory.yml site.yml
   ```
   This installs dependencies, sets up PostgreSQL, and configures Gunicorn and Nginx.
