import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
    QGraphicsView, QGraphicsScene, QListWidget, QWidget, QSplitter, QFileDialog,
    QCheckBox
)
from PyQt5.QtGui import QPixmap, QPen
from PyQt5.QtCore import Qt, QRectF
import fitz  # PyMuPDF
import os
import json

class PDFViewer(QMainWindow):
    def __init__(self, pdf_path):
        super().__init__()
        self.setWindowTitle("PDF Figure Extractor")

        # Figure tracking
        self.next_figure_number = 1  # Global figure counter
        self.current_detailed_figure = None

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
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

        # Detailed Figure Checkbox
        self.detailed_checkbox = QCheckBox("Detailed Figure")
        self.detailed_checkbox.stateChanged.connect(self.toggle_detailed_mode)
        right_layout.addWidget(self.detailed_checkbox)

        # Control Buttons
        self.add_figure_button = QPushButton("Add Figure")
        self.add_figure_button.clicked.connect(self.add_figure)
        self.add_figure_button.setEnabled(False)

        # New buttons for detailed mode
        self.add_full_figure_button = QPushButton("Add Full Figure")
        self.add_full_figure_button.clicked.connect(self.add_full_figure)
        self.add_full_figure_button.setEnabled(False)
        self.add_full_figure_button.hide()

        self.add_panel_button = QPushButton("Add Panel")
        self.add_panel_button.clicked.connect(self.add_panel)
        self.add_panel_button.setEnabled(False)
        self.add_panel_button.hide()

        self.save_button = QPushButton("Save Figures")
        self.save_button.clicked.connect(self.save_figures)
        self.save_button.setEnabled(False)

        self.prev_button = QPushButton("Previous Page")
        self.prev_button.clicked.connect(self.prev_page)
        self.prev_button.setEnabled(False)

        self.next_button = QPushButton("Next Page")
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)

        # Updated figure tracking
        self.figure_boxes = []  # Will store (page, rect, type, figure_number, panel_number)
        self.detailed_mode = False
        self.panel_count = 0  # Tracks panels for current detailed figure

        # Add Buttons to Right Layout
        right_layout.addWidget(self.add_figure_button)
        right_layout.addWidget(self.add_full_figure_button)
        right_layout.addWidget(self.add_panel_button)
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
        self.figure_boxes = []  # Store boxes as tuples (page, QRectF, type, parent_id)
        self.current_figure_id = 0  # To track the parent figure for panels
        self.detailed_mode = False

        self.graphics_view.mousePressEvent = self.start_box
        self.graphics_view.mouseMoveEvent = self.update_box
        self.graphics_view.mouseReleaseEvent = self.finish_box

        # Load PDF
        if pdf_path:
            self.load_pdf(pdf_path)

    def toggle_detailed_mode(self, state):
        self.detailed_mode = bool(state)
        if self.detailed_mode:
            self.add_figure_button.hide()
            self.add_full_figure_button.show()
            self.add_panel_button.show()
        else:
            self.add_figure_button.show()
            self.add_full_figure_button.hide()
            self.add_panel_button.hide()
        
        # Reset buttons state based on selection
        if self.selection_box:
            if self.detailed_mode:
                self.add_full_figure_button.setEnabled(True)
                self.add_panel_button.setEnabled(True)
            else:
                self.add_figure_button.setEnabled(True)

    def load_pdf(self, file_path):
        if file_path and os.path.exists(file_path):
            self.pdf_document = fitz.open(file_path)
            self.current_page = 0
            self.show_page()
            self.save_button.setEnabled(True)
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)
        else:
            print(f"Error: File '{file_path}' does not exist.")

    def show_page(self):
        if self.pdf_document:
            page = self.pdf_document[self.current_page]
            pix = page.get_pixmap(dpi=150)
            img_path = "temp_page.png"
            pix.save(img_path)

            pixmap = QPixmap(img_path)
            self.current_pixmap = pixmap
            self.scene.clear()
            self.scene.addPixmap(pixmap)
            self.selection_box = None

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
            if self.detailed_mode:
                self.add_full_figure_button.setEnabled(True)
                self.add_panel_button.setEnabled(True)
            else:
                self.add_figure_button.setEnabled(True)

    def add_figure(self):
        if self.selection_box:
            rect = self.selection_box.rect()
            figure_number = self.next_figure_number
            self.figure_boxes.append((self.current_page, rect, "single", figure_number, None))
            self.figure_list.addItem(f"Figure {figure_number}")
            self.add_figure_button.setEnabled(False)
            self.next_figure_number += 1

    def add_full_figure(self):
        if self.selection_box:
            rect = self.selection_box.rect()
            self.current_detailed_figure = self.next_figure_number
            self.panel_count = 0
            self.figure_boxes.append((
                self.current_page, 
                rect, 
                "full", 
                self.current_detailed_figure,
                None
            ))
            self.figure_list.addItem(f"Figure {self.current_detailed_figure} (Full)")
            self.add_full_figure_button.setEnabled(False)
            # Don't increment next_figure_number yet - wait until all panels are done

    def add_panel(self):
        if self.selection_box:
            rect = self.selection_box.rect()
            self.panel_count += 1
            self.figure_boxes.append((
                self.current_page, 
                rect, 
                "panel", 
                self.current_detailed_figure,
                self.panel_count
            ))
            self.figure_list.addItem(
                f"Figure {self.current_detailed_figure} Panel {self.panel_count}"
            )
            self.add_panel_button.setEnabled(False)

    def toggle_detailed_mode(self, state):
        self.detailed_mode = bool(state)
        if self.detailed_mode:
            self.add_figure_button.hide()
            self.add_full_figure_button.show()
            self.add_panel_button.show()
            # If we're switching to detailed mode and were in the middle of something,
            # increment the figure number to ensure we don't reuse numbers
            if self.current_detailed_figure != self.next_figure_number - 1:
                self.current_detailed_figure = None
        else:
            # If we're switching out of detailed mode, make sure to increment the figure number
            # past the last detailed figure we were working on
            if self.current_detailed_figure is not None:
                self.next_figure_number = self.current_detailed_figure + 1
                self.current_detailed_figure = None
            self.add_figure_button.show()
            self.add_full_figure_button.hide()
            self.add_panel_button.hide()
        
        if self.selection_box:
            if self.detailed_mode:
                self.add_full_figure_button.setEnabled(True)
                self.add_panel_button.setEnabled(True)
            else:
                self.add_figure_button.setEnabled(True)

    def save_figures(self):
        if len(sys.argv) < 3:
            print("Error: No output directory specified.")
            return
        
        output_folder = sys.argv[2]
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        metadata = {"figures": []}
        
        # Sort the figure_boxes by figure number and panel number
        sorted_boxes = sorted(
            self.figure_boxes,
            key=lambda x: (x[3], x[4] if x[4] is not None else -1)
        )

        for page_num, rect, fig_type, figure_number, panel_number in sorted_boxes:
            page = self.pdf_document[page_num]
            x_scale = page.rect.width / self.current_pixmap.width()
            y_scale = page.rect.height / self.current_pixmap.height()

            fitz_rect = fitz.Rect(
                rect.left() * x_scale, rect.top() * y_scale,
                rect.right() * x_scale, rect.bottom() * y_scale
            )

            if fitz_rect.is_empty or fitz_rect.width <= 0 or fitz_rect.height <= 0:
                continue

            # Generate filename based on type
            if fig_type == "single":
                filename = f"figure_{figure_number}.png"
            elif fig_type == "full":
                filename = f"figure_{figure_number}_full.png"
            else:  # panel
                filename = f"figure_{figure_number}_panel_{panel_number}.png"

            # Save the image
            pix = page.get_pixmap(clip=fitz_rect, dpi=150)
            img_path = os.path.join(output_folder, filename)
            pix.save(img_path)

            # Add to metadata
            metadata["figures"].append({
                "filename": filename,
                "type": fig_type,
                "figure_number": figure_number,
                "panel_number": panel_number,
                "page": page_num + 1,
                "bbox": [rect.left(), rect.top(), rect.right(), rect.bottom()]
            })

        # Save metadata
        metadata_path = os.path.join(output_folder, "figures_metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Reset everything after saving
        self.figure_boxes = []
        self.current_detailed_figure = None
        self.panel_count = 0
        self.figure_list.clear()

        # If we were in detailed mode, increment the figure number
        if self.detailed_mode:
            self.next_figure_number += 1
    def next_page(self):
        if self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.show_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gui.py /path/to/paper.pdf /path/to/output/dir")
        sys.exit(1)

    pdf_path = sys.argv[1]
    app = QApplication(sys.argv)
    viewer = PDFViewer(pdf_path)
    viewer.show()
    sys.exit(app.exec_())
