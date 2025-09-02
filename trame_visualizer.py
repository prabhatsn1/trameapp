#!/usr/bin/env python3
"""
Trame CSV 3D Visualizer
A web application for visualizing CSV data in 3D space with interactive controls.
"""

import os
import pandas as pd
import numpy as np
from trame.app import get_server
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3 as v3, vtk as vtk_widgets
import vtk
from vtk.util import numpy_support

# -----------------------------------------------------------------------------
# Trame setup
# -----------------------------------------------------------------------------

server = get_server()
state, ctrl = server.state, server.controller

# -----------------------------------------------------------------------------
# State variables
# -----------------------------------------------------------------------------

state.trame__title = "CSV 3D Visualizer"
state.csv_data = None
state.current_component_id = "All"
state.current_material_id = "All"
state.color_mode = "True_Temp"
state.available_component_ids = ["All"]
state.available_material_ids = ["All"]
state.data_loaded = False
state.status_message = "No data loaded. Please upload a CSV file or load sample data."
state.uploaded_files = []

# VTK setup
renderer = vtk.vtkRenderer()
renderer.SetBackground(0.1, 0.1, 0.2)  # Dark blue background
render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)
render_window.SetSize(800, 600)

# Initialize the interactor - this is crucial for Trame integration
render_window_interactor = vtk.vtkRenderWindowInteractor()
render_window_interactor.SetRenderWindow(render_window)

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def load_csv_data(file_path):
    """Load and process CSV data"""
    try:
        df = pd.read_csv(file_path)
        
        # Print actual column names for debugging
        print(f"Actual CSV columns: {list(df.columns)}")
        
        # Validate required columns - updated to match your exact column names
        required_cols = ['X (m)', 'Y (m)', 'Z (m)', 'Component ID', 'Material ID', 'True_Temp', 'Pred_Temp', 'Abs_Error']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            return None, f"Missing required columns: {', '.join(missing_cols)}"
            
        # Get unique values for dropdowns
        component_ids = sorted(df['Component ID'].unique().tolist())
        material_ids = sorted(df['Material ID'].unique().tolist())
        
        return df, component_ids, material_ids, "Data loaded successfully!"
    except Exception as e:
        return None, f"Error loading CSV: {str(e)}"

def get_color_array(df, color_mode):
    """Get color array based on selected mode"""
    if color_mode in df.columns:
        values = df[color_mode].values
        # Normalize values to 0-1 range for color mapping
        min_val, max_val = values.min(), values.max()
        if max_val > min_val:
            normalized = (values - min_val) / (max_val - min_val)
        else:
            normalized = np.zeros_like(values)
        return normalized, min_val, max_val
    return np.zeros(len(df)), 0, 1

def create_3d_points(df, color_mode):
    """Create VTK points for 3D visualization"""
    # Clear previous actors
    renderer.RemoveAllViewProps()
    
    if df is None or df.empty:
        state.status_message = "No data to display after filtering."
        return
    
    try:
        # Create points - using correct column names
        points = vtk.vtkPoints()
        for _, row in df.iterrows():
            points.InsertNextPoint(float(row['X (m)']), float(row['Y (m)']), float(row['Z (m)']))
        
        # Create polydata
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        
        # Create vertices
        vertices = vtk.vtkCellArray()
        for i in range(points.GetNumberOfPoints()):
            vertices.InsertNextCell(1, [i])
        polydata.SetVerts(vertices)
        
        # Add color data
        colors, min_val, max_val = get_color_array(df, color_mode)
        color_array = numpy_support.numpy_to_vtk(colors)
        color_array.SetName("colors")
        polydata.GetPointData().SetScalars(color_array)
        
        # Create mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)
        mapper.SetScalarRange(0, 1)
        
        # Create actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetPointSize(8)
        
        # Set color map
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(256)
        lut.SetRange(0, 1)
        
        # Different color schemes for different modes
        if color_mode == "True_Temp":
            lut.SetHueRange(0.667, 0.0)  # Blue to Red
        elif color_mode == "Pred_Temp":
            lut.SetHueRange(0.333, 0.0)  # Green to Red
        else:  # Abs_Error
            lut.SetHueRange(0.0, 0.667)  # Red to Blue
        
        lut.Build()
        mapper.SetLookupTable(lut)
        
        # Add actor to renderer
        renderer.AddActor(actor)
        
        # Add axes
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(2, 2, 2)
        axes.SetShaftTypeToCylinder()
        axes.SetCylinderRadius(0.02)
        renderer.AddActor(axes)
        
        # Add a color bar
        scalar_bar = vtk.vtkScalarBarActor()
        scalar_bar.SetLookupTable(lut)
        scalar_bar.SetTitle(f"{color_mode}\n({min_val:.2f} - {max_val:.2f})")
        scalar_bar.SetNumberOfLabels(5)
        scalar_bar.SetPosition(0.85, 0.1)
        scalar_bar.SetWidth(0.1)
        scalar_bar.SetHeight(0.8)
        renderer.AddActor(scalar_bar)
        
        # Reset camera
        renderer.ResetCamera()
        render_window.Render()
        
        state.status_message = f"Displaying {len(df)} points colored by {color_mode}"
        
    except Exception as e:
        state.status_message = f"Error creating visualization: {str(e)}"

