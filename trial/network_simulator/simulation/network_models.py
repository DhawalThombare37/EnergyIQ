from utils.constants import TECH_CONFIGS, DEFAULT_PARAMS
from simulation.calculations import (
    calculate_snr, calculate_shannon_capacity, estimate_latency, 
    estimate_packet_loss, estimate_power_usage
)

class NetworkModel:
    def __init__(self, tech_name):
        self.tech_name = tech_name
        self.config = TECH_CONFIGS[tech_name]
        self.params = {
            'distance': DEFAULT_PARAMS['distance'],
            'users': DEFAULT_PARAMS['users'],
            'signal_power': DEFAULT_PARAMS['signal_power'],
            'noise_level': DEFAULT_PARAMS['noise_level'],
            'bandwidth': (self.config['bandwidth'][0] + self.config['bandwidth'][1]) / 2,
            'congestion': 0.1,
            'security_level': 1
        }
    
    def update_params(self, key, value):
        self.params[key] = value

    def simulate(self):
        """Perform simulation based on current parameters."""
        snr = calculate_snr(self.params['signal_power'], self.params['noise_level'])
        
        # Adjust throughput based on users and tech limits
        potential_throughput = calculate_shannon_capacity(self.params['bandwidth'], snr)
        actual_throughput = min(potential_throughput / max(1, self.params['users']), self.config['speed_max'])
        
        # VPN Overhead
        latency_overhead = 0
        if self.tech_name == 'VPN':
            latency_overhead = self.params['security_level'] * 10
            actual_throughput *= (1 - (self.params['security_level'] * 0.05))

        latency = estimate_latency(
            self.config['latency_base'], 
            self.params['distance'], 
            self.params['users'] * self.params['congestion']
        ) + latency_overhead
        
        packet_loss = estimate_packet_loss(
            self.params['distance'], 
            self.config['range'][1], 
            self.params['noise_level']
        )
        
        # Jitter is loosely related to congestion and latency
        jitter = (latency * 0.1) * (1 + self.params['congestion'])
        
        power = estimate_power_usage(
            self.config['power_usage'], 
            actual_throughput, 
            self.params['signal_power']
        )

        return {
            'throughput': actual_throughput,
            'latency': latency,
            'jitter': jitter,
            'packet_loss': packet_loss,
            'power': power,
            'snr': snr
        }
