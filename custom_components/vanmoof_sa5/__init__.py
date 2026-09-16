"""The VanMoof SA5 Home Assistant integration."""
from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .api import async_bootstrap_client
from .const import DOMAIN, PLATFORMS
from .coordinator import VanMoofDataUpdateCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VanMoof SA5 from a config entry."""
    api = await async_bootstrap_client(hass, dict(entry.data))
    coordinator = VanMoofDataUpdateCoordinator(hass, entry, api)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform(platform) for platform in PLATFORMS]
    )
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # BLE fetches can take minutes if the bike is unreachable; run the first
    # refresh in the background instead of blocking setup on it, otherwise
    # Home Assistant's bootstrap can forcibly cancel this integration's setup.
    entry.async_create_background_task(
        hass, coordinator.async_refresh(), "vanmoof_sa5_initial_refresh"
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry, [Platform(platform) for platform in PLATFORMS]
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
