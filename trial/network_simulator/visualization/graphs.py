import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class RealTimeGraph(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, title="Real-Time Data"):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#2b2b2b')
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor('#2b2b2b')
        self.axes.tick_params(colors='white')
        self.axes.set_title(title, color='white')
        
        # Style the plot
        self.axes.spines['bottom'].set_color('white')
        self.axes.spines['top'].set_color('white')
        self.axes.spines['left'].set_color('white')
        self.axes.spines['right'].set_color('white')
        
        super(RealTimeGraph, self).__init__(fig)
        self.setParent(parent)
        
        self.data_x = []
        self.data_y = []
        self.line, = self.axes.plot([], [], 'r-', linewidth=2)
        
    def update_plot(self, new_x, new_y, label_x="X", label_y="Y", color='#2ecc71'):
        self.data_x.append(new_x)
        self.data_y.append(new_y)
        
        # Keep last 50 points
        if len(self.data_x) > 50:
            self.data_x.pop(0)
            self.data_y.pop(0)
            
        self.line.set_data(self.data_x, self.data_y)
        self.line.set_color(color)
        
        if self.data_x:
            self.axes.set_xlim(min(self.data_x), max(self.data_x) + 0.1)
            self.axes.set_ylim(min(self.data_y) * 0.9, max(self.data_y) * 1.1 + 0.1)
            
        self.axes.set_xlabel(label_x, color='white')
        self.axes.set_ylabel(label_y, color='white')
        self.draw()

    def clear(self):
        self.data_x = []
        self.data_y = []
        self.line.set_data([], [])
        self.draw()
