provider "google" {
  project     = "<YOUR_GCP_PROJECT_ID>"
  region      = "us-west1"
  zone        = "us-west1-a"
}

resource "google_compute_instance" "questbycycle" {
  name         = "questbycycle"
  machine_type = "e2-small"
  zone         = "us-west1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 50
      type  = "pd-balanced"
    }
  }

  network_interface {
    network       = "default"
    access_config {} # Ephemeral external IP
  }

  tags = ["http-server", "https-server", "ssh-server"]

  metadata = {
    # Enables login via OS Login, not via instance SSH keys.
    enable-oslogin = "TRUE"
  }

  service_account {
    email  = "<YOUR_GCE_SERVICE_ACCOUNT_EMAIL>"
    scopes = ["cloud-platform"]
  }
}

resource "google_compute_firewall" "default-http" {
  name    = "allow-http"
  network = "default"
  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server"]
}

resource "google_compute_firewall" "default-https" {
  name    = "allow-https"
  network = "default"
  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["https-server"]
}

output "instance_ip" {
  value = google_compute_instance.questbycycle.network_interface[0].access_config[0].nat_ip
}
