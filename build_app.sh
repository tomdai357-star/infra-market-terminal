#!/bin/bash

# Clean up previous build artifacts
rm -rf build dist "Market Terminal.spec"

# Compile the application with all required Finplot and XGBoost backends
/usr/local/bin/python3 -m PyInstaller --name "Market Terminal" --windowed --noconfirm --exclude-module PyQt6 --collect-all finplot --collect-all xgboost ui.py

echo "Build complete! Check the /dist folder for the application."