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

def clear_selection(obj): # Clear all selections in the mesh
    for v in obj.data.vertices: v.select = False
    for e in obj.data.edges: e.select = False
    for f in obj.data.polygons: f.select = False

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

def create_sphere(name, location, scale, radius=1.0, segments=32, rings=16):
    # Add Sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=segments, ring_count=rings)
    
    sphere = bpy.context.object
    sphere.name = name
    
    sphere.scale = (scale[0], scale[1], scale[2])
    
    return sphere

def shade_smooth(obj):
    # Make sure the object is a mesh
    if obj.type != 'MESH':
        return
        
    # Smooth polygons
    for poly in obj.data.polygons:
        poly.use_smooth = True
            
    # Update mesh data
    obj.data.update()

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

def simple_deform(obj, angle, axis='Z', mode='TWIST', limit=None):
    if obj and obj.type == 'MESH':
        # Add the Simple Deform modifier
        mod = obj.modifiers.new(name="SimpleDeform", type='SIMPLE_DEFORM')
        
        # Set the angle in radians
        mod.angle = radians(angle)
        
        # Set the deformation axis
        mod.deform_axis = axis
        
        # Set the deformation mode (Not working for now T-T)
        # mod.mode = mode
        
        # Set limits
        if limit is not None:
            mod.limits[0] = limit[0]  # Lower
            mod.limits[1] = limit[1]  # Upper
        
        return mod
    return 'Something'

def join_elements(obj, indices, mode='EDGE'):
    if not obj or obj.type != 'MESH':
        return None
    
    # Ensure that Blender is in OBJECT mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Clear all selections
    clear_selection(obj)
    
    # Switch to EDIT mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Create a BMesh instance from the active edit mesh
    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    
    # Select and join the specified elements
    if mode == 'EDGE':
        # Bridge edge loops (Ctrl+F equivalent for edges)
        selected_edges = []
        for idx in indices:
            if idx < len(bm.edges):
                bm.edges[idx].select = True
                selected_edges.append(bm.edges[idx])
        
        # Apply bridge operation
        if len(selected_edges) >= 2:
            try:
                bmesh.ops.bridge_loops(bm, edges=selected_edges)
            except Exception as e:
                print(f"Bridge operation failed: {e}")
    
    elif mode == 'VERT':
        # Join vertices (corners)
        selected_verts = []
        for idx in indices:
            if idx < len(bm.verts):
                bm.verts[idx].select = True
                selected_verts.append(bm.verts[idx])
        
        # For vertices, merge them together
        if len(selected_verts) >= 2:
            try:
                bmesh.ops.pointmerge(bm, verts=selected_verts, keep_edges=False)
            except Exception as e:
                print(f"Point merge operation failed: {e}")
    
    # Update the mesh and return to OBJECT mode
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return obj




# Apply All
def ApplyAll():
    bpy.ops.object.convert(target='MESH')

def bevel_vertices_ops(obj, vertex_indices, offset=0.5, segments=10):
    # Make sure it is OBJECT mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Clear All Selection
    clear_selection(obj)
    
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
    clear_selection(obj)
    
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

def extrude(obj, mode, index, direction, distance):
    # Ensure we are in OBJECT mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Clear all selections
    clear_selection(obj)
    
    # Selection mode
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
    
    # Set the pivot point to individual origins
    bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
    
    # Extrude the selection
    bpy.ops.mesh.extrude_context()
    
    # Move in the specified direction
    if direction == 'UP':
        bpy.ops.transform.translate(value=(0, 0, distance))
    elif direction == 'DOWN':
        bpy.ops.transform.translate(value=(0, 0, -distance))
    elif direction == 'LEFT':
        bpy.ops.transform.translate(value=(-distance, 0, 0))
    elif direction == 'RIGHT':
        bpy.ops.transform.translate(value=(distance, 0, 0))
    elif direction == 'FORWARD':
        bpy.ops.transform.translate(value=(0, distance, 0))
    elif direction == 'BACKWARD':
        bpy.ops.transform.translate(value=(0, -distance, 0))
    
    # Switch back to OBJECT mode
    bpy.ops.object.mode_set(mode='OBJECT')

def delete_poly(obj, mode, index):
    if not obj or obj.type != 'MESH':
        print("Invalid object or not a mesh.")
        return
    
    # Ensure we are in OBJECT mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Clear all selections
    clear_selection(obj)
    
    # Select the specified element based on mode and index
    if mode == 'VERT':
        if index < len(obj.data.vertices):
            obj.data.vertices[index].select = True
        else:
            print(f"Vertex index {index} out of range.")
            return
    elif mode == 'EDGE':
        if index < len(obj.data.edges):
            obj.data.edges[index].select = True
        else:
            print(f"Edge index {index} out of range.")
            return
    elif mode == 'FACE':
        if index < len(obj.data.polygons):
            obj.data.polygons[index].select = True
        else:
            print(f"Face index {index} out of range.")
            return
    else:
        print("Invalid mode. Use 'VERT', 'EDGE', or 'FACE'.")
        return
    
    # Switch to EDIT mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Delete the selected element
    bpy.ops.mesh.delete(type='VERT' if mode == 'VERT' else 'EDGE' if mode == 'EDGE' else 'FACE')
    
    # Switch back to OBJECT mode
    bpy.ops.object.mode_set(mode='OBJECT')

def apply_color(target_obj, mat_name="Color", color=(1.0, 1.0, 1.0, 1.0), metallic=0.0, roughness=0.5, emit_strength=0.0):
    
    # Create New Material
    myMat = bpy.data.materials.new(name=mat_name)
    myMat.use_nodes = True
    
    # Get Principled BSDF node
    bsdf = myMat.node_tree.nodes.get("Principled BSDF")
    
    # Set the values directly
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        
        # Emission
        emit_socket = 'Emission Color' if 'Emission Color' in bsdf.inputs else 'Emission'
        bsdf.inputs[emit_socket].default_value = color 
        
        # Emission Strength
        if 'Emission Strength' in bsdf.inputs:
            bsdf.inputs['Emission Strength'].default_value = emit_strength

    # Clear existing materials and assign the new one
    target_obj.data.materials.clear()
    target_obj.data.materials.append(myMat)
    
    return myMat

def transform(obj, location=None, rotation=None, scale=None):
    if location:
        obj.location = location
    if rotation:
        obj.rotation_euler[0] = radians(rotation[0])
        obj.rotation_euler[1] = radians(rotation[1])
        obj.rotation_euler[2] = radians(rotation[2])
    if scale:
        obj.scale = scale
    return obj


index_overlay(True)

# Camera Setup
bpy.ops.object.camera_add(location=(-40, 40, 30))
camera = bpy.context.object
camera.name = "Camera"
bpy.context.scene.camera = camera
transform(camera, rotation=(65, 0, -135))


# Base ======================================================================================
base = create_plane("Base", (0,0,1), (10,10,1))

add_solidify(base, thickness=1)
ApplyAll()

add_loop_cut(base, edge_indices=[0, 2, 4, 6], cuts=1, offset=-0.3)
add_loop_cut(base, edge_indices=[0, 12, 4, 13], cuts=1, offset=0)
add_loop_cut(base, edge_indices=[1, 18, 27, 3, 7, 25, 17, 5], cuts=1, offset=0.4)
add_loop_cut(base, edge_indices=[1, 18, 27, 35, 34, 25, 17, 5], cuts=1, offset=0)
add_loop_cut(base, edge_indices=[1, 18, 27, 35, 34, 25, 17, 5], cuts=1, offset=0)
add_loop_cut(base, edge_indices=[2, 37, 53, 69, 15, 14, 71, 55, 39, 6], cuts=1, offset=0)


