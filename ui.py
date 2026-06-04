import sys
import json
import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class MarketTerminalWindow(QMainWindow):
    """
    The master window interface for the Infrastructure Resource & Market Terminal.
    Establishes the window properties, dark theme styling, and layout framework.
    """
    def __init__(self):
        super().__init__()
        
        # 1. Configure Window Properties
        self.setWindowTitle("Infrastructure Resource & Market Terminal")
        self.resize(1280, 800)  # Standard HD workstation aspect ratio
        self.setMinimumSize(1024, 640)
        
        # Apply a clean, modern dark styling palette to the window environment
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121214;
            }
            QLabel {
                color: #E2E8F0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        # 2. Setup Central Widget and Layout Framework
        # QMainWindow requires a central widget to anchor layout hierarchies
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # We use a vertical box layout to stack components cleanly from top to bottom
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)
        
        # 3. Component Placeholders
        self._initialize_placeholder_ui()
        
        logging.info("Main application window initialized successfully.")

    def _initialize_placeholder_ui(self):
        """Creates structural placeholders for controls and charts to verify layout integrity."""
        
        # Header/Status Bar Widget
        self.status_label = QLabel("Terminal Engine Active | Storage Layer: DuckDB Connected")
        self.status_label.setStyleSheet("font-size: 11px; color: #64748B; font-weight: bold;")
        self.main_layout.addWidget(self.status_label, alignment=Qt.AlignRight)
        
        # Placeholder for Step 2: Interactive Control Panel
        self.control_panel_frame = QFrame()
        self.control_panel_frame.setFixedHeight(80)
        self.control_panel_frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A1E;
                border: 1px solid #2D2D34;
                border-radius: 6px;
            }
        """)
        
        control_layout = QVBoxLayout(self.control_panel_frame)
        control_msg = QLabel("Placeholder: Interactive Control Panel (Dropdowns, Sliders, and Run Actions Go Here)")
        control_msg.setStyleSheet("color: #A0AEC0; font-size: 13px;")
        control_layout.addWidget(control_msg, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(self.control_panel_frame)
        
        # Placeholder for Step 3: High-Performance Chart Panel (finplot)
        self.chart_frame = QFrame()
        self.chart_frame.setStyleSheet("""
            QFrame {
                background-color: #1A1A1E;
                border: 1px solid #2D2D34;
                border-radius: 6px;
            }
        """)
        
        chart_layout = QVBoxLayout(self.chart_frame)
        chart_msg = QLabel("Placeholder: High-Performance Multi-Axis Chart Canvas (finplot Engine)")
        chart_msg.setStyleSheet("color: #A0AEC0; font-size: 14px; font-weight: bold;")
        chart_layout.addWidget(chart_msg, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(self.chart_frame, stretch=1) # Stretch=1 forces chart to claim remaining space

def main():
    """Main entry point to initialize and spin up the Qt application loop."""
    app = QApplication(sys.argv)
    
    # Instantiate and display our layout canvas
    window = MarketTerminalWindow()
    window.show()
    
    # Hand execution over to the Qt OS window event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()