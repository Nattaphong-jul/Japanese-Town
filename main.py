import bpy
import os
from math import radians
import math
import bmesh
import traceback
import random

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

def create_cylinder(name, location, scale, radius=1.0, depth=2.0, vertices=32):
    # Add Cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, vertices=vertices, location=location)
    
    cylinder = bpy.context.object
    cylinder.name = name
    
    cylinder.scale = (scale[0], scale[1], scale[2])
    
    return cylinder

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
        mod = obj.modifiers.new(name="SimpleDeform", type='SIMPLE_DEFORM')
        
        mod.deform_method = mode
        mod.angle = radians(angle)
        mod.deform_axis = axis
        
        if limit is not None:
            mod.limits[0] = limit[0]
            mod.limits[1] = limit[1]
        
        return mod
    return None

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

def join_obj(name: str, objects: list):
    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')

    # Select all target mesh objects
    for obj in objects:
        if obj.type == 'MESH':
            obj.select_set(True)

    # Set the first object as active
    bpy.context.view_layer.objects.active = objects[0]

    # Join into single object
    bpy.ops.object.join()

    # Rename the result
    bpy.context.view_layer.objects.active.name = name

    return bpy.context.view_layer.objects.active

def insert_face(obj, face_index, scale=0.1):
    if not obj or obj.type != 'MESH':
        print("Invalid object or not a mesh.")
        return
    
    if face_index < 0 or face_index >= len(obj.data.polygons):
        print(f"Face index {face_index} out of range.")
        return
    
    # Ensure we are in OBJECT mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Clear all selections
    clear_selection(obj)
    
    # Select the specified face
    obj.data.polygons[face_index].select = True
    
    # Switch to EDIT mode
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Inset the face using the inset faces operator
    bpy.ops.mesh.inset(use_boundary=False, use_even_offset=True, use_relative_offset=False, use_edge_rail=False, thickness=scale, depth=0.0, use_outset=False, use_select_inset=True, use_individual=False, use_interpolate=False, release_confirm=False)
    
    # Switch back to OBJECT mode
    bpy.ops.object.mode_set(mode='OBJECT')


index_overlay(True)

# Base ======================================================================================
base = create_plane("Base", (0,0,1), (10,10,1))

add_solidify(base, thickness=1)
ApplyAll()

add_loop_cut(base, edge_indices=[0, 2, 4, 6], cuts=1, offset=-0.2)
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
apply_color(base, "BaseGreen", color=(0, 0.6, 0.5, 0), roughness=0.8)
# =============================================================================================

# Water =======================================================================================
water = create_plane("Water", location=(0,0,0.52), scale=(7,7,1))
apply_color(water, "WaterBlue", color=(0.0, 0.4, 1.0, 0.6))
# =============================================================================================

# House 1 =====================================================================================
house_1 = create_cube("House 1", location=(-4.5,-7.5,2), scale=(1.5,1.5,1))
add_loop_cut(house_1 , edge_indices=[2, 8], cuts=1, offset=0)
grab_move(house_1, 'EDGE', 14, 'UP', 1)
apply_color(house_1, "Brown", color=(0.4, 0.2, 0.1, 1), roughness=0.9)

roof_1 = create_plane("House 1 Roof", location=(-4.5, -7.5, 3), scale=(2, 2, 1))
apply_color(roof_1, "GreenRoof", color=(0.1, 0.4, 0.2, 1), roughness=0.9)
add_loop_cut(roof_1, edge_indices=[0, 2], cuts=1, offset=0)
grab_move(roof_1, 'EDGE', 6, 'UP', 1)
add_solidify(roof_1, thickness=0.35)

# =============================================================================================

# House 2 =====================================================================================
house_2 = create_cube("House 2", location=(0,-8,2), scale=(1.5,1.5,1))
add_loop_cut(house_2 , edge_indices=[5, 11], cuts=1, offset=0)
grab_move(house_2, 'EDGE', 14, 'UP', 1)
apply_color(house_2, "Brown", color=(0.4, 0.2, 0.1, 1), roughness=0.9)

