import sys
import os

os.chdir('/Users/tomdai/Documents/infra-market-terminal')
os.environ["PYQTGRAPH_QT_LIB"] = "PySide6"
import json
import logging
import duckdb
import pandas as pd
import finplot as fplt
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QComboBox,
    QSpinBox,
    QPushButton,
    QCheckBox
)

from ml_engine import generate_forecast


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class MarketTerminalWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Infrastructure Resource & Market Terminal")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 640)
        
        # Apply dark theme styling
        self.setStyleSheet("""
            QMainWindow { background-color: #121214; }
            QLabel { color: #E2E8F0; font-family: 'Segoe UI', Arial, sans-serif; }
            QComboBox, QSpinBox { 
                background-color: #2D2D34; color: #FFFFFF; 
                border: 1px solid #4A4A5A; border-radius: 4px; padding: 5px;
            }
            QPushButton {
                background-color: #2563EB; color: white; font-weight: bold;
                border-radius: 4px; padding: 8px 15px;
            }
            QPushButton:hover { background-color: #3B82F6; }
        """)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)
        
        self.config_data = self._load_config()
        
        self._build_header()
        self._build_control_panel()
        self._build_chart_panel()

    def _load_config(self) -> dict:
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return {"assets": {"commodities": [], "civil_engineering": [], "mining": []}}

    def _build_header(self):
        self.status_label = QLabel("Terminal Engine Active | Storage Layer: DuckDB Connected")
        self.status_label.setStyleSheet("font-size: 11px; color: #64748B; font-weight: bold;")
        self.main_layout.addWidget(self.status_label, alignment=Qt.AlignRight)

    def _build_control_panel(self):
        self.control_frame = QFrame()
        self.control_frame.setStyleSheet("QFrame { background-color: #1A1A1E; border: 1px solid #2D2D34; border-radius: 6px; }")
        control_layout = QHBoxLayout(self.control_frame)
        control_layout.setContentsMargins(15, 15, 15, 15)
        
        control_layout.addWidget(QLabel("Primary Commodity:"))
        self.combo_commodity = QComboBox()
        for item in self.config_data.get("assets", {}).get("commodities", []):
            self.combo_commodity.addItem(f"{item['name']} ({item['ticker']})", item['ticker'])
        control_layout.addWidget(self.combo_commodity)
        
        control_layout.addWidget(QLabel("   Target Equity:"))
        self.combo_equity = QComboBox()
        for category in ["civil_engineering", "mining"]:
            for item in self.config_data.get("assets", {}).get(category, []):
                self.combo_equity.addItem(f"{item['name']} ({item['ticker']})", item['ticker'])
        control_layout.addWidget(self.combo_equity)
        
        control_layout.addWidget(QLabel("   Time-Lag Shift (Days):"))
        self.spin_lag = QSpinBox()
        self.spin_lag.setRange(0, 180)
        self.spin_lag.setSingleStep(30)
        self.spin_lag.setValue(90)
        control_layout.addWidget(self.spin_lag)
        
        # Add the AI Toggle
        self.chk_ml = QCheckBox("Enable AI Forecast")
        self.chk_ml.setStyleSheet("color: #F472B6; font-weight: bold;") # Neon Pink
        control_layout.addWidget(self.chk_ml)

        control_layout.addSpacing(20)
        self.btn_run = QPushButton("Run Analysis")
        self.btn_run.clicked.connect(self._on_run_clicked)
        control_layout.addWidget(self.btn_run)
        
        control_layout.addStretch()
        self.main_layout.addWidget(self.control_frame)

    def _build_chart_panel(self):
        """Initializes the embedded finplot canvas with dual Y-axes."""
        self.chart_frame = QFrame()
        self.chart_frame.setStyleSheet("QFrame { background-color: #121214; border: 1px solid #2D2D34; border-radius: 6px; }")
        chart_layout = QVBoxLayout(self.chart_frame)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        
        # Configure finplot global visuals
        fplt.background = '#121214'
        fplt.foreground = '#E2E8F0'
        fplt.cross_hair_color = '#64748B'
        
        # Create Primary Axis (Commodities) and Secondary Axis (Equities)
        self.ax = fplt.create_plot(init_zoom_periods=300)
        self.ax2 = self.ax.overlay() 
        
        # Embed the finplot Qt window into our PySide6 layout
        chart_layout.addWidget(self.ax.vb.win)
        self.main_layout.addWidget(self.chart_frame, stretch=1)
        
        # Boot finplot internally without taking over the main Qt event loop
        fplt.show(qt_exec=False)

    def _on_run_clicked(self):
        """The core mathematical engine and rendering handoff."""
        commodity = self.combo_commodity.currentData()
        equity = self.combo_equity.currentData()
        lag = self.spin_lag.value()
        
        try:
            # 1. Query DuckDB for overlapping date ranges
            # 1. Query DuckDB for overlapping date ranges (with read_only to prevent locking)
            with duckdb.connect("terminal_data.db", read_only=True) as conn:
                query = f"""
                    SELECT 
                        c.date,
                        c.close AS commodity_close,
                        c.close_ma_90 AS commodity_ma_90,
                        (e.close * fx.close) AS equity_close
                    FROM daily_assets c
                    JOIN daily_assets e ON c.date = e.date
                    JOIN daily_assets fx ON c.date = fx.date
                    WHERE c.ticker = '{commodity}' 
                      AND e.ticker = '{equity}'
                      AND fx.ticker = 'CADUSD=X'
                    ORDER BY c.date ASC
                """
                df = conn.execute(query).df()
                
            if df.empty:
                self.status_label.setText(f"Error: No overlapping database records for {commodity} vs {equity}.")
                return
                
            # 2. Apply Time-Lag Shift to Equities
            # Shifting forward organically drops the end dates where no future equity data exists yet
            # 2. Apply Time-Lag Shift to Equities
            df['equity_shifted'] = df['equity_close'].shift(-lag)
            df = df.dropna().reset_index(drop=True)
            
            # 3. Clear previous charts
            self.ax.reset()
            self.ax2.reset()
            
            # 4. Render Data
            fplt.plot(df['date'], df['commodity_close'], ax=self.ax, legend=f"{commodity} Raw", color='#3B82F6', width=1)
            fplt.plot(df['date'], df['commodity_ma_90'], ax=self.ax, legend=f"{commodity} 90-Day MA", color='#F59E0B', width=2)
            
            # Secondary Axis (Right)
            fplt.plot(df['date'], df['equity_shifted'], ax=self.ax2, legend=f"{equity} (+{lag} Days)", color='#10B981', width=2)
            
            # --- THE FIX: Track the min and max values for the right-hand axis ---
            y_min = df['equity_shifted'].min()
            y_max = df['equity_shifted'].max()

            # --- AI Forecasting Overlay ---
            if self.chk_ml.isChecked():
                try:
                    self.status_label.setText(f"Engine Active | Training XGBoost Model on RTX Hardware...")
                    QApplication.processEvents() 
                    
                    forecast_df = generate_forecast(commodity, equity, forecast_days=lag)
                    
                    # Plot the AI forecast
                    fplt.plot(forecast_df['date'], forecast_df['predicted_equity'], ax=self.ax2, legend="AI Price Forecast", color='#F472B6', width=3)
                    
                    # Expand the scale if the AI predicts prices higher or lower than historical data
                    y_min = min(y_min, float(forecast_df['predicted_equity'].min()))
                    y_max = max(y_max, float(forecast_df['predicted_equity'].max()))
                except Exception as e:
                    logging.error(f"ML Engine failed: {e}")
            
            # 5. Reset Zoom FIRST
            fplt.autoviewrestore()

            # --- THE FIX: Force the Secondary Axis to Auto-Scale AFTER zoom reset ---
            padding = (y_max - y_min) * 0.05
            fplt.set_y_range(y_min - padding, y_max + padding, ax=self.ax2)
            
            # --- Axis Labels & Title ---
            self.ax.setTitle(f"{commodity} vs {equity} Momentum ({lag}-Day Shift)", color="#E2E8F0", size="12pt")
            self.ax.setLabel('bottom', "Date", color="#64748B")
            self.ax.setLabel('left', "Commodity Price (USD)", color="#64748B")
            self.ax.showAxis('right')
            self.ax.setLabel('right', "Normalized Equity (USD)", color="#64748B")

            self.status_label.setText(f"Rendering Complete | Displaying {commodity} vs {equity} with a {lag}-Day Reporting Delay")

def main():
    app = QApplication(sys.argv)
    window = MarketTerminalWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()