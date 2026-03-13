import bpy
import os
from math import radians
import math
import bmesh

# Reset to Object Mode
if bpy.ops.object.mode_set.poll():
    bpy.ops.object.mode_set(mode='OBJECT')

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

def create_cube(name, location, scale):
    # Add Cube
    bpy.ops.mesh.primitive_cube_add(location=location)
    
    cube = bpy.context.object
    cube.name = name
    
    cube.scale = (scale[0], scale[1], scale[2])
    
    return cube

def create_triangle(name, location, scale):
    # Create a new mesh and object
    mesh = bpy.data.meshes.new("TriangleMesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    # Create bmesh and add vertices
    bm = bmesh.new()
    v0 = bm.verts.new((0, 0, 0))
    v1 = bm.verts.new((scale[0], 0, 0))
    v2 = bm.verts.new((scale[0]/2, scale[1], 0))
    
    # Create face
    bm.faces.new([v0, v1, v2])
    
    # Update mesh
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    # Set location and scale
    obj.location = location
    obj.scale = scale
    
    return obj

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

def add_loop_cut(obj, edge_indices, cuts=1, offset=0.0):
    # Make sure we are in EDIT mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Create a BMesh instance from the active edit mesh
    bm = bmesh.from_edit_mesh(obj.data)
    
    # Ensure the internal index table is updated so we can access edges by index
    bm.edges.ensure_lookup_table()
    
    # Collect the edges we want to cut across
    try:
        edges_to_cut = [bm.edges[i] for i in edge_indices]
    except IndexError:
        print("Error: One or more edge indices are out of range.")
        bpy.ops.object.mode_set(mode='OBJECT')
        return
        
    # --- Store edge vectors and midpoints before cutting ---
    edge_data = []
    reference_vector = None # We will use this to align all other vectors
    
    if offset != 0.0 and cuts == 1:
        for e in edges_to_cut:
            v1, v2 = e.verts
            vec = v2.co - v1.co
            
            # FIXED: Make sure all slide vectors point in the same direction!
            if reference_vector is None:
                reference_vector = vec # Set the first edge as the master direction
            elif vec.dot(reference_vector) < 0:
                vec = -vec # If this edge points the opposite way, flip it
                
            edge_data.append({
                "midpoint": (v1.co + v2.co) / 2.0,
                "vector": vec
            })
    
    # Perform the loop cut (subdivide the edge ring)
    bmesh.ops.subdivide_edgering(
        bm,
        edges=edges_to_cut,
        cuts=cuts,
        profile_shape='LINEAR',
        profile_shape_factor=0.0
    )
    
    # --- Find the new vertices at the midpoints and slide them ---
    if offset != 0.0 and cuts == 1:
        offset = max(-1.0, min(1.0, offset)) # Keep offset between -1 and 1
        
        # Scan all vertices in the mesh
        for v in bm.verts:
            for data in edge_data:
                # If a vertex is exactly where the old midpoint was, it's our new cut!
                if (v.co - data["midpoint"]).length < 0.001:
                    v.co += data["vector"] * (offset / 2.0)
                    break
    
    # Update the mesh and return to OBJECT mode
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

def grab_move(obj, mode, index, direction, distance):
    # Ensure we are in OBJECT mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Clear all selections
    for v in obj.data.vertices: v.select = False
    for e in obj.data.edges: e.select = False
    for f in obj.data.polygons: f.select = False
    
    # Select the specified element based on mode and index
    if mode == 'VERT':
        obj.data.vertices[index].select = True
    elif mode == 'EDGE':
        obj.data.edges[index].select = True
    elif mode == 'FACE':
        obj.data.polygons[index].select = True
    else:
        print("Invalid mode. Use 'VERT', 'EDGE', or 'FACE'.")
        return
    
    # Switch to EDIT mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Set the pivot point to individual origins for better control I guess
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    
    # Move the selected element in the specified direction
    if direction == 'UP':
        bpy.ops.transform.translate(value=(0, 0, distance))
    elif direction == 'DOWN':
        bpy.ops.transform.translate(value=(0, 0, -distance))
    elif direction == 'LEFT':
        bpy.ops.transform.translate(value=(-distance, 0, 0))
    elif direction == 'RIGHT':
        bpy.ops.transform.translate(value=(distance, 0, 0))
    
    # Switch back to OBJECT mode
    bpy.ops.object.mode_set(mode='OBJECT')


index_overlay(True)

base = create_plane("Base", (0,0,0), (10,10,1))

add_solidify(base, thickness=1)
ApplyAll()

add_loop_cut(base, edge_indices=[0, 2, 4, 6], cuts=1, offset=0.2)
add_loop_cut(base, edge_indices=[0, 12, 4, 13], cuts=1, offset=0.2)

bevel_vertices_ops(base, [0, 4, 3, 7], offset=0.2, segments=24)

house_body = create_cube("House Body", (-1,1,1), (1.5,1.5,1))
# tri = create_triangle("Roof", (-1,1,2.5), (1.5,1.5,1))

add_loop_cut(house_body , edge_indices=[11, 5], cuts=1, offset=0)

grab_move(house_body, 'EDGE', 14, 'UP', 1)