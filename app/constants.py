from datetime import timezone, timedelta

# Shared timezone aware constant
UTC = timezone.utc

# Mapping quest frequency strings to their time delta
FREQUENCY_DELTA = {
    'daily': timedelta(days=1),
    'weekly': timedelta(weeks=1),
    'monthly': timedelta(days=30),
}
