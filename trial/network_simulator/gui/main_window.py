from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QFrame, QScrollArea
from PyQt5.QtCore import Qt
from gui.technology_window import TechWindow
from utils.constants import TECH_CONFIGS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wireless Network Technology Simulator")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QLabel { color: white; font-family: Segoe UI; }
            QPushButton { 
                background-color: #34495e; 
                color: white; 
                border-radius: 10px; 
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3e5871; }
            QFrame#Card { 
                background-color: #1e1e1e; 
                border: 2px solid #333; 
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("<h1>Interactive Wireless Simulator</h1>")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        subheader = QLabel("<p style='font-size: 16px; color: #888;'>Select a technology to begin simulation and analysis</p>")
        subheader.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subheader)
        main_layout.addSpacing(30)
        
        # Grid for Tech Cards
        grid_layout = QGridLayout()
        technologies = list(TECH_CONFIGS.keys())
        
        for i, tech in enumerate(technologies):
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)
            
            title = QLabel(f"<h3>{tech}</h3>")
            title.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(title)
            
            desc = QLabel(f"<p style='color: {TECH_CONFIGS[tech]['color']}; font-weight: bold;'>{self.get_tech_summary(tech)}</p>")
            desc.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(desc)
            
            btn = QPushButton("Open Simulation")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=tech: self.open_tech_window(t))
            card_layout.addWidget(btn)
            
            grid_layout.addWidget(card, i // 3, i % 3)
            
        main_layout.addLayout(grid_layout)
        main_layout.addStretch()

    def get_tech_summary(self, tech):
        config = TECH_CONFIGS[tech]
        if tech == 'VPN':
            return "Secure Encrypted Tunnel"
        return f"Max {config['speed_max']} Mbps"

    def open_tech_window(self, tech):
        self.tech_window = TechWindow(tech)
        self.tech_window.show()
