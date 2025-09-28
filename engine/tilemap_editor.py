import sys
import json
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pygame
import numpy as np

class TilemapCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setMinimumSize(800, 600)
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.tile_size = 16
        self.zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 8.0
        
        self.camera_x = 0
        self.camera_y = 0
        
        self.grid_width = 100
        self.grid_height = 100
        self.world_data = np.zeros((self.grid_height, self.grid_width), dtype=int)
        self.collision_data = np.zeros((self.grid_height, self.grid_width), dtype=bool)
        
        self.show_grid = True
        self.show_viewport = True
        self.show_collision = True
        self.viewport_width = 320
        self.viewport_height = 180
        
        self.selected_tile = 0
        self.edit_mode = "paint"
        self.painting = False
        self.erasing = False
        self.last_painted_pos = None
        
        self.tileset_image = None
        self.tile_surfaces = []
        
        self.setMouseTracking(True)
        
    def set_tileset(self, image_path):
        self.tileset_image = QPixmap(image_path)
        if not self.tileset_image.isNull():
            self.extract_tiles()
            self.update()
    
    def extract_tiles(self):
        if not self.tileset_image:
            return
        
        self.tile_surfaces = []
        tiles_x = self.tileset_image.width() // self.tile_size
        tiles_y = self.tileset_image.height() // self.tile_size
        
        for y in range(tiles_y):
            for x in range(tiles_x):
                tile_rect = QRect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                tile_pixmap = self.tileset_image.copy(tile_rect)
                self.tile_surfaces.append(tile_pixmap)
    
    def set_edit_mode(self, mode):
        self.edit_mode = mode
        if mode == "paint":
            self.setCursor(Qt.ArrowCursor)
        elif mode == "collision":
            self.setCursor(Qt.CrossCursor)
        elif mode == "erase":
            self.setCursor(Qt.PointingHandCursor)
    
    def wheelEvent(self, event):
        old_zoom = self.zoom
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 1.0 / 1.1
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * zoom_factor))
        
        if old_zoom != self.zoom:
            mouse_pos = event.pos()
            world_x = (mouse_pos.x() + self.camera_x) / old_zoom
            world_y = (mouse_pos.y() + self.camera_y) / old_zoom
            
            new_screen_x = world_x * self.zoom
            new_screen_y = world_y * self.zoom
            
            self.camera_x = new_screen_x - mouse_pos.x()
            self.camera_y = new_screen_y - mouse_pos.y()

        self.update()
        self.parent.update_status()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.painting = True
            if self.edit_mode == "paint":
                self.paint_tile(event.pos())
            elif self.edit_mode == "collision":
                self.toggle_collision(event.pos())
            elif self.edit_mode == "erase":
                self.erase_tile(event.pos())
        elif event.button() == Qt.RightButton:
            self.erasing = True
            if self.edit_mode == "collision":
                self.remove_collision(event.pos())
            else:
                self.erase_tile(event.pos())
        elif event.button() == Qt.MiddleButton:
            self.setCursor(Qt.ClosedHandCursor)
            self.last_pan_pos = event.pos()
    
    def mouseMoveEvent(self, event):
        if self.painting:
            if self.edit_mode == "paint":
                self.paint_tile(event.pos())
            elif self.edit_mode == "collision":
                self.add_collision(event.pos())
            elif self.edit_mode == "erase":
                self.erase_tile(event.pos())
        elif self.erasing:
            if self.edit_mode == "collision":
                self.remove_collision(event.pos())
            else:
                self.erase_tile(event.pos())
        elif event.buttons() & Qt.MiddleButton:
            delta = event.pos() - self.last_pan_pos
            self.camera_x -= delta.x()
            self.camera_y -= delta.y()
            self.last_pan_pos = event.pos()
            self.update()
        
        world_x, world_y = self.screen_to_world(event.pos())
        if 0 <= world_x < self.grid_width and 0 <= world_y < self.grid_height:
            has_collision = self.collision_data[world_y, world_x]
            tile_id = self.world_data[world_y, world_x]
            self.parent.update_mouse_pos(world_x, world_y, tile_id, has_collision)
        else:
            self.parent.update_mouse_pos(world_x, world_y, 0, False)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.painting = False
            self.last_painted_pos = None
        elif event.button() == Qt.RightButton:
            self.erasing = False
        elif event.button() == Qt.MiddleButton:
            if self.edit_mode == "paint":
                self.setCursor(Qt.ArrowCursor)
            elif self.edit_mode == "collision":
                self.setCursor(Qt.CrossCursor)
            elif self.edit_mode == "erase":
                self.setCursor(Qt.PointingHandCursor)
    
    def keyPressEvent(self, event):
        move_speed = 20 / self.zoom
        if event.key() == Qt.Key_W:
            self.camera_y -= move_speed
        elif event.key() == Qt.Key_S:
            self.camera_y += move_speed
        elif event.key() == Qt.Key_A:
            self.camera_x -= move_speed
        elif event.key() == Qt.Key_D:
            self.camera_x += move_speed
        elif event.key() == Qt.Key_G:
            self.show_grid = not self.show_grid
        elif event.key() == Qt.Key_V:
            self.show_viewport = not self.show_viewport
        elif event.key() == Qt.Key_C:
            self.show_collision = not self.show_collision
        elif event.key() == Qt.Key_R:
            self.reset_view()
        elif event.key() == Qt.Key_1:
            self.set_edit_mode("paint")
            self.parent.paint_mode_btn.setChecked(True)
        elif event.key() == Qt.Key_2:
            self.set_edit_mode("collision")
            self.parent.collision_mode_btn.setChecked(True)
        elif event.key() == Qt.Key_3:
            self.set_edit_mode("erase")
            self.parent.erase_mode_btn.setChecked(True)
        
        self.update()
        self.parent.update_status()
    
    def screen_to_world(self, screen_pos):
        scaled_tile_size = self.tile_size * self.zoom
        world_x = int((screen_pos.x() + self.camera_x) // scaled_tile_size)
        world_y = int((screen_pos.y() + self.camera_y) // scaled_tile_size)
        return world_x, world_y
    
    def paint_tile(self, pos):
        world_x, world_y = self.screen_to_world(pos)
        
        if 0 <= world_x < self.grid_width and 0 <= world_y < self.grid_height:
            current_pos = (world_x, world_y)
            if self.last_painted_pos != current_pos:
                self.world_data[world_y, world_x] = self.selected_tile + 1
                self.last_painted_pos = current_pos
                self.update()
    
    def erase_tile(self, pos):
        world_x, world_y = self.screen_to_world(pos)
        
        if 0 <= world_x < self.grid_width and 0 <= world_y < self.grid_height:
            self.world_data[world_y, world_x] = 0
            self.update()
    
    def toggle_collision(self, pos):
        world_x, world_y = self.screen_to_world(pos)
        
        if 0 <= world_x < self.grid_width and 0 <= world_y < self.grid_height:
            self.collision_data[world_y, world_x] = not self.collision_data[world_y, world_x]
            self.update()
    
    def add_collision(self, pos):
        world_x, world_y = self.screen_to_world(pos)
        
        if 0 <= world_x < self.grid_width and 0 <= world_y < self.grid_height:
            self.collision_data[world_y, world_x] = True
            self.update()
    
    def remove_collision(self, pos):
        world_x, world_y = self.screen_to_world(pos)
        
        if 0 <= world_x < self.grid_width and 0 <= world_y < self.grid_height:
            self.collision_data[world_y, world_x] = False
            self.update()
    
    def reset_view(self):
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        self.update()
        self.parent.update_status()
    
    def clear_world(self):
        self.world_data = np.zeros((self.grid_height, self.grid_width), dtype=int)
        self.update()
    
    def clear_collisions(self):
        self.collision_data = np.zeros((self.grid_height, self.grid_width), dtype=bool)
        self.update()
    
    def resize_world(self, width, height):
        old_world_data = self.world_data.copy()
        old_collision_data = self.collision_data.copy()
        
        self.grid_width = width
        self.grid_height = height
        self.world_data = np.zeros((height, width), dtype=int)
        self.collision_data = np.zeros((height, width), dtype=bool)
        
        copy_height = min(old_world_data.shape[0], height)
        copy_width = min(old_world_data.shape[1], width)
        
        self.world_data[:copy_height, :copy_width] = old_world_data[:copy_height, :copy_width]
        self.collision_data[:copy_height, :copy_width] = old_collision_data[:copy_height, :copy_width]
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(45, 45, 45))
        
        if not self.tile_surfaces:
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(self.rect().center(), "Load a tileset to begin")
            return
        
        scaled_tile_size = self.tile_size * self.zoom
        
        start_x = max(0, int(self.camera_x // scaled_tile_size))
        end_x = min(self.grid_width, int((self.camera_x + self.width()) // scaled_tile_size) + 1)
        start_y = max(0, int(self.camera_y // scaled_tile_size))
        end_y = min(self.grid_height, int((self.camera_y + self.height()) // scaled_tile_size) + 1)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_x = x * scaled_tile_size - self.camera_x
                screen_y = y * scaled_tile_size - self.camera_y
                
                tile_id = self.world_data[y, x]
                if tile_id > 0 and tile_id <= len(self.tile_surfaces):
                    tile_pixmap = self.tile_surfaces[tile_id - 1]
                    scaled_pixmap = tile_pixmap.scaled(int(scaled_tile_size), int(scaled_tile_size), Qt.KeepAspectRatio, Qt.FastTransformation)
                    painter.drawPixmap(int(screen_x), int(screen_y), scaled_pixmap)
                
                if self.show_collision and self.collision_data[y, x]:
                    collision_color = QColor(255, 100, 150, 120)
                    painter.fillRect(int(screen_x), int(screen_y), int(scaled_tile_size), int(scaled_tile_size), collision_color)
                
                if self.show_grid and self.zoom >= 0.5:
                    painter.setPen(QColor(100, 100, 100))
                    painter.drawRect(int(screen_x), int(screen_y), int(scaled_tile_size), int(scaled_tile_size))
        
        if self.show_viewport:
            viewport_x = (self.viewport_width / 2) * self.zoom - self.camera_x
            viewport_y = (self.viewport_height / 2) * self.zoom - self.camera_y
            viewport_w = self.viewport_width * self.zoom
            viewport_h = self.viewport_height * self.zoom
            
            painter.setPen(QPen(QColor(255, 100, 100), 3))
            painter.drawRect(int(viewport_x - viewport_w/2), int(viewport_y - viewport_h/2), 
                           int(viewport_w), int(viewport_h))

class TilePalette(QWidget):
    tileSelected = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(250)
        self.setMinimumHeight(400)
        
        self.tile_surfaces = []
        self.selected_tile = 0
        self.tile_size = 16
        self.tiles_per_row = 12
        self.scroll_offset = 0
        
        self.setMouseTracking(True)
    
    def set_tiles(self, tile_surfaces):
        self.tile_surfaces = tile_surfaces
        self.selected_tile = 0
        self.scroll_offset = 0
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.tile_surfaces:
            tile_index = self.get_tile_at_pos(event.pos())
            if 0 <= tile_index < len(self.tile_surfaces):
                self.selected_tile = tile_index
                self.tileSelected.emit(tile_index)
                self.update()
    
    def wheelEvent(self, event):
        self.scroll_offset += event.angleDelta().y() // 120 * 20
        self.scroll_offset = max(0, self.scroll_offset)
        self.update()
    
    def get_tile_at_pos(self, pos):
        adjusted_y = pos.y() + self.scroll_offset
        row = adjusted_y // (self.tile_size + 2)
        col = pos.x() // (self.tile_size + 2)
        return row * self.tiles_per_row + col
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(40, 40, 40))
        
        if not self.tile_surfaces:
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(self.rect().center(), "No tiles loaded")
            return
        
        y_offset = -self.scroll_offset
        
        for i, tile in enumerate(self.tile_surfaces):
            row = i // self.tiles_per_row
            col = i % self.tiles_per_row
            
            x = col * (self.tile_size + 2) + 5
            y = row * (self.tile_size + 2) + 5 + y_offset
            
            if y + self.tile_size < 0 or y > self.height():
                continue
            
            painter.drawPixmap(x, y, tile)
            
            if i == self.selected_tile:
                painter.setPen(QPen(QColor(255, 255, 0), 2))
                painter.drawRect(x - 1, y - 1, self.tile_size + 2, self.tile_size + 2)

class TilemapEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Tilemap Editor")
        self.setGeometry(100, 100, 1400, 900)
        
        self.init_ui()
        self.init_menus()
        self.init_toolbar()
        self.init_status_bar()
        
        self.current_file = None
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        self.canvas = TilemapCanvas(self)
        self.palette = TilePalette(self)
        
        self.palette.tileSelected.connect(self.on_tile_selected)
        
        left_panel = QWidget()
        left_panel.setFixedWidth(280)
        left_layout = QVBoxLayout(left_panel)
        
        mode_group = QGroupBox("Edit Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_group_buttons = QButtonGroup()
        
        self.paint_mode_btn = QRadioButton("Paint Mode (1)")
        self.paint_mode_btn.setChecked(True)
        self.paint_mode_btn.toggled.connect(lambda: self.canvas.set_edit_mode("paint") if self.paint_mode_btn.isChecked() else None)
        
        self.collision_mode_btn = QRadioButton("Collision Mode (2)")
        self.collision_mode_btn.toggled.connect(lambda: self.canvas.set_edit_mode("collision") if self.collision_mode_btn.isChecked() else None)
        
        self.erase_mode_btn = QRadioButton("Erase Mode (3)")
        self.erase_mode_btn.toggled.connect(lambda: self.canvas.set_edit_mode("erase") if self.erase_mode_btn.isChecked() else None)
        
        self.mode_group_buttons.addButton(self.paint_mode_btn)
        self.mode_group_buttons.addButton(self.collision_mode_btn)
        self.mode_group_buttons.addButton(self.erase_mode_btn)
        
        mode_layout.addWidget(self.paint_mode_btn)
        mode_layout.addWidget(self.collision_mode_btn)
        mode_layout.addWidget(self.erase_mode_btn)
        
        left_layout.addWidget(mode_group)
        
        palette_label = QLabel("Tile Palette")
        palette_label.setStyleSheet("font-weight: bold; padding: 5px;")
        left_layout.addWidget(palette_label)
        left_layout.addWidget(self.palette)
        
        properties_group = QGroupBox("Properties")
        properties_layout = QFormLayout(properties_group)
        
        self.world_width_spin = QSpinBox()
        self.world_width_spin.setRange(10, 500)
        self.world_width_spin.setValue(self.canvas.grid_width)
        self.world_width_spin.valueChanged.connect(self.on_world_size_changed)
        
        self.world_height_spin = QSpinBox()
        self.world_height_spin.setRange(10, 500)
        self.world_height_spin.setValue(self.canvas.grid_height)
        self.world_height_spin.valueChanged.connect(self.on_world_size_changed)
        
        self.tile_size_spin = QSpinBox()
        self.tile_size_spin.setRange(8, 64)
        self.tile_size_spin.setValue(self.canvas.tile_size)
        self.tile_size_spin.valueChanged.connect(self.on_tile_size_changed)
        
        self.viewport_width_spin = QSpinBox()
        self.viewport_width_spin.setRange(100, 1000)
        self.viewport_width_spin.setValue(self.canvas.viewport_width)
        self.viewport_width_spin.valueChanged.connect(self.on_viewport_changed)
        
        self.viewport_height_spin = QSpinBox()
        self.viewport_height_spin.setRange(100, 1000)
        self.viewport_height_spin.setValue(self.canvas.viewport_height)
        self.viewport_height_spin.valueChanged.connect(self.on_viewport_changed)
        
        properties_layout.addRow("World Width:", self.world_width_spin)
        properties_layout.addRow("World Height:", self.world_height_spin)
        properties_layout.addRow("Tile Size:", self.tile_size_spin)
        properties_layout.addRow("Viewport Width:", self.viewport_width_spin)
        properties_layout.addRow("Viewport Height:", self.viewport_height_spin)
        
        self.grid_checkbox = QCheckBox("Show Grid (G)")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.toggled.connect(self.on_grid_toggled)
        
        self.viewport_checkbox = QCheckBox("Show Viewport (V)")
        self.viewport_checkbox.setChecked(True)
        self.viewport_checkbox.toggled.connect(self.on_viewport_toggled)
        
        self.collision_checkbox = QCheckBox("Show Collision (C)")
        self.collision_checkbox.setChecked(True)
        self.collision_checkbox.toggled.connect(self.on_collision_toggled)
        
        properties_layout.addRow(self.grid_checkbox)
        properties_layout.addRow(self.viewport_checkbox)
        properties_layout.addRow(self.collision_checkbox)
        
        left_layout.addWidget(properties_group)
        
        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout(tools_group)
        
        clear_tiles_btn = QPushButton("Clear Tiles")
        clear_tiles_btn.clicked.connect(self.canvas.clear_world)
        tools_layout.addWidget(clear_tiles_btn)
        
        clear_collision_btn = QPushButton("Clear Collisions")
        clear_collision_btn.clicked.connect(self.canvas.clear_collisions)
        tools_layout.addWidget(clear_collision_btn)
        
        reset_view_btn = QPushButton("Reset View (R)")
        reset_view_btn.clicked.connect(self.canvas.reset_view)
        tools_layout.addWidget(reset_view_btn)
        
        left_layout.addWidget(tools_group)
        left_layout.addStretch()
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.canvas, 1)
    
    def init_menus(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        load_tileset_action = QAction("Load Tileset", self)
        load_tileset_action.setShortcut("Ctrl+T")
        load_tileset_action.triggered.connect(self.load_tileset)
        file_menu.addAction(load_tileset_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu("Edit")
        
        paint_action = QAction("Paint Mode", self)
        paint_action.setShortcut("1")
        paint_action.triggered.connect(lambda: self.set_mode("paint"))
        edit_menu.addAction(paint_action)
        
        collision_action = QAction("Collision Mode", self)
        collision_action.setShortcut("2")
        collision_action.triggered.connect(lambda: self.set_mode("collision"))
        edit_menu.addAction(collision_action)
        
        erase_action = QAction("Erase Mode", self)
        erase_action.setShortcut("3")
        erase_action.triggered.connect(lambda: self.set_mode("erase"))
        edit_menu.addAction(erase_action)
        
        view_menu = menubar.addMenu("View")
        
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl+=")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        zoom_reset_action = QAction("Reset Zoom", self)
        zoom_reset_action.setShortcut("Ctrl+0")
        zoom_reset_action.triggered.connect(self.canvas.reset_view)
        view_menu.addAction(zoom_reset_action)
        
        view_menu.addSeparator()
        
        grid_action = QAction("Toggle Grid", self)
        grid_action.setShortcut("G")
        grid_action.triggered.connect(lambda: self.grid_checkbox.setChecked(not self.grid_checkbox.isChecked()))
        view_menu.addAction(grid_action)
        
        viewport_action = QAction("Toggle Viewport", self)
        viewport_action.setShortcut("V")
        viewport_action.triggered.connect(lambda: self.viewport_checkbox.setChecked(not self.viewport_checkbox.isChecked()))
        view_menu.addAction(viewport_action)
        
        collision_action = QAction("Toggle Collision", self)
        collision_action.setShortcut("C")
        collision_action.triggered.connect(lambda: self.collision_checkbox.setChecked(not self.collision_checkbox.isChecked()))
        view_menu.addAction(collision_action)
    
    def init_toolbar(self):
        toolbar = self.addToolBar("Main")
        
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self.new_file)
        toolbar.addWidget(new_btn)
        
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_file)
        toolbar.addWidget(open_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_file)
        toolbar.addWidget(save_btn)
        
        toolbar.addSeparator()
        
        tileset_btn = QPushButton("Load Tileset")
        tileset_btn.clicked.connect(self.load_tileset)
        toolbar.addWidget(tileset_btn)
        
        toolbar.addSeparator()
        
        paint_btn = QPushButton("Paint")
        paint_btn.clicked.connect(lambda: self.set_mode("paint"))
        toolbar.addWidget(paint_btn)
        
        collision_btn = QPushButton("Collision")
        collision_btn.clicked.connect(lambda: self.set_mode("collision"))
        toolbar.addWidget(collision_btn)
        
        erase_btn = QPushButton("Erase")
        erase_btn.clicked.connect(lambda: self.set_mode("erase"))
        toolbar.addWidget(erase_btn)
    
    def init_status_bar(self):
        self.status_bar = self.statusBar()
        self.mouse_pos_label = QLabel("Mouse: (0, 0)")
        self.tile_info_label = QLabel("Tile: 0")
        self.collision_info_label = QLabel("Collision: No")
        self.zoom_label = QLabel("Zoom: 100%")
        self.camera_label = QLabel("Camera: (0, 0)")
        self.mode_label = QLabel("Mode: Paint")
        
        self.status_bar.addWidget(self.mouse_pos_label)
        self.status_bar.addWidget(self.tile_info_label)
        self.status_bar.addWidget(self.collision_info_label)
        self.status_bar.addPermanentWidget(self.mode_label)
        self.status_bar.addPermanentWidget(self.zoom_label)
        self.status_bar.addPermanentWidget(self.camera_label)
    
    def set_mode(self, mode):
        self.canvas.set_edit_mode(mode)
        if mode == "paint":
            self.paint_mode_btn.setChecked(True)
            self.mode_label.setText("Mode: Paint")
        elif mode == "collision":
            self.collision_mode_btn.setChecked(True)
            self.mode_label.setText("Mode: Collision")
        elif mode == "erase":
            self.erase_mode_btn.setChecked(True)
            self.mode_label.setText("Mode: Erase")
    
    def on_tile_selected(self, tile_index):
        self.canvas.selected_tile = tile_index
    
    def on_world_size_changed(self):
        width = self.world_width_spin.value()
        height = self.world_height_spin.value()
        self.canvas.resize_world(width, height)
    
    def on_tile_size_changed(self):
        self.canvas.tile_size = self.tile_size_spin.value()
        if self.canvas.tileset_image:
            self.canvas.extract_tiles()
            self.palette.set_tiles(self.canvas.tile_surfaces)
        self.canvas.update()
    
    def on_viewport_changed(self):
        self.canvas.viewport_width = self.viewport_width_spin.value()
        self.canvas.viewport_height = self.viewport_height_spin.value()
        self.canvas.update()
    
    def on_grid_toggled(self, checked):
        self.canvas.show_grid = checked
        self.canvas.update()
    
    def on_viewport_toggled(self, checked):
        self.canvas.show_viewport = checked
        self.canvas.update()
    
    def on_collision_toggled(self, checked):
        self.canvas.show_collision = checked
        self.canvas.update()
    
    def load_tileset(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Tileset", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        
        if file_path:
            self.canvas.set_tileset(file_path)
            self.palette.set_tiles(self.canvas.tile_surfaces)
    
    def new_file(self):
        self.canvas.clear_world()
        self.canvas.clear_collisions()
        self.current_file = None
        self.setWindowTitle("Advanced Tilemap Editor")
    
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Tilemap", "", "JSON Files (*.json)")
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.canvas.tile_size = data.get('tile_size', 16)
                self.canvas.grid_width = data.get('grid_width', 100)
                self.canvas.grid_height = data.get('grid_height', 100)
                self.canvas.viewport_width = data.get('viewport_width', 320)
                self.canvas.viewport_height = data.get('viewport_height', 180)
                
                world_data = data.get('world_data', [])
                if world_data:
                    self.canvas.world_data = np.array(world_data, dtype=int)
                else:
                    self.canvas.world_data = np.zeros((self.canvas.grid_height, self.canvas.grid_width), dtype=int)
                
                collision_data = data.get('collision_data', [])
                if collision_data:
                    self.canvas.collision_data = np.array(collision_data, dtype=bool)
                else:
                    self.canvas.collision_data = np.zeros((self.canvas.grid_height, self.canvas.grid_width), dtype=bool)
                
                self.world_width_spin.setValue(self.canvas.grid_width)
                self.world_height_spin.setValue(self.canvas.grid_height)
                self.tile_size_spin.setValue(self.canvas.tile_size)
                self.viewport_width_spin.setValue(self.canvas.viewport_width)
                self.viewport_height_spin.setValue(self.canvas.viewport_height)
                
                self.canvas.update()
                self.current_file = file_path
                self.setWindowTitle(f"Advanced Tilemap Editor - {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load file: {str(e)}")
    
    def save_file(self):
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Tilemap", "", "JSON Files (*.json)")
        
        if file_path:
            self.save_to_file(file_path)
            self.current_file = file_path
            self.setWindowTitle(f"Advanced Tilemap Editor - {os.path.basename(file_path)}")
    
    def save_to_file(self, file_path):
        try:
            data = {
                'tile_size': self.canvas.tile_size,
                'grid_width': self.canvas.grid_width,
                'grid_height': self.canvas.grid_height,
                'viewport_width': self.canvas.viewport_width,
                'viewport_height': self.canvas.viewport_height,
                'world_data': self.canvas.world_data.tolist(),
                'collision_data': self.canvas.collision_data.tolist()
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save file: {str(e)}")
    
    def zoom_in(self):
        self.canvas.zoom = min(self.canvas.max_zoom, self.canvas.zoom * 1.2)
        self.canvas.update()
        self.update_status()
    
    def zoom_out(self):
        self.canvas.zoom = max(self.canvas.min_zoom, self.canvas.zoom / 1.2)
        self.canvas.update()
        self.update_status()
    
    def update_mouse_pos(self, x, y, tile_id=0, has_collision=False):
        self.mouse_pos_label.setText(f"Mouse: ({x}, {y})")
        self.tile_info_label.setText(f"Tile: {tile_id}")
        self.collision_info_label.setText(f"Collision: {'Yes' if has_collision else 'No'}")
    
    def update_status(self):
        self.zoom_label.setText(f"Zoom: {int(self.canvas.zoom * 100)}%")
        self.camera_label.setText(f"Camera: ({int(self.canvas.camera_x)}, {int(self.canvas.camera_y)})")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
    dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    
    app.setPalette(dark_palette)
    
    editor = TilemapEditor()
    editor.show()
    
    sys.exit(app.exec_())