roof_2 = create_plane("House 2 Roof", location=(0, -8, 3), scale=(2, 2, 1))
apply_color(roof_2, "GreenRoof", color=(0.1, 0.4, 0.2, 1), roughness=0.9)
add_loop_cut(roof_2, edge_indices=[1, 3], cuts=1, offset=0)
grab_move(roof_2, 'EDGE', 6, 'UP', 1)
add_solidify(roof_2, thickness=0.35)

# =============================================================================================

# House 3 =====================================================================================
house_3 = create_cube("House 3", location=(4.5,-8,2), scale=(1.5,1.5,1))
add_loop_cut(house_3 , edge_indices=[2, 8], cuts=1, offset=0)
grab_move(house_3, 'EDGE', 14, 'UP', 1)
apply_color(house_3, "Brown", color=(0.4, 0.2, 0.1, 1), roughness=0.9)

roof_3 = create_plane("House 3 Roof", location=(4.5, -8, 3), scale=(2, 2, 1))
apply_color(roof_3, "GreenRoof", color=(0.1, 0.4, 0.2, 1), roughness=0.9)
add_loop_cut(roof_3, edge_indices=[0, 2], cuts=1, offset=0)
grab_move(roof_3, 'EDGE', 6, 'UP', 1)
add_solidify(roof_3, thickness=0.35)

# =============================================================================================

# House 4 =====================================================================================
house_4 = create_cube("House 4", location=(8,-1,2), scale=(1.5,2,1))
add_loop_cut(house_4 , edge_indices=[2, 8], cuts=1, offset=0)
grab_move(house_4, 'EDGE', 14, 'UP', 1)
apply_color(house_4, "Brown", color=(0.4, 0.2, 0.1, 1), roughness=0.9)

roof_4 = create_plane("House 4 Roof", location=(8, -1, 3), scale=(2, 2.5, 1))
apply_color(roof_4, "GreenRoof", color=(0.1, 0.4, 0.2, 1), roughness=0.9)
add_loop_cut(roof_4, edge_indices=[0, 2], cuts=1, offset=0)
grab_move(roof_4, 'EDGE', 6, 'UP', 1)
add_solidify(roof_4, thickness=0.35)

# =============================================================================================

# House 5 =====================================================================================
house_5 = create_cube("House 5", location=(8,4,2), scale=(1.5,1.5,1))
add_loop_cut(house_5 , edge_indices=[2, 8], cuts=1, offset=0)
grab_move(house_5, 'EDGE', 14, 'UP', 1)
apply_color(house_5, "Brown", color=(0.4, 0.2, 0.1, 1), roughness=0.9)

roof_5 = create_plane("House 5 Roof", location=(8, 4, 3), scale=(2, 2, 1))
apply_color(roof_5, "GreenRoof", color=(0.1, 0.4, 0.2, 1), roughness=0.9)
add_loop_cut(roof_5, edge_indices=[0, 2], cuts=1, offset=0)
grab_move(roof_5, 'EDGE', 6, 'UP', 1)
add_solidify(roof_5, thickness=0.35)

# =============================================================================================

# House 6 =====================================================================================
house_6 = create_cube("House 6", location=(5,8,2), scale=(1.5,1.5,1))
add_loop_cut(house_6 , edge_indices=[5, 11], cuts=1, offset=0)
grab_move(house_6, 'EDGE', 14, 'UP', 1)
apply_color(house_6, "Brown", color=(0.4, 0.2, 0.1, 1), roughness=0.9)

roof_6 = create_plane("House 6 Roof", location=(5, 8, 3), scale=(2, 2, 1))
apply_color(roof_6, "GreenRoof", color=(0.1, 0.4, 0.2, 1), roughness=0.9)
add_loop_cut(roof_6, edge_indices=[1, 3], cuts=1, offset=0)
grab_move(roof_6, 'EDGE', 6, 'UP', 1)
add_solidify(roof_6, thickness=0.35)

# =============================================================================================

# House 7 =====================================================================================
house_7 = create_cube("House 7", location=(-4,8,2), scale=(1.5,1.5,1))
add_loop_cut(house_7 , edge_indices=[2, 8], cuts=1, offset=0)
grab_move(house_7, 'EDGE', 14, 'UP', 1)
apply_color(house_7, "Brown", color=(0.4, 0.2, 0.1, 1), roughness=0.9)

