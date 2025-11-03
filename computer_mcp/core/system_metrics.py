"""System metrics collection for performance monitoring."""

from typing import Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def get_system_metrics() -> dict[str, Any]:
    """Collect system performance metrics.
    
    Returns:
        Dictionary with system metrics including:
        - memory: RAM utilization
        - cpu: CPU utilization (per-core and overall)
        - disk: Disk I/O statistics
        - network: Network I/O statistics
        - processes: Number of running processes
        - boot_time: System boot time
        - error: Error message if psutil is not available
    """
    if not PSUTIL_AVAILABLE:
        return {"error": "psutil not available", "note": "Install psutil to enable system metrics"}
    
    try:
        metrics = {}
        
        # Memory utilization
        memory = psutil.virtual_memory()
        metrics["memory"] = {
            "total_bytes": memory.total,
            "available_bytes": memory.available,
            "used_bytes": memory.used,
            "percent": memory.percent,
            "free_bytes": memory.free,
        }
        
        # Swap memory (if available)
        try:
            swap = psutil.swap_memory()
            metrics["swap"] = {
                "total_bytes": swap.total,
                "used_bytes": swap.used,
                "free_bytes": swap.free,
                "percent": swap.percent,
            }
        except Exception:
            pass
        
        # CPU utilization
        cpu_percent = psutil.cpu_percent(interval=0.1)  # Small interval for quick response
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_count = psutil.cpu_count()
        cpu_freq = None
        try:
            freq = psutil.cpu_freq()
            if freq:
                cpu_freq = {
                    "current_mhz": freq.current,
                    "min_mhz": freq.min if freq.min else None,
                    "max_mhz": freq.max if freq.max else None,
                }
        except Exception:
            pass
        
        metrics["cpu"] = {
            "percent": cpu_percent,
            "per_core_percent": cpu_per_core,
            "count": cpu_count,
            "frequency_mhz": cpu_freq,
        }
        
        # Disk I/O
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics["disk"] = {
                    "read_bytes": disk_io.read_bytes,
                    "write_bytes": disk_io.write_bytes,
                    "read_count": disk_io.read_count,
                    "write_count": disk_io.write_count,
                    "read_time_ms": disk_io.read_time if hasattr(disk_io, 'read_time') else None,
                    "write_time_ms": disk_io.write_time if hasattr(disk_io, 'write_time') else None,
                }
        except Exception:
            pass
        
        # Disk usage for all partitions
        try:
            disk_usage = []
            partitions = psutil.disk_partitions(all=False)
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_bytes": usage.total,
                        "used_bytes": usage.used,
                        "free_bytes": usage.free,
                        "percent": usage.percent,
                    })
                except (PermissionError, OSError):
                    # Skip partitions we can't access
                    continue
            if disk_usage:
                metrics["disk_partitions"] = disk_usage
        except Exception:
            pass
        
        # Network I/O
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                metrics["network"] = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "errin": net_io.errin if hasattr(net_io, 'errin') else None,
                    "errout": net_io.errout if hasattr(net_io, 'errout') else None,
                    "dropin": net_io.dropin if hasattr(net_io, 'dropin') else None,
                    "dropout": net_io.dropout if hasattr(net_io, 'dropout') else None,
                }
        except Exception:
            pass
        
        # Network interfaces (active connections)
        try:
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            interfaces = []
            for interface_name, addrs in net_if_addrs.items():
                stats = net_if_stats.get(interface_name)
                interface_info = {
                    "name": interface_name,
                    "addresses": [
                        {
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask if addr.netmask else None,
                            "broadcast": addr.broadcast if addr.broadcast else None,
                        }
                        for addr in addrs
                    ],
                }
                if stats:
                    interface_info["stats"] = {
                        "isup": stats.isup,
                        "speed_mbps": stats.speed if stats.speed > 0 else None,
                        "mtu": stats.mtu if stats.mtu > 0 else None,
                    }
                interfaces.append(interface_info)
            if interfaces:
                metrics["network_interfaces"] = interfaces
        except Exception:
            pass
        
        # Process count
        try:
            metrics["processes"] = {
                "count": len(psutil.pids()),
            }
        except Exception:
            pass
        
        # Boot time
        try:
            metrics["boot_time"] = psutil.boot_time()
        except Exception:
            pass
        
        # Load average (Unix-like systems)
        try:
            load_avg = psutil.get_loadavg()
            if load_avg:
                metrics["load_average"] = {
                    "1min": load_avg[0],
                    "5min": load_avg[1],
                    "15min": load_avg[2],
                }
        except Exception:
            # Not available on Windows
            pass
        
        return metrics
    
    except Exception as e:
        return {"error": f"Failed to collect system metrics: {str(e)}"}

