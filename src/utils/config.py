"""
Configuration centralisée PATAKS.
Valeurs modifiables sans recompiler.
"""

APP_NAME    = "PATAKS"
APP_VERSION = "2.0.0"
COMPANY     = "Petagoria"
WEBSITE     = "https://petagoria.com"

# Intervalles (secondes)
MONITOR_INTERVAL = 1.0
UI_REFRESH_MS    = 1000

# Seuils alertes (%)
CPU_WARN    = 70
CPU_CRIT    = 85
RAM_WARN    = 75
RAM_CRIT    = 90
TEMP_WARN   = 75
TEMP_CRIT   = 85
DISK_WARN   = 85
DISK_CRIT   = 95

# Historique graphiques (nb points)
HISTORY_LEN = 60
