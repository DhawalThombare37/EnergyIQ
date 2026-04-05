from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QFrame, QGridLayout, QPushButton
from PyQt5.QtCore import Qt, QTimer
from visualization.graphs import RealTimeGraph
from visualization.animations import NetworkAnimation
from simulation.network_models import NetworkModel
from utils.constants import TECH_CONFIGS

class TechWindow(QWidget):
    def __init__(self, tech_name):
        super().__init__()
        self.tech_name = tech_name
        self.model = NetworkModel(tech_name)
        self.setWindowTitle(f"Simulation: {tech_name}")
        self.setMinimumSize(1000, 800)
        self.setStyleSheet("background-color: #1e1e1e; color: white; font-family: Segoe UI;")
        
        self.setup_ui()
        
        # Timer for real-time updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(1000) # Update metrics every second
        self.time_step = 0

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left Panel: Controls
        left_panel = QFrame()
        left_panel.setFixedWidth(300)
        left_panel.setStyleSheet("background-color: #2b2b2b; border-radius: 10px; padding: 10px;")
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel(f"<h2>{self.tech_name} Controls</h2>"))
        
        self.sliders = {}
        self.add_slider(left_layout, "Distance (m)", "distance", 1, self.model.config['range'][1])
        self.add_slider(left_layout, "Number of Users", "users", 1, 100)
        self.add_slider(left_layout, "Noise Level (dBm)", "noise_level", -120, -60)
        self.add_slider(left_layout, "Congestion (%)", "congestion", 0, 100)
        
        if self.tech_name == 'VPN':
            self.add_slider(left_layout, "Security Level", "security_level", 1, 10)

        left_layout.addStretch()
        main_layout.addWidget(left_panel)
        
        # Right Panel: Simulation & visualization
        right_layout = QVBoxLayout()
        
        # Top: Animation
        self.animation = NetworkAnimation(self.tech_name)
        right_layout.addWidget(self.animation)
        
        # Middle: Metrics Displays
        metrics_frame = QFrame()
        metrics_layout = QGridLayout(metrics_frame)
        self.metric_labels = {}
        
        metrics = ["Throughput", "Latency", "Jitter", "Packet Loss", "Power Usage"]
        for i, m in enumerate(metrics):
            lbl = QLabel(f"<b>{m}:</b> 0")
            lbl.setStyleSheet("font-size: 16px; color: #7f8c8d;")
            self.metric_labels[m] = lbl
            metrics_layout.addWidget(lbl, i // 3, i % 3)
            
        right_layout.addWidget(metrics_frame)
        
        # Bottom: Graphs
        graph_layout = QHBoxLayout()
        self.graph_throughput = RealTimeGraph(self, title="Throughput (Mbps)")
        self.graph_latency = RealTimeGraph(self, title="Latency (ms)")
        graph_layout.addWidget(self.graph_throughput)
        graph_layout.addWidget(self.graph_latency)
        right_layout.addLayout(graph_layout)
        
        main_layout.addLayout(right_layout)

    def add_slider(self, layout, label, key, min_val, max_val):
        layout.addWidget(QLabel(label))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(int(self.model.params.get(key, min_val)))
        slider.valueChanged.connect(lambda val, k=key: self.on_slider_change(k, val))
        layout.addWidget(slider)
        self.sliders[key] = slider

    def on_slider_change(self, key, value):
        if key == 'congestion':
            self.model.update_params(key, value / 100.0)
        else:
            self.model.update_params(key, value)
        self.update_simulation()

    def update_simulation(self):
        results = self.model.simulate()
        self.time_step += 1
        
        # Update Labels
        self.metric_labels["Throughput"].setText(f"<b>Throughput:</b> {results['throughput']:.2f} Mbps")
        self.metric_labels["Latency"].setText(f"<b>Latency:</b> {results['latency']:.2f} ms")
        self.metric_labels["Jitter"].setText(f"<b>Jitter:</b> {results['jitter']:.2f} ms")
        self.metric_labels["Packet Loss"].setText(f"<b>Packet Loss:</b> {results['packet_loss']:.2f} %")
        self.metric_labels["Power Usage"].setText(f"<b>Power Usage:</b> {results['power']:.2f} W")
        
        # Update Graphs
        color = TECH_CONFIGS[self.tech_name]['color']
        self.graph_throughput.update_plot(self.time_step, results['throughput'], "Time (s)", "Mbps", color)
        self.graph_latency.update_plot(self.time_step, results['latency'], "Time (s)", "ms", color)
