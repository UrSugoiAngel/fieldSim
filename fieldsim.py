# Simulate an electrostatic field from points on a 2D plane

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import io
from PIL import Image

import sys
from PySide6 import QtCore, QtWidgets, QtGui

class UI(QtWidgets.QWidget):
    sign = 1
    def __init__(self):
        super().__init__()

        self.fs = FieldSim()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Field Simulator')
        self.setGeometry(100, 100, 800, 800)
        
        # Main layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.layout)
        
        # Top horizontal layout for the clear button
        top_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(top_layout)
        
        # Add clear button to left side
        self.clrBtn = QtWidgets.QPushButton('Clear Charges')
        self.clrBtn.clicked.connect(self.fs.clear_charges)
        self.clrBtn.clicked.connect(self.update_field)  # Make sure to update after clearing
        top_layout.addWidget(self.clrBtn, alignment=QtCore.Qt.AlignLeft)
        
        # Add stretch to push button to the left
        top_layout.addStretch(1)
        
        # Canvas for the field
        self.canvas = QtWidgets.QLabel(self)
        self.canvas.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.canvas)
        
        # Bottom control panel
        bottom_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(bottom_layout)
        
        self.posnegBtn = QtWidgets.QPushButton('Positive/Negative')
        self.posnegBtn.clicked.connect(self.toggle_charge)
        bottom_layout.addWidget(self.posnegBtn)
        
        self.chrgstrInput = QtWidgets.QLineEdit(self)
        self.chrgstrInput.setPlaceholderText('Enter charge strength in Coulombs')
        self.chrgstrInput.setStyleSheet("color: red;")
        bottom_layout.addWidget(self.chrgstrInput)
        
        self.update_field()
        self.show()
    
    def mousePressEvent(self, event):
        # Get canvas position and dimensions
        canvas_rect = self.canvas.geometry()
        canvas_pos = self.canvas.mapToGlobal(QtCore.QPoint(0, 0))
        window_pos = self.mapToGlobal(QtCore.QPoint(0, 0))
        
        # Calculate relative position within canvas
        rel_x = event.position().x() - (canvas_rect.x())
        rel_y = event.position().y() - (canvas_rect.y())
        
        # Calculate position as ratio of canvas dimensions
        ratio_x = rel_x / canvas_rect.width()
        ratio_y = rel_y / canvas_rect.height()
        
        # Only process clicks within the canvas bounds
        if 0 <= ratio_x <= 1 and 0 <= ratio_y <= 1:
            if event.button() == QtCore.Qt.LeftButton:
                # Convert to field coordinates
                x = ratio_x * self.fs.POINTS_X
                y = ratio_y * self.fs.POINTS_Y
                self.fs.add_charge(x, y, self.sign * float(self.chrgstrInput.text()))
                self.update_field()
            elif event.button() == QtCore.Qt.RightButton:
                # Clear charges on right click
                self.fs.clear_charges()
                self.update_field()
    
    def update_field(self):
        qimg = self.fs.get_plot()
        self.canvas.setPixmap(QtGui.QPixmap.fromImage(qimg))

    def toggle_charge(self):
        self.sign = -1 if self.sign == 1 else 1
        if self.sign == 1:
            self.chrgstrInput.setStyleSheet("color: red;")
        else:
            self.chrgstrInput.setStyleSheet("color: blue;")


class FieldSim:
    POINTS_X = 100
    POINTS_Y = 100
    K = 8.99e9
    pointvals = []

    charges = [{'x': 20, 'y': 70, 'q': 0.04}]

    def __init__(self):
        self.pointvals = [self.POINTS_X * [0] for _i in range(self.POINTS_Y)]

    def add_charge(self, x, y, q):
        self.charges.append({'x': x, 'y': y, 'q': q})
    
    def clear_charges(self):
        self.charges = []
    
    def get_field(self):
        x = np.arange(self.POINTS_X)
        y = np.arange(self.POINTS_Y)
        X, Y = np.meshgrid(x, y)
        field = np.zeros((self.POINTS_Y, self.POINTS_X))
        for charge in self.charges:
            dx = X - charge['x']
            dy = Y - charge['y']
            r = np.sqrt(dx**2 + dy**2)
            r[r == 0] = np.nan
            field += self.K * charge['q'] / (r**2)
        field = np.nan_to_num(field)
        return field
    
    def plot_field(self):
        field = np.array(self.get_field())
        norm = colors.SymLogNorm(linthresh=2e4, linscale=0.03,
                                 vmin=np.percentile(field, 5) if np.min(field) < 0 else -np.max(field),
                                 vmax=np.percentile(field, 95))
        plt.imshow(field, cmap='coolwarm', interpolation='gaussian', norm=norm)
        plt.show()

    def get_plot(self):
        field = np.array(self.get_field())
        fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
        
        # Force the colormap to be symmetric around zero
        if(np.max(field) == 0 and np.min(field) == 0):
            vmax = 1
            vmin = -1
        else:
            vmax = np.max(np.abs(field))
            vmin = -vmax
        
        norm = colors.SymLogNorm(linthresh=8e4, linscale=0.03, 
                                vmin=vmin, vmax=vmax)
        
        ax.imshow(field, cmap='coolwarm', interpolation='gaussian', norm=norm)
        ax.axis('off')
        fig.tight_layout(pad=0)
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        
        # Convert PIL Image to QImage
        pil_img = Image.open(buf)
        img_data = pil_img.convert("RGBA").tobytes("raw", "RGBA")
        qimg = QtGui.QImage(img_data, pil_img.width, pil_img.height, QtGui.QImage.Format_RGBA8888)
        
        return qimg
    
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ui = UI()
    sys.exit(app.exec())