roof_7 = create_plane("House 7 Roof", location=(-4, 8, 3), scale=(2, 2, 1))
apply_color(roof_7, "GreenRoof", color=(0.1, 0.4, 0.2, 1), roughness=0.9)
add_loop_cut(roof_7, edge_indices=[0, 2], cuts=1, offset=0)
grab_move(roof_7, 'EDGE', 6, 'UP', 1)
add_solidify(roof_7, thickness=0.35)

# =============================================================================================

# Small Shrine ================================================================================
shrine_small = create_cube("Shrine Small", location=(-8.5,0,1.5), scale=(0.8,1,0.5))
add_loop_cut(shrine_small , edge_indices=[5, 11], cuts=1, offset=0)
grab_move(shrine_small, 'EDGE', 14, 'UP', 0.5)
apply_color(shrine_small, "Brown", color=(0.4, 0.2, 0.1, 1), roughness=0.9)

small_shrine_roof = create_plane("Shrine Small Roof", location=(-8.5, 0, 2), scale=(1.2, 1.2, 1))
apply_color(small_shrine_roof, "GreenRoof", color=(0.1, 0.4, 0.2, 1), roughness=0.9)
add_loop_cut(small_shrine_roof, edge_indices=[1, 3], cuts=1, offset=0)
grab_move(small_shrine_roof, 'EDGE', 6, 'UP', 0.5)
add_solidify(small_shrine_roof, thickness=0.2)

# =============================================================================================

# Center Shrine ===============================================================================
shrine_location = (0.56, -1.34, 1.9)
shrine = create_cube("Shrine", location=shrine_location, scale=(2,2,1))
extrude(shrine, 'FACE', 5, 'UP', 6)
simple_deform(shrine, angle=-20, axis='Z', mode='TAPER')
apply_color(shrine, "Brown", color=(0.4, 0.2, 0.1, 1), roughness=0.9)

roof_Y = 7
for i in range(3):
    shrine_roof = create_plane(f"Shrine Roof {i + 1}", location=(shrine_location[0], shrine_location[1], shrine_location[2] + roof_Y), scale=(3,3,1))
    add_solidify(shrine_roof, thickness=0.01)
    ApplyAll()
    insert_face(shrine_roof, 0, scale=0.98)
    grab_move(shrine_roof, 'FACE', 0, 'UP', 2)
    apply_color(shrine_roof, f"GreenRoof {i + 1}", color=(0.1, 0.4, 0.2, 1), roughness=0.9)
    roof_Y -= 3

# =============================================================================================

# Little Shrine ===============================================================================
shrine_little = create_cube("Shrine Little", location=(-8.4, 7, 1.5), scale=(0.5,0.6,0.5))
add_loop_cut(shrine_little , edge_indices=[5, 11], cuts=1, offset=0)
grab_move(shrine_little, 'EDGE', 14, 'UP', 0.5)
apply_color(shrine_little, "Brown", color=(0.4, 0.2, 0.1, 1), roughness=0.9)

