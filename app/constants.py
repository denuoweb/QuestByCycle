from datetime import timezone, timedelta

# Shared timezone aware constant
UTC = timezone.utc

# Mapping quest frequency strings to their time delta
FREQUENCY_DELTA = {
    'daily': timedelta(days=1),
    'weekly': timedelta(weeks=1),
    'monthly': timedelta(days=30),
}

# Administrative subscription offer
ADMIN_UPGRADE_PRICE = 10  # USD per month
ADMIN_STORAGE_GB = 5      # Storage allowance in gigabytes
ADMIN_RETENTION_DAYS = 60  # Data retention period in days

