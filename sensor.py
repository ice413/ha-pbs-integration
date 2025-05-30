import logging
from homeassistant.helpers.entity import Entity
from .api import ProxmoxBackupAPI

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Proxmox Backup sensors."""
    host = config.get("pbs_host")
    token_id = config.get("pbs_token_id")
    token = config.get("pbs_token")

    try:
        api = ProxmoxBackupAPI(host, token_id, token)
        response = api.get_datastores()
        datastores = response.get("data", [])
        sensors = []

        for ds in datastores:
            store_name = ds.get("store")
            if not store_name:
                _LOGGER.warning("Datastore missing 'store' key: %s", ds)
                continue

            usage_response = api.get_datastore_status(store_name)
            usage = usage_response.get("data", {})

            sensors.append(ProxmoxBackupSensor(store_name, usage))

        add_entities(sensors)

    except Exception as e:
        _LOGGER.error("Error setting up proxmox_backup sensors: %s", e)

class ProxmoxBackupSensor(Entity):
    def __init__(self, name, usage):
        self._name = name
        self._used = usage.get("used", 0)
        self._total = usage.get("total", 0)
        self._avail = usage.get("avail", 0)

    @property
    def name(self):
        return f"Proxmox Backup {self._name} Usage"

    @property
    def state(self):
        return self._used

    @property
    def extra_state_attributes(self):
        return {
            "used_bytes": self._used,
            "total_bytes": self._total,
            "available_bytes": self._avail,
            "used_percent": round((self._used / self._total) * 100, 2) if self._total else None,
            "free_percent": round((self._avail / self._total) * 100, 2) if self._total else None,
        }