# Tree Function ===============================================================================
def create_tree(name, location=(0, 0, 0), scale=(1, 1, 1), rotation=(0, 0, 0), leave_color=(1.0,  0.62, 0.76, 1.0), log_color=(0.25, 0.1, 0.04, 1.0)):
    # -- Trunk --
    tree_log = create_cylinder("Tree Trunk", location=(-7, 5, 2.4), scale=(0.5, 0.5, 2), radius=0.4, depth=2, vertices=20)
    add_loop_cut(tree_log, edge_indices=[2] + list(range(3, 59, 3)), cuts=6, offset=0)
    simple_deform(tree_log, angle=-60, axis='X', mode='BEND', limit=(0, 1))
    ApplyAll()
    apply_color(tree_log, "BarkBrown", color=log_color, roughness=0.9)

    # -- Leaves (Sakura Pink, Low Poly, Overlapping) --
    leaves_main  = create_sphere("Leaves Main",  location=(-7.0, 5.0, 4.0), scale=(1.3, 1.3, 1.1), radius=1.0, segments=8, rings=6)
    leaves_top   = create_sphere("Leaves Top",   location=(-7.2, 4.8, 4.9), scale=(1.0, 1.0, 0.9), radius=1.0, segments=8, rings=6)
    leaves_left  = create_sphere("Leaves Left",  location=(-8.3, 4.6, 3.7), scale=(1.0, 1.0, 0.9), radius=1.0, segments=8, rings=6)
    leaves_right = create_sphere("Leaves Right", location=(-5.8, 5.3, 3.7), scale=(1.0, 1.0, 0.9), radius=1.0, segments=8, rings=6)
    leaves_back  = create_sphere("Leaves Back",  location=(-7.0, 6.3, 3.5), scale=(1.0, 1.0, 0.8), radius=1.0, segments=8, rings=6)
    leaves_front = create_sphere("Leaves Front", location=(-7.0, 3.8, 3.5), scale=(1.0, 1.0, 0.8), radius=1.0, segments=8, rings=6)

    apply_color(leaves_main,  "SakuraPink", color=leave_color, roughness=0.8, emit_strength=2)
    apply_color(leaves_top,   "SakuraPink", color=leave_color, roughness=0.8, emit_strength=2)
    apply_color(leaves_left,  "SakuraPink", color=leave_color, roughness=0.8, emit_strength=2)
    apply_color(leaves_right, "SakuraPink", color=leave_color, roughness=0.8, emit_strength=2)
    apply_color(leaves_back,  "SakuraPink", color=leave_color, roughness=0.85, emit_strength=2)
    apply_color(leaves_front, "SakuraPink", color=leave_color, roughness=0.85, emit_strength=2)

    # -- Join everything into one object --
    tree = join_obj(name, [
        leaves_main, leaves_top,
        leaves_left, leaves_right,
        leaves_back, leaves_front,
        tree_log
    ])
    transform(tree, location=location, scale=scale, rotation=rotation)
    return tree

# Create Trees ============
create_tree("Sakura Tree 1", location=(-8.4, -4, 3.8), scale=(1, 1, 1), rotation=(-10, 0, 90))
create_tree("Sakura Tree 2", location=(-8.4, -8, 3), scale=(0.7, 0.7, 0.7), rotation=(0, -8, 90))
create_tree("Sakura Tree 3", location=(-2.82, 1.7, 3), scale=(0.7, 0.7, 0.7), rotation=(0, -10, 0))
create_tree("Sakura Tree 4", location=(-9.8, 3, 3), scale=(0.7, 0.7, 0.7), rotation=(0, -8, 0))
create_tree("Sakura Tree 5", location=(-9.4, 6, 3), scale=(0.7, 0.7, 0.7), rotation=(0, -8, 70))
create_tree("Sakura Tree 6", location=(-9.6, 9.4, 3), scale=(0.7, 0.7, 0.7), rotation=(0, -10, 10))
create_tree("Sakura Tree 7", location=(-7, 9.6, 3), scale=(0.7, 0.7, 0.7), rotation=(0, -13, -80))
create_tree("Sakura Tree 8", location=(0, 9.4, 3), scale=(0.7, 0.7, 0.7), rotation=(0, -10, -20))
create_tree("Sakura Tree 9", location=(2, 9.6, 3), scale=(0.7, 0.7, 0.7), rotation=(-10, 0, -10))
create_tree("Sakura Tree 10", location=(8.2, 9.6, 4), scale=(1, 1, 1), rotation=(-10, 0, -30))
create_tree("Sakura Tree 11", location=(3.86, 3, 2.6), scale=(0.6, 0.6, 0.6), rotation=(-10, 0, 90))
create_tree("Green Tree", location=(9.7, 7, 4), scale=(1, 1, 1), rotation=(-10, 0, -90), leave_color=(0.0, 0.4, 0.2, 1.0), log_color=(0.2, 0.1, 0.05, 1.0))
create_tree("Green Tree 2", location=(8, -8, 3.8), scale=(1, 1, 1), rotation=(-10, 0, 0), leave_color=(0.0, 0.4, 0.2, 1.0), log_color=(0.2, 0.1, 0.05, 1.0))
create_tree("Green Tree 3", location=(7, -5, 3.8), scale=(1, 1, 1), rotation=(-10, 0, 90), leave_color=(0.0, 0.4, 0.2, 1.0), log_color=(0.2, 0.1, 0.05, 1.0))
create_tree("Sakura Tree 12", location=(9.5, -6, 3), scale=(0.7, 0.7, 0.7), rotation=(-10, 0, -90))

# ============================================================================================

