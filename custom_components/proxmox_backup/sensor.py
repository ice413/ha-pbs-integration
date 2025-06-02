from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .coordinator import ProxmoxBackupCoordinator
from .const import DOMAIN
import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Proxmox Backup sensors from a config entry using DataUpdateCoordinator."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

#    coordinator = ProxmoxBackupCoordinator(hass, entry)
#    await coordinator.async_config_entry_first_refresh()



    sensors = []

    # Usage sensors
    usage_data = coordinator.data.get("usage", {})
    for store_name, usage in usage_data.items():
        sensors.append(ProxmoxBackupSensor(coordinator, store_name, usage))

    # Snapshot sensors aggregation
    snapshot_counts_per_node = {}
    snapshot_sizes_per_node = {}
    total_snapshots_count = 0
    total_snapshots_size = 0

    for snap in coordinator.data.get("snapshots", []):
        backup_type = snap.get("backup-type")
        backup_id = snap.get("backup-id")
        size = snap.get("size", 0)
        if not backup_type or not backup_id:
            continue

        key = (backup_type, backup_id)
        snapshot_counts_per_node[key] = snapshot_counts_per_node.get(key, 0) + 1
        snapshot_sizes_per_node[key] = snapshot_sizes_per_node.get(key, 0) + size

        total_snapshots_count += 1
        total_snapshots_size += size

    for (backup_type, backup_id), count in snapshot_counts_per_node.items():
        size_bytes = snapshot_sizes_per_node.get((backup_type, backup_id), 0)
        sensors.append(ProxmoxSnapshotSensorPerNode(coordinator, backup_type, backup_id, count, size_bytes))

    sensors.append(ProxmoxSnapshotTotalSensor(coordinator, total_snapshots_count, total_snapshots_size))

    # GC sensors
    for gc_entry in coordinator.data.get("gc", []):
        store = gc_entry.get("store")
        if store:
            sensors.append(ProxmoxBackupGCSensor(coordinator, store, gc_entry))

    async_add_entities(sensors)


class ProxmoxBackupSensor(Entity):
    def __init__(self, coordinator, store_name):
        self.coordinator = coordinator
        self._store_name = store_name

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    @property
    def name(self):
        return f"Proxmox Backup {self._store_name} Usage"

    @property
    def unique_id(self):
        return f"proxmox_backup_usage_{self._store_name}"

    @property
    def state(self):
        usage = self._get_usage()
        return usage.get("used", 0)

    @property
    def extra_state_attributes(self):
        usage = self._get_usage()
        used = usage.get("used", 0)
        total = usage.get("total", 0)
        avail = usage.get("avail", 0)
        return {
            "used_bytes": used,
            "total_bytes": total,
            "available_bytes": avail,
            "used_percent": round((used / total) * 100, 2) if total else None,
            "free_percent": round((avail / total) * 100, 2) if total else None,
        }

    def _get_usage(self):
        return self.coordinator.data.get("usage", {}).get(self._store_name, {})

    @property
    def device_class(self):
        return "data_size"

    @property
    def unit_of_measurement(self):
        return "bytes"

    @property
    def icon(self):
        return "mdi:harddisk"

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.coordinator.last_update_success



class ProxmoxSnapshotSensorPerNode(Entity):
    def __init__(self, coordinator, backup_type, backup_id):
        self.coordinator = coordinator
        self._backup_type = backup_type
        self._backup_id = backup_id

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    @property
    def name(self):
        return f"Proxmox Backup {self._backup_type}/{self._backup_id} Snapshots"

    @property
    def unique_id(self):
        return f"proxmox_backup_{self._backup_type}_{self._backup_id}_snapshots"

    @property
    def state(self):
        return self._get_snapshot_count()

    @property
    def extra_state_attributes(self):
        size = self._get_snapshot_size()
        return {
            "backup_type": self._backup_type,
            "backup_id": self._backup_id,
            "snapshot_count": self._get_snapshot_count(),
            "total_snapshot_size_bytes": size,
            "total_snapshot_size_human": self._human_readable_size(size),
        }

    def _get_snapshot_count(self):
        return sum(
            1 for snap in self.coordinator.data.get("snapshots", [])
            if snap.get("backup-type") == self._backup_type and snap.get("backup-id") == self._backup_id
        )

    def _get_snapshot_size(self):
        return sum(
            snap.get("size", 0) for snap in self.coordinator.data.get("snapshots", [])
            if snap.get("backup-type") == self._backup_type and snap.get("backup-id") == self._backup_id
        )

    def _human_readable_size(self, size, decimal_places=2):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.{decimal_places}f} {unit}"
            size /= 1024
        return f"{size:.{decimal_places}f} PB"

    @property
    def icon(self):
        return "mdi:backup-restore"

    @property
    def device_class(self):
        return "count"

    @property
    def unit_of_measurement(self):
        return "snapshots"

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.coordinator.last_update_success



class ProxmoxSnapshotTotalSensor(Entity):
    def __init__(self, coordinator):
        self.coordinator = coordinator

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    @property
    def name(self):
        return "Proxmox Backup Total Snapshots"

    @property
    def unique_id(self):
        return "proxmox_backup_total_snapshots"

    @property
    def state(self):
        return len(self.coordinator.data.get("snapshots", []))

    @property
    def extra_state_attributes(self):
        total_size = sum(snap.get("size", 0) for snap in self.coordinator.data.get("snapshots", []))
        return {
            "total_snapshot_count": len(self.coordinator.data.get("snapshots", [])),
            "total_snapshot_size_bytes": total_size,
            "total_snapshot_size_human": self._human_readable_size(total_size),
        }

    def _human_readable_size(self, size, decimal_places=2):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.{decimal_places}f} {unit}"
            size /= 1024
        return f"{size:.{decimal_places}f} PB"

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.coordinator.last_update_success



class ProxmoxBackupGCSensor(Entity):
    def __init__(self, coordinator, store):
        self.coordinator = coordinator
        self._store = store

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    @property
    def name(self):
        return f"Proxmox Backup GC Status {self._store}"

    @property
    def unique_id(self):
        return f"proxmox_backup_gc_status_{self._store.lower()}"

    @property
    def state(self):
        gc_data = self._get_gc_data()
        return gc_data.get("last-run-state", "unknown")

    @property
    def extra_state_attributes(self):
        gc_data = self._get_gc_data()
        dedup_factor = self._calculate_dedup_factor(gc_data)
        return {
            "store": self._store,
            "last_run_endtime": self._format_timestamp(gc_data.get("last-run-endtime")),
            "next_run": self._format_timestamp(gc_data.get("next-run")),
            "removed_bytes": gc_data.get("removed-bytes"),
            "removed_chunks": gc_data.get("removed-chunks"),
            "index_data_bytes": gc_data.get("index-data-bytes"),
            "disk_bytes": gc_data.get("disk-bytes"),
            "deduplication_factor": dedup_factor,
        }

    def _get_gc_data(self):
        for entry in self.coordinator.data.get("gc", []):
            if entry.get("store") == self._store:
                return entry
        return {}

    def _format_timestamp(self, ts):
        if ts is None:
            return None
        try:
            return datetime.fromtimestamp(ts).isoformat()
        except Exception:
            return str(ts)

    def _calculate_dedup_factor(self, gc_data):
        index_data = gc_data.get("index-data-bytes", 0)
        disk_data = gc_data.get("disk-bytes", 1)
        return round(index_data / disk_data, 2) if disk_data else None

    @property
    def icon(self):
        return "mdi:recycle"

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self.coordinator.last_update_success