def filter_data():
    """Filter data based on current selections"""
    if state.csv_data is None:
        return None
    
    df = state.csv_data.copy()
    
    if state.current_component_id and state.current_component_id != "All":
        df = df[df['Component ID'] == state.current_component_id]
    
    if state.current_material_id and state.current_material_id != "All":
        df = df[df['Material ID'] == state.current_material_id]
    
    return df

# -----------------------------------------------------------------------------
# State watchers
# -----------------------------------------------------------------------------

@state.change("uploaded_files")
def on_uploaded_files_change(uploaded_files, **kwargs):
    """Watch for changes in uploaded_files state and trigger file processing"""
    print(f"uploaded_files changed: {uploaded_files}")  # Debug logging
    print(f"uploaded_files type: {type(uploaded_files)}")  # Debug logging
    
    if not uploaded_files:
        return
    
    # Handle different formats that Trame might provide
    try:
        # Check if it's a list and has items
        if isinstance(uploaded_files, list) and len(uploaded_files) > 0:
            # Handle each file in the list
            for file_item in uploaded_files:
                process_single_file(file_item)
        elif uploaded_files is not None:  # Handle single file case - fixed to avoid DataFrame ambiguity
            process_single_file(uploaded_files)
    except Exception as e:
        print(f"Error in uploaded_files_change: {e}")
        state.status_message = f"Error processing uploaded file: {str(e)}"
        state.dirty("status_message")

def process_single_file(file_item):
    """Process a single uploaded file"""
    print(f"Processing file item: {file_item}")
    print(f"File item type: {type(file_item)}")
    
    try:
        content = None
        
        # Handle different file formats that Trame might provide
        if hasattr(file_item, 'read'):
            # File-like object
            content = file_item.read()
            if isinstance(content, str):
                content = content.encode('utf-8')
        elif isinstance(file_item, dict):
            # Dictionary with file info
            if 'content' in file_item:
                content = file_item['content']
            elif 'file' in file_item and hasattr(file_item['file'], 'read'):
                content = file_item['file'].read()
                if isinstance(content, str):
                    content = content.encode('utf-8')
            elif 'name' in file_item:
                # File path case
                with open(file_item['name'], 'rb') as f:
                    content = f.read()
        elif isinstance(file_item, str):
            # String content or file path
            if file_item.endswith('.csv') and os.path.exists(file_item):
                with open(file_item, 'rb') as f:
                    content = f.read()
            else:
                content = file_item.encode('utf-8')
        
        if content is None:
            state.status_message = "Could not read file content."
            state.dirty("status_message")
            return
        
        # Ensure content is bytes
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        # Save uploaded file temporarily
        temp_path = "/tmp/uploaded_data.csv"
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        print(f"File saved to: {temp_path}")  # Debug logging
        
        # Load and process the data
        result = load_csv_data(temp_path)
        print(f"Load result: {result}")  # Debug logging
        
        if len(result) == 4:  # Success case
            df, component_ids, material_ids, message = result
            state.csv_data = df
            state.available_component_ids = ["All"] + component_ids
            state.available_material_ids = ["All"] + material_ids
            state.current_component_id = "All"
            state.current_material_id = "All"
            state.data_loaded = True
            state.status_message = f"{message} - {len(df)} rows loaded."
            
            print(f"Data loaded successfully: {len(df)} rows")  # Debug logging
            
            # Update visualization
            filtered_df = filter_data()
            create_3d_points(filtered_df, state.color_mode)
            
            # Force UI update
            ctrl.view_update()
            
            state.dirty("available_component_ids", "available_material_ids", "data_loaded", "status_message")
        else:
            error_msg = result[1] if len(result) > 1 else "Unknown error"
            state.status_message = f"Error: {error_msg}"
            state.data_loaded = False
            state.dirty("status_message", "data_loaded")
            
    except Exception as e:
        state.status_message = f"Error processing file: {str(e)}"
        state.data_loaded = False
        state.dirty("status_message", "data_loaded")
        print(f"Exception in file processing: {e}")  # Debug logging

