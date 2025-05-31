from homeassistant.core import HomeAssistant
from .const import DOMAIN  # Import DOMAIN instead of redefining it

async def async_setup(hass: HomeAssistant, config: dict):
    # Optional: you can log something or set up integration-wide values here
    return True