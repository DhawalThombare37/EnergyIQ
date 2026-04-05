from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF
import random

class NetworkAnimation(QWidget):
    def __init__(self, tech_name, parent=None):
        super().__init__(parent)
        self.tech_name = tech_name
        self.setMinimumHeight(250)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50) # 20 FPS
        
        self.packets = [] # List of {'pos': QPointF, 'velocity': float, 'type': str}
        self.nodes = [] # [{'pos': QPoint, 'type': 'tower/router/server'}]
        self.setup_scene()

    def setup_scene(self):
        w, h = 600, 250
        if self.tech_name in ['2G', '3G', '4G LTE', '5G']:
            self.nodes = [
                {'pos': QPoint(50, 125), 'type': 'Tower'},
                {'pos': QPoint(550, 125), 'type': 'Phone'}
            ]
        elif self.tech_name == 'WiFi':
            self.nodes = [
                {'pos': QPoint(300, 125), 'type': 'Router'},
                {'pos': QPoint(100, 180), 'type': 'Laptop'},
                {'pos': QPoint(500, 180), 'type': 'Phone'}
            ]
        elif self.tech_name == 'VPN':
            self.nodes = [
                {'pos': QPoint(50, 125), 'type': 'User'},
                {'pos': QPoint(550, 125), 'type': 'Server'}
            ]

    def update_animation(self):
        # Add new packets randomly based on tech speed (pseudoreality)
        if random.random() < 0.2:
            self.spawn_packet()
            
        # Move packets
        new_packets = []
        for p in self.packets:
            p['progress'] += 0.02
            if p['progress'] < 1.0:
                new_packets.append(p)
        self.packets = new_packets
        self.update()

    def spawn_packet(self):
        if not self.nodes: return
        start_node = self.nodes[0]
        end_node = self.nodes[-1]
        self.packets.append({
            'start': start_node['pos'],
            'end': end_node['pos'],
            'progress': 0,
            'color': QColor(0, 255, 0) if self.tech_name != 'VPN' else QColor(0, 191, 255)
        })

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        # Draw VPN Tunnel if needed
        if self.tech_name == 'VPN':
            painter.setPen(QPen(QColor(100, 100, 100, 100), 40, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.nodes[0]['pos'], self.nodes[-1]['pos'])
            painter.setPen(QPen(QColor(0, 191, 255, 50), 30))
            painter.drawLine(self.nodes[0]['pos'], self.nodes[-1]['pos'])

        # Draw Nodes
        for node in self.nodes:
            painter.setBrush(QColor(200, 200, 200))
            painter.drawEllipse(node['pos'], 15, 15)
            painter.setPen(Qt.white)
            painter.drawText(node['pos'].x() - 20, node['pos'].y() + 30, node['type'])

        # Draw Packets
        for p in self.packets:
            x = p['start'].x() + (p['end'].x() - p['start'].x()) * p['progress']
            y = p['start'].y() + (p['end'].y() - p['start'].y()) * p['progress']
            
            painter.setBrush(p['color'])
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(int(x), int(y)), 5, 5)
            
            if self.tech_name == 'VPN':
                 # Draw "lock" shield for VPN packets
                 painter.setBrush(QColor(255, 215, 0, 150))
                 painter.drawRect(int(x)-3, int(y)-8, 6, 6)