# -----------------------------------------------------------------------------
# Controller functions
# -----------------------------------------------------------------------------

@ctrl.add("on_file_change")
def on_file_change(files):
    """Handle file upload"""
    print(f"File upload triggered with files: {files}")  # Debug logging
    
    if not files or len(files) == 0:
        state.status_message = "No file selected."
        state.dirty("status_message")
        return
        
    file_info = files[0]
    print(f"File info: {file_info}")  # Debug logging
    
    # Handle different file input formats
    content = None
    if 'content' in file_info:
        content = file_info['content']
    elif 'file' in file_info and hasattr(file_info['file'], 'read'):
        content = file_info['file'].read()
    elif isinstance(file_info, dict) and 'name' in file_info:
        # Handle file path case
        try:
            with open(file_info['name'], 'rb') as f:
                content = f.read()
        except Exception as e:
            state.status_message = f"Error reading file: {str(e)}"
            state.dirty("status_message")
            return
    
    if content is None:
        state.status_message = "Could not read file content."
        state.dirty("status_message")
        return
    
    try:
        # Save uploaded file temporarily
        temp_path = "/tmp/uploaded_data.csv"
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        print(f"File saved to: {temp_path}")  # Debug logging
        
        # Load and process the data
        result = load_csv_data(temp_path)
        print(f"Load result: {result}")  # Debug logging
        
        if len(result) == 4:  # Success case
            df, component_ids, material_ids, message = result
            state.csv_data = df
            state.available_component_ids = ["All"] + component_ids
            state.available_material_ids = ["All"] + material_ids
            state.current_component_id = "All"
            state.current_material_id = "All"
            state.data_loaded = True
            state.status_message = f"{message} - {len(df)} rows loaded."
            
            print(f"Data loaded successfully: {len(df)} rows")  # Debug logging
            
            # Update visualization
            filtered_df = filter_data()
            create_3d_points(filtered_df, state.color_mode)
            
            # Force UI update
            ctrl.view_update()
            
            state.dirty("available_component_ids", "available_material_ids", "data_loaded", "status_message")
        else:
            error_msg = result[1] if len(result) > 1 else "Unknown error"
            state.status_message = f"Error: {error_msg}"
            state.data_loaded = False
            state.dirty("status_message", "data_loaded")
            
    except Exception as e:
        state.status_message = f"Error processing file: {str(e)}"
        state.data_loaded = False
        state.dirty("status_message", "data_loaded")
        print(f"Exception in file upload: {e}")  # Debug logging

@ctrl.add("on_component_change")
def on_component_change():
    """Handle component ID selection change"""
    filtered_df = filter_data()
    create_3d_points(filtered_df, state.color_mode)
    state.dirty("status_message")

@ctrl.add("on_material_change") 
def on_material_change():
    """Handle material ID selection change"""
    filtered_df = filter_data()
    create_3d_points(filtered_df, state.color_mode)
    state.dirty("status_message")

@ctrl.add("on_color_mode_change")
def on_color_mode_change():
    """Handle color mode change"""
    filtered_df = filter_data()
    create_3d_points(filtered_df, state.color_mode)
    state.dirty("status_message")

