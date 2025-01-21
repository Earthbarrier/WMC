import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
    QGraphicsView, QGraphicsScene, QListWidget, QWidget, QSplitter, QFileDialog
)
from PyQt5.QtGui import QPixmap, QPen
from PyQt5.QtCore import Qt, QRectF
import fitz  # PyMuPDF
import os


class PDFViewer(QMainWindow):
    def __init__(self, pdf_path):
        super().__init__()
        self.setWindowTitle("PDF Figure Extractor")

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()  # Horizontal layout for main window
        self.central_widget.setLayout(self.main_layout)

        # PDF View
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)

        # Splitter for Resizing
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.graphics_view)

        # Right Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        # List for Figures
        self.figure_list = QListWidget()
        right_layout.addWidget(self.figure_list)

        # Control Buttons
        self.add_figure_button = QPushButton("Add Figure")
        self.add_figure_button.clicked.connect(self.add_figure)
        self.add_figure_button.setEnabled(False)

        self.save_button = QPushButton("Save Figures")
        self.save_button.clicked.connect(self.save_figures)
        self.save_button.setEnabled(False)

        self.prev_button = QPushButton("Previous Page")
        self.prev_button.clicked.connect(self.prev_page)
        self.prev_button.setEnabled(False)

        self.next_button = QPushButton("Next Page")
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)

        # Add Buttons to Right Layout
        right_layout.addWidget(self.add_figure_button)
        right_layout.addWidget(self.save_button)
        right_layout.addWidget(self.prev_button)
        right_layout.addWidget(self.next_button)

        splitter.addWidget(right_panel)
        self.main_layout.addWidget(splitter)

        # PDF Variables
        self.pdf_document = None
        self.current_page = 0
        self.current_pixmap = None
        self.start_pos = None
        self.end_pos = None
        self.selection_box = None
        self.figure_boxes = []  # Store boxes as tuples (page, QRectF)

        self.graphics_view.mousePressEvent = self.start_box
        self.graphics_view.mouseMoveEvent = self.update_box
        self.graphics_view.mouseReleaseEvent = self.finish_box

        # Load PDF
        if pdf_path:
            self.load_pdf(pdf_path)

    def load_pdf(self, file_path):
        if file_path and os.path.exists(file_path):
            self.pdf_document = fitz.open(file_path)
            self.current_page = 0
            self.show_page()
            self.add_figure_button.setEnabled(False)
            self.save_button.setEnabled(True)
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)
        else:
            print(f"Error: File '{file_path}' does not exist.")

    def show_page(self):
        if self.pdf_document:
            page = self.pdf_document[self.current_page]
            pix = page.get_pixmap(dpi=150)  # High DPI for better quality
            img_path = "temp_page.png"
            pix.save(img_path)

            pixmap = QPixmap(img_path)
            self.current_pixmap = pixmap
            self.scene.clear()
            self.scene.addPixmap(pixmap)
            self.selection_box = None  # Clear previous selection box

    def start_box(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = self.graphics_view.mapToScene(event.pos())

    def update_box(self, event):
        if self.start_pos:
            self.end_pos = self.graphics_view.mapToScene(event.pos())
            if self.selection_box:
                self.scene.removeItem(self.selection_box)
            rect = QRectF(self.start_pos, self.end_pos).normalized()
            pen = QPen(Qt.red)
            pen.setWidth(2)
            self.selection_box = self.scene.addRect(rect, pen)

    def finish_box(self, event):
        if event.button() == Qt.LeftButton and self.start_pos and self.end_pos:
            self.end_pos = self.graphics_view.mapToScene(event.pos())
            self.add_figure_button.setEnabled(True)

    def add_figure(self):
        if self.selection_box:
            rect = self.selection_box.rect()
            self.figure_boxes.append((self.current_page, rect))
            self.figure_list.addItem(f"Page {self.current_page + 1}: {rect}")
            self.add_figure_button.setEnabled(False)

    def save_figures(self):
        # Get the output folder from command-line arguments
        if len(sys.argv) < 3:
            print("Error: No output directory specified.")
            return
        
        output_folder = sys.argv[2]

        # Ensure the output directory exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Iterate over figure_boxes to save figures
        for idx, (page_num, rect) in enumerate(self.figure_boxes):
            page = self.pdf_document[page_num]

            # Calculate scaling factors and convert QRectF to fitz.Rect
            x_scale = page.rect.width / self.current_pixmap.width()
            y_scale = page.rect.height / self.current_pixmap.height()

            fitz_rect = fitz.Rect(
                rect.left() * x_scale, rect.top() * y_scale,
                rect.right() * x_scale, rect.bottom() * y_scale
            )

            # Ensure the rectangle is valid
            if fitz_rect.is_empty or fitz_rect.width <= 0 or fitz_rect.height <= 0:
                continue

            # Generate and save the image
            pix = page.get_pixmap(clip=fitz_rect, dpi=150)
            img_path = os.path.join(output_folder, f"figure_{idx + 1}.png")
            pix.save(img_path)

        # Clear the figure boxes after saving
        self.figure_boxes = []
#
    def next_page(self):
        if self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.show_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()


# Run the application
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gui.py /path/to/paper.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    app = QApplication(sys.argv)
    viewer = PDFViewer(pdf_path)
    viewer.show()
    sys.exit(app.exec_())
