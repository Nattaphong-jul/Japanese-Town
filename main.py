import bpy
import os
from math import radians
import math

# Delete all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

print_loc = 0
def printout(text_content, name = 'text'):
    global print_loc
    text_content = str(text_content)
    bpy.ops.object.text_add(location=(0,0,print_loc))
    text = bpy.context.object
    text.data.body = text_content
    text.rotation_euler[0] = radians(90)
    print_loc -= 1
    return text

# Show vertex index
def index_overlay(b: bool = True):
    bpy.context.preferences.view.show_developer_ui = True

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.overlay.show_extra_indices = b
    return b

def create_plane(name, location, scale):
    # Add Plain
    bpy.ops.mesh.primitive_plane_add(location=location)
    
    plane = bpy.context.object
    plane.name = name
    
    plane.scale = (scale[0], scale[1], 1)
    
    return plane

def add_solidify(obj, thickness=0.5):
    """Adds a Solidify modifier to the given object."""
    if obj and obj.type == 'MESH':
        # Add the modifier
        mod = obj.modifiers.new(name="MySolidify", type='SOLIDIFY')
        
        # Set the thickness
        mod.thickness = thickness
        
        # Offset
        mod.offset = -1 
        return mod
    return None

# Apply All
def ApplyAll():
    bpy.ops.object.convert(target='MESH')

def bevel_vertices_ops(obj, vertex_indices, offset=0.5, segments=10):
    # Make sure it is OBJECT mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Clear All Selection
    for v in obj.data.vertices: v.select = False
    for e in obj.data.edges: e.select = False
    for f in obj.data.polygons: f.select = False
    
    # Select all assigned edges
    for idx in vertex_indices:
        obj.data.vertices[idx].select = True
        
    # Change to EDIT Mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Ensure Blender is in Vertex Selection Mode
    bpy.ops.mesh.select_mode(type='VERT')
    
    # Bevel Edge
    bpy.ops.mesh.bevel(
        offset=offset, 
        segments=segments, 
        affect='EDGES'
    )
    
    # Switch back to OBJECT Mode
    bpy.ops.object.mode_set(mode='OBJECT')



index_overlay(True)


base = create_plane("Base", (0,0,0), (10,10,1))

add_solidify(base, thickness=1)
ApplyAll()

bevel_vertices_ops(base, [0, 4, 3, 7], offset=0.2, segments=24)

