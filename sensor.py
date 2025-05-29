from homeassistant.helpers.entity import Entity
from .const import DOMAIN
from .api import ProxmoxBackupAPI

def setup_platform(hass, config, add_entities, discovery_info=None):
    host = config.get("host")
    username = config.get("username")
    password = config.get("password")
    
    api = ProxmoxBackupAPI(host, username, password)
    datastores = api.get_datastores()

    sensors = [ProxmoxBackupSensor(ds["name"], ds["usage"]) for ds in datastores]
    add_entities(sensors, True)

class ProxmoxBackupSensor(Entity):
    def __init__(self, name, usage):
        self._name = f"PBS Datastore {name}"
        self._state = usage["used"] / usage["total"] * 100
        self._attr = {
            "total": usage["total"],
            "used": usage["used"],
            "avail": usage["avail"],
        }

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return round(self._state, 2)

    @property
    def extra_state_attributes(self):
        return self._attr