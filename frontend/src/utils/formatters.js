export function formatWarehouse(warehouseId, warehouseName) {
  if (warehouseName && warehouseName !== warehouseId) {
    return `${warehouseName} (${warehouseId})`;
  }
  return `Warehouse ${warehouseId}`;
}

export function formatDriver(driverId, driverName) {
  if (driverName && driverName !== driverId) {
    return `${driverName} (${driverId})`;
  }
  return `Driver ${driverId}`;
}

export function formatRouteOption(optionId, featureVector) {
  if (!optionId) return '';
  const [warehouseId, driverId] = optionId.split('::');
  const wh = featureVector?.warehouse_options?.find(w => w.warehouse_id === warehouseId);
  const drv = featureVector?.available_drivers?.find(d => d.driver_id === driverId);
  return `${formatWarehouse(warehouseId, wh?.name)} with ${formatDriver(driverId, drv?.name)}`;
}

export function decisionToLabel(decision) {
  const map = { confirm: 'Confirmed', qualify: 'Confirmed with Conditions', override: 'Override Applied' };
  return map[decision] ?? decision;
}

// Strip legacy bracketed IDs like [WH-SF01::DRV-001] from backend text.
export function sanitizeOptionIds(text) {
  if (!text) return text;
  return text.replace(/\[([A-Z0-9-]+)::([A-Z0-9-]+)\]/g, 'Warehouse $1 with Driver $2');
}

export function capitalizePriority(priority) {
  if (!priority) return 'Standard';
  return priority.charAt(0).toUpperCase() + priority.slice(1).toLowerCase();
}

export function formatCurrencyUSD(value) {
  if (value == null) return 'N/A';
  return `$${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
