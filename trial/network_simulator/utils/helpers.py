# Helper functions for the network simulator

def format_bits(bits):
    """Format bits into readable throughput strings."""
    if bits < 1e3:
        return f"{bits:.2f} bps"
    elif bits < 1e6:
        return f"{bits/1e3:.2f} Kbps"
    elif bits < 1e9:
        return f"{bits/1e6:.2f} Mbps"
    else:
        return f"{bits/1e9:.2f} Gbps"

def format_latency(ms):
    """Format latency into readable strings."""
    if ms < 1:
        return f"{ms*1000:.2f} \u03bcs"
    return f"{ms:.2f} ms"