@ctrl.add("load_sample_data")
def load_sample_data():
    """Load sample data from sample_3d_data.csv"""
    sample_path = os.path.join(os.path.dirname(__file__), "sample_3d_data.csv")
    if os.path.exists(sample_path):
        result = load_csv_data(sample_path)
        if len(result) == 4:  # Success case
            df, component_ids, material_ids, message = result
            state.csv_data = df
            state.available_component_ids = ["All"] + component_ids
            state.available_material_ids = ["All"] + material_ids
            state.current_component_id = "All"
            state.current_material_id = "All"
            state.data_loaded = True
            state.status_message = f"Sample data loaded: {message}"
            
            # Update visualization
            filtered_df = filter_data()
            create_3d_points(filtered_df, state.color_mode)
            state.dirty("available_component_ids", "available_material_ids", "data_loaded", "status_message")
    else:
        state.status_message = "Sample data file not found."
        state.dirty("status_message")

# -----------------------------------------------------------------------------
# UI Layout
# -----------------------------------------------------------------------------

def create_layout():
    with SinglePageLayout(server) as layout:
        # Toolbar
        with layout.toolbar:
            v3.VToolbarTitle("CSV 3D Visualizer")
            v3.VSpacer()
            v3.VBtn("Load Sample Data", 
                   click="load_sample_data", 
                   color="primary", 
                   variant="outlined",
                   prepend_icon="mdi-database")
            
        # Main content
        with layout.content:
            with v3.VContainer(fluid=True):
                # Status message
                with v3.VRow():
                    with v3.VCol(cols=12):
                        v3.VAlert(
                            v_model=("data_loaded",),
                            type="success" if ("data_loaded",) else "info",
                            text=("status_message",),
                            style="margin-bottom: 20px;"
                        )
                
                # Controls and visualization
                with v3.VRow():
                    with v3.VCol(cols=12, md=3):
                        with v3.VCard(outlined=True, style="height: fit-content;"):
                            with v3.VCardTitle():
                                v3.VIcon("mdi-tune", style="margin-right: 8px;")
                                "Controls"
                            
                            with v3.VCardText():
                                # File upload
                                v3.VFileInput(
                                    label="Upload CSV File",
                                    accept=".csv",
                                    prepend_icon="mdi-upload",
                                    variant="outlined",
                                    density="compact",
                                    style="margin-bottom: 16px;",
                                    v_model=("uploaded_files", []),
                                    show_size=True,
                                    clearable=True,
                                    # Watch for changes in the uploaded_files state
                                    __events=["update:modelValue"]
                                )
                                
                                # Component ID dropdown
                                v3.VSelect(
                                    label="Component ID",
                                    v_model=("current_component_id",),
                                    items=("available_component_ids",),
                                    variant="outlined",
                                    density="compact",
                                    style="margin-bottom: 16px;",
                                    change="on_component_change",
                                    disabled=("!data_loaded",)
                                )
                                
                                # Material ID dropdown  
                                v3.VSelect(
                                    label="Material ID",
                                    v_model=("current_material_id",),
                                    items=("available_material_ids",), 
                                    variant="outlined",
                                    density="compact",
                                    style="margin-bottom: 16px;",
                                    change="on_material_change",
                                    disabled=("!data_loaded",)
                                )
                                
                                # Color mode selection
                                v3.VSelect(
                                    label="Color Mode",
                                    v_model=("color_mode",),
                                    items=['True_Temp', 'Pred_Temp', 'Abs_Error'],
                                    variant="outlined", 
                                    density="compact",
                                    change="on_color_mode_change",
                                    disabled=("!data_loaded",)
                                )
                    
                    # 3D Visualization
                    with v3.VCol(cols=12, md=9):
                        with v3.VCard(outlined=True, style="height: 700px;"):
                            with v3.VCardTitle():
                                v3.VIcon("mdi-cube-outline", style="margin-right: 8px;")
                                "3D Visualization"
                                v3.VSpacer()
                                v3.VChip(
                                    text=("status_message",),
                                    color="primary",
                                    size="small"
                                )
                            
                            with v3.VCardText(style="height: calc(100% - 64px); padding: 8px;"):
                                vtk_widgets.VtkRemoteView(
                                    render_window,
                                    style="height: 100%; width: 100%; border-radius: 4px;"
                                )

# -----------------------------------------------------------------------------
# Main execution
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    create_layout()
    server.start()