# bpy.ops.object.mode_set(mode='EDIT')

extrude(base, 'FACE', 14, 'DOWN', 0.5)
extrude(base, 'FACE', 22, 'DOWN', 0.5)
extrude(base, 'FACE', 38, 'DOWN', 0.5)

delete_poly(base, 'EDGE', 52)
delete_poly(base, 'EDGE', 60)
bevel_vertices_ops(base, [0, 4, 3, 7], offset=0.2, segments=24)   
# bpy.ops.object.mode_set(mode='EDIT')
# =============================================================================================

# House 1 =====================================================================================
house_1 = create_cube("House 1", location=(-4.5,-7.5,2), scale=(1.5,1.5,1))
add_loop_cut(house_1 , edge_indices=[2, 8], cuts=1, offset=0)
grab_move(house_1, 'EDGE', 14, 'UP', 1)

# =============================================================================================

# House 2 =====================================================================================
house_2 = create_cube("House 2", location=(0,-8,2), scale=(1.5,1.5,1))
add_loop_cut(house_2 , edge_indices=[5, 11], cuts=1, offset=0)
grab_move(house_2, 'EDGE', 14, 'UP', 1)

# =============================================================================================

# House 3 =====================================================================================
house_3 = create_cube("House 3", location=(4.5,-8,2), scale=(1.5,1.5,1))
add_loop_cut(house_3 , edge_indices=[2, 8], cuts=1, offset=0)
grab_move(house_3, 'EDGE', 14, 'UP', 1)

# =============================================================================================

# House 4 =====================================================================================
house_4 = create_cube("House 4", location=(8,-1,2), scale=(1.5,2,1))
add_loop_cut(house_4 , edge_indices=[2, 8], cuts=1, offset=0)
grab_move(house_4, 'EDGE', 14, 'UP', 1)

# =============================================================================================

# House 5 =====================================================================================
house_5 = create_cube("House 5", location=(8,4,2), scale=(1.5,1.5,1))
add_loop_cut(house_5 , edge_indices=[2, 8], cuts=1, offset=0)
grab_move(house_5, 'EDGE', 14, 'UP', 1)

# =============================================================================================

# House 6 =====================================================================================
house_6 = create_cube("House 6", location=(5,8,2), scale=(1.5,1.5,1))
add_loop_cut(house_6 , edge_indices=[5, 11], cuts=1, offset=0)
grab_move(house_6, 'EDGE', 14, 'UP', 1)

# =============================================================================================

# House 7 =====================================================================================
house_7 = create_cube("House 7", location=(-4,8,2), scale=(1.5,1.5,1))
add_loop_cut(house_7 , edge_indices=[2, 8], cuts=1, offset=0)
grab_move(house_7, 'EDGE', 14, 'UP', 1)

# =============================================================================================

# Small Shrine ================================================================================
shrine_small = create_cube("Shrine Small", location=(-8.5,0,1.5), scale=(0.8,1,0.5))
add_loop_cut(shrine_small , edge_indices=[5, 11], cuts=1, offset=0)
grab_move(shrine_small, 'EDGE', 14, 'UP', 0.5)

# =============================================================================================

# Center Shrine ===============================================================================
shrine = create_cube("Shrine", location=(1.5,-1.5,2), scale=(2,2,1))
extrude(shrine, 'FACE', 5, 'UP', 6)
# =============================================================================================


# apply_color(house_1, "SimpleGreen", color=(0.0, 1.0, 0.0, 1.0), emit_strength=1.0)
# ball = create_sphere("Ball", (2,2,1), (0.5,0.5,0.5))
# shade_smooth(ball)

# plane = create_plane("Ground", (0,0,10), (20,20,1))
# transform(plane,rotation=(0,45,0))
# add_loop_cut(plane, edge_indices=[0, 2], cuts=10, offset=0)
# simple_deform(plane, angle=45, axis='Z', limit=(-0.5, 0.5))

