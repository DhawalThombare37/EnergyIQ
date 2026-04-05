# Network Simulator Constants

TECH_CONFIGS = {
    '2G': {
        'range': (0, 35000), # meters
        'bandwidth': (0.2, 0.5), # MHz
        'speed_max': 0.1, # Mbps
        'latency_base': 300, # ms
        'power_usage': 1.0, # relative unit
        'color': '#f39c12'
    },
    '3G': {
        'range': (0, 5000),
        'bandwidth': (5.0, 10.0),
        'speed_max': 14.4,
        'latency_base': 100,
        'power_usage': 1.5,
        'color': '#3498db'
    },
    '4G LTE': {
        'range': (0, 2000),
        'bandwidth': (20.0, 40.0),
        'speed_max': 150,
        'latency_base': 30,
        'power_usage': 2.0,
        'color': '#2ecc71'
    },
    '5G': {
        'range': (0, 500),
        'bandwidth': (100.0, 400.0),
        'speed_max': 1000,
        'latency_base': 5,
        'power_usage': 2.5,
        'color': '#e74c3c'
    },
    'WiFi': {
        'range': (0, 100),
        'bandwidth': (20.0, 160.0),
        'speed_max': 600,
        'latency_base': 10,
        'power_usage': 0.5,
        'color': '#9b59b6'
    },
    'VPN': {
        'range': (0, 1000000), # Global
        'bandwidth': (10.0, 100.0),
        'speed_max': 100,
        'latency_base': 50, # Extra overhead
        'power_usage': 1.2,
        'color': '#34495e'
    }
}

DEFAULT_PARAMS = {
    'distance': 100,
    'users': 1,
    'signal_power': -70, # dBm
    'noise_level': -100 # dBm
}
