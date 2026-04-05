import math

def calculate_snr(signal_power, noise_level):
    """Calculate Signal-to-Noise Ratio."""
    return signal_power - noise_level

def calculate_shannon_capacity(bandwidth_mhz, snr_db):
    """Calculate theoretical max throughput using Shannon-Hartley theorem."""
    snr_linear = 10**(snr_db / 10)
    return bandwidth_mhz * math.log2(1 + snr_linear)

def estimate_latency(base_latency, distance_meters, congestion_factor):
    """Estimate latency based on distance and network congestion."""
    speed_of_light = 3e8
    propagation_delay = (distance_meters / speed_of_light) * 1000 # to ms
    return base_latency + propagation_delay + (congestion_factor * 10)

def estimate_packet_loss(distance, max_range, noise_level):
    """Simple model for packet loss probability."""
    if distance > max_range:
        return 100.0
    loss = (distance / max_range)**2 * 5 + abs(noise_level + 100) * 0.5
    return min(100.0, max(0.0, loss))

def estimate_power_usage(base_power, throughput, signal_power):
    """Estimate power consumption."""
    return base_power + (throughput * 0.01) + abs(signal_power) * 0.005