# Bushes =====================================================================================
def create_bush(name, location=(0, 0, 0), scale=(1, 1, 1), rotation=(0, 0, 0), color=(0.0, 0.4, 0.2, 1.0)):
    bush = create_sphere(name, location=location, scale=scale, radius=1.0, segments=8, rings=6)
    apply_color(bush, name + "Mat", color=color, roughness=0.8)
    transform(bush, location=location, scale=scale, rotation=rotation)
    return bush

# Create Bushes ===========
create_bush("Bush 1", location=(-7.1, -1.5, 1.2), rotation=(0, 0, 0), scale=(0.40, 0.74, 0.50))
create_bush("Bush 2", location=(-7.0, 0.02, 1.13), rotation=(0, 0, 0), scale=(0.40, 0.51, 0.50))
create_bush("Bush 3", location=(-7.1, 1.18, 1.06), rotation=(0, 0, 0), scale=(0.40, 0.43, 0.50))
create_bush("Bush 4", location=(-7.7, 2.42, 1.23), rotation=(0, 0, 0), scale=(0.69, 0.71, 0.69))
create_bush("Bush 5", location=(-7.1, 4.20, 1.44), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 6", location=(-8.6, 3.65, 1.03), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 7", location=(-9.6, 4.46, 1.02), rotation=(0, 0, 0), scale=(0.17, 0.19, 0.29))
create_bush("Bush 8", location=(-9.7, 3.76, 0.94), rotation=(0, 0, 0), scale=(0.17, 0.19, 0.29))
create_bush("Bush 9", location=(-9.5, 4.98, 0.93), rotation=(0, 0, 0), scale=(0.17, 0.19, 0.29))
create_bush("Bush 10", location=(-9.0, 2.37, 1.00), rotation=(-3.9, -3.2, -1.0), scale=(0.17, 0.19, 0.22))
create_bush("Bush 11", location=(-8.5, 8.65, 1.07), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 12", location=(-7.2, 7.47, 0.84), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 13", location=(-6.2, 8.34, 0.94), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.39))
create_bush("Bush 14", location=(-7.7, -8.7, 1.06), rotation=(0, 0, 0), scale=(0.69, 0.71, 0.69))
create_bush("Bush 15", location=(-1.4, 8.14, 0.84), rotation=(0, 0, 0), scale=(0.46, 0.50, 0.77))
create_bush("Bush 16", location=(-0.0, 7.74, 0.84), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.66))
create_bush("Bush 17", location=(1.38, 7.13, 1.44), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 18", location=(2.74, 8.19, 1.23), rotation=(0, 0, 0), scale=(0.69, 0.71, 0.69))
create_bush("Bush 19", location=(8.91, -3.9, 1.23), rotation=(0, 0, 0), scale=(0.69, 0.71, 0.69))
create_bush("Bush 20", location=(-0.7, 6.84, 1.2), rotation=(0, 0, -95.0), scale=(0.40, 0.74, 0.50))
create_bush("Bush 21", location=(8.84, 1.72, 1.2), rotation=(0, 0, -95.0), scale=(0.40, 0.74, 0.50))
create_bush("Bush 22", location=(2.32, -7.1, 1.01), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 23", location=(7.52, 7.65, 1.23), rotation=(0, 0, 0), scale=(0.69, 0.71, 0.69))
create_bush("Bush 24", location=(7.47, 6.17, 1.44), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 25", location=(7.51, 2.01, 1.44), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 26", location=(6.15, -6.2, 1.06), rotation=(0, 0, 0), scale=(0.40, 0.43, 0.50))
create_bush("Bush 27", location=(6.57, -7.0, 1.06), rotation=(0, 0, 0), scale=(0.40, 0.43, 0.50))
create_bush("Bush 28", location=(9.77, 0.83, 1.00), rotation=(-3.9, -3.2, -1.0), scale=(0.17, 0.19, 0.22))
create_bush("Bush 29", location=(9.73, -0.4, 1.00), rotation=(-3.9, -3.2, -1.0), scale=(0.17, 0.19, 0.22))
create_bush("Bush 30", location=(-9.6, 1.41, 1.00), rotation=(-3.9, -3.2, -1.0), scale=(0.17, 0.19, 0.22))
create_bush("Bush 31", location=(-8.7, 1.50, 1.00), rotation=(-3.9, -3.2, -1.0), scale=(0.17, 0.19, 0.22))
create_bush("Bush 32", location=(-5.2, -9.5, 1.44), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 33", location=(-2.2, -9.5, 1.44), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 34", location=(-2.5, -9.0, 1.44), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 35", location=(-1.9, -7.9, 1.44), rotation=(0, 0, 0), scale=(0.39, 0.43, 0.65))
create_bush("Bush 36", location=(9.75, 0.20, 1.00), rotation=(-3.9, -3.2, -1.0), scale=(0.17, 0.19, 0.22))

# ============================================================================================

# Floor Tiles ================================================================================
def create_floor_tile(name, location=(0, 0, 0), scale=(1, 1, 1), rotation=(0, 0, 0), color=(0.5, 0.5, 0.5, 1.0)):
    tile = create_cube(name, location=location, scale=scale)
    apply_color(tile, name + "Mat", color=color, roughness=0.8)
    transform(tile, location=location, scale=scale, rotation=rotation)
    return tile

# Create Floor Tiles ============
START_X = -6.2
STEP_X = 0.6       
Z_VAL = 0.97       
SCALE = (0.20, 0.20, 0.05)
DARK_GREY = (0.15, 0.15, 0.15, 1.0)
NUM_TILES = 21
START_Y = -5.6
tile_index = 1

# Line 1
for i in range(NUM_TILES):
    current_x = START_X + (i * STEP_X)
    randomized_y = START_Y + random.uniform(-0.1, 0.1)
    randomized_rot_z = random.uniform(-5.0, 5.0)
    
    create_floor_tile(
        name=f"FloorTile_{tile_index}",
        location=(current_x, randomized_y, Z_VAL),
        scale=SCALE,
        rotation=(0, 0, randomized_rot_z),
        color=DARK_GREY
    )
    tile_index += 1

# Line 2
for i in range(NUM_TILES):
    current_x = START_X + (i * STEP_X)
    randomized_y = START_Y + 0.6 + random.uniform(-0.1, 0.1)
    randomized_rot_z = random.uniform(-5.0, 5.0)
    
    create_floor_tile(
        name=f"FloorTile_{tile_index}",
        location=(current_x, randomized_y, Z_VAL),
        scale=SCALE,
        rotation=(0, 0, randomized_rot_z),
        color=DARK_GREY
    )
    tile_index += 1

# Line 3
for i in range(NUM_TILES):
    current_x = START_X + (i * STEP_X)
    randomized_y = START_Y + 1.2 + random.uniform(-0.1, 0.1)
    randomized_rot_z = random.uniform(-5.0, 5.0)
    
    create_floor_tile(
        name=f"FloorTile_{tile_index}",
        location=(current_x, randomized_y, Z_VAL),
        scale=SCALE,
        rotation=(0, 0, randomized_rot_z),
        color=DARK_GREY
    )
    tile_index += 1

# Side 2 ===========
START_Y = -3.81
END_Y = 5.993
NUM_TILES = 17
STEP_Y = (END_Y - START_Y) / (NUM_TILES - 1)

# Starting X positions
BASE_X_1 = 4.638
BASE_X_3 = 6.049
BASE_X_2 = (BASE_X_1 + BASE_X_3) / 2.0

BASE_Z = 0.970
BASE_ROT_Z = -2.34
SCALE = (0.20, 0.20, 0.05)
DARK_GREY = (0.15, 0.15, 0.15, 1.0)

tile_index = 1

# Line 1
for i in range(NUM_TILES):
    current_y = START_Y + (i * STEP_Y)
    randomized_x = BASE_X_1 + random.uniform(-0.1, 0.1)
    randomized_rot_z = BASE_ROT_Z + random.uniform(-5.0, 5.0)
    
    create_floor_tile(
        name=f"Y_FloorTile_{tile_index}",
        location=(randomized_x, current_y, BASE_Z),
        scale=SCALE,
        rotation=(0, 0, randomized_rot_z),
        color=DARK_GREY
    )
    tile_index += 1

# Line 2
for i in range(NUM_TILES):
    current_y = START_Y + (i * STEP_Y)
    randomized_x = BASE_X_2 + random.uniform(-0.1, 0.1)
    randomized_rot_z = BASE_ROT_Z + random.uniform(-5.0, 5.0)
    
    create_floor_tile(
        name=f"Y_FloorTile_{tile_index}",
        location=(randomized_x, current_y, BASE_Z),
        scale=SCALE,
        rotation=(0, 0, randomized_rot_z),
        color=DARK_GREY
    )
    tile_index += 1

# Line 3
for i in range(NUM_TILES):
    current_y = START_Y + (i * STEP_Y)
    randomized_x = BASE_X_3 + random.uniform(-0.1, 0.1)
    randomized_rot_z = BASE_ROT_Z + random.uniform(-5.0, 5.0)
    current_z = BASE_Z + (0.03 * (i / (NUM_TILES - 1))) 
    
    create_floor_tile(
        name=f"Y_FloorTile_{tile_index}",
        location=(randomized_x, current_y, current_z),
        scale=SCALE,
        rotation=(0, 0, randomized_rot_z),
        color=DARK_GREY
    )
    tile_index += 1
# ============================================================================================

# Lighting Setup =============================================================================
def add_light(name, type, location=(0, 0, 0), rotation=(0, 0, 0), energy=1000, color=(1.0, 1.0, 1.0), angle=180):
    type = type.upper()
    if type not in ('POINT', 'AREA'):
        print(f"[add_light] Unsupported light type '{type}'. Use 'POINT' or 'AREA'.")
        return None
 
    # Create the light data block
    light_data = bpy.data.lights.new(name=name + "_data", type=type)
    light_data.energy = energy
    light_data.color = (color[0], color[1], color[2])
 
    # Area-light-specific: spread angle
    if type == 'AREA':
        light_data.spread = radians(angle)
 
    # Create the object and link it to the scene
    light_obj = bpy.data.objects.new(name=name, object_data=light_data)
    bpy.context.collection.objects.link(light_obj)
 
    # Set transform
    light_obj.location = location
    light_obj.rotation_euler = (radians(rotation[0]), radians(rotation[1]), radians(rotation[2]))
 
    return light_obj

# Adding Lights
add_light("area_light_1", type='AREA', location=(13.96, 2.416, 9.585), rotation=(-21.1, 48.0, -6.33), energy=1077.400, color=(0.20, 0.30, 0.65), angle=180)
add_light("area_light_2", type='AREA', location=(-7.79, 0.016, 12.32), rotation=(-5.10, -35.4, -1.75), energy=1077.400, color=(0.20, 0.30, 0.65), angle=180)
add_light("area_light_3", type='AREA', location=(0.992, 17.10, 8.050), rotation=(-65.3, 2.549, -3.33), energy=2233.100, color=(0.65, 0.70, 0.90), angle=180)
add_light("area_light_4", type='AREA', location=(0.884, -12.9, 15.06), rotation=(48.96, -6.03, -6.09), energy=1077.400, color=(0.35, 0.25, 0.65), angle=180)

# Point lights
pointlight_color = (0.45, 0.85, 0.95)
pointlight_energy = 324

add_light("point_light_1", type='POINT', location=(-3.62, -5.14, 2.662), rotation=(0, 0, 0), energy=pointlight_energy, color=pointlight_color)
add_light("point_light_2", type='POINT', location=(3.872, -5.14, 2.662), rotation=(0, 0, 0), energy=pointlight_energy, color=pointlight_color)
add_light("point_light_3", type='POINT', location=(3.872, 0.445, 2.662), rotation=(0, 0, 0), energy=pointlight_energy, color=pointlight_color)
add_light("point_light_4", type='POINT', location=(3.872, 4.597, 2.662), rotation=(0, 0, 0), energy=pointlight_energy, color=pointlight_color)
add_light("point_light_5", type='POINT', location=(-7.41, -5.71, 2.275), rotation=(0, 0, 0), energy=pointlight_energy, color=pointlight_color)
add_light("point_light_6", type='POINT', location=(-7.93, 4.597, 2.662), rotation=(0, 0, 0), energy=pointlight_energy, color=pointlight_color)
# =============================================================================================

# Camera Setup
bpy.ops.object.camera_add(location=(-40, 40, 30))
camera = bpy.context.object
camera.name = "Camera"
bpy.context.scene.camera = camera
transform(camera, rotation=(65, 0, -135))