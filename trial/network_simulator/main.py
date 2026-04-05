import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt5.QtWidgets import QApplication
    from gui.main_window import MainWindow
except ImportError:
    print("Error: PyQt5 not found. Please run 'pip install PyQt5 matplotlib numpy'")
    sys.exit(1)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion') # Consistent modern look across platforms
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
