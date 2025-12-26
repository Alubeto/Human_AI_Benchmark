import bpy
import math
import random
from mathutils import Matrix, Vector
import sys
import os  # Added for directory handling

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
collection_name = "ImportedMeshes"
rotation_increment = math.radians(15)  # 15 degrees per step
loop = 7  # Number of random rotations to perform

# Paths
filepath_name = '/Users/albert' 
relative_path = '03211117/87882e55a8914e78a3cb15c59bd3ecf2'
obj_path = f'{filepath_name}/.cache/huggingface/hub/datasets--ShapeNet--ShapeNetCore/blobs/{relative_path}/models/model_normalized.obj'

# DYNAMIC OUTPUT PATH SETUP
# This sets the output to: [Current Terminal Directory]/test
current_dir = os.getcwd()
output_path = os.path.join(current_dir, "test")

# Create the directory if it doesn't exist
os.makedirs(output_path, exist_ok=True)

print(f"Loading OBJ file from: {obj_path}")
print(f"Saving renders to: {output_path}")

# -----------------------------------------------------------------------------
# UTILITY FUNCTIONS
# -----------------------------------------------------------------------------

def clear_scene():
    """Removes existing imported collection and clears the scene."""
    collection = bpy.data.collections.get(collection_name)
    if collection:
        for obj in collection.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
    
    # Select all and delete (clears default cube, lights, etc.)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def recalculate_normals(obj):
    """Fixes normal orientation for meshes."""
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')

def get_collection_center(collection):
    """Calculates the center of mass of all meshes in a collection."""
    total_center = Vector((0, 0, 0))
    total_vertices = 0
    
    for obj in collection.objects:
        if obj.type == 'MESH':
            world_matrix = obj.matrix_world
            for v in obj.data.vertices:
                world_v = world_matrix @ v.co
                total_center += world_v
                total_vertices += 1
    
    if total_vertices > 0:
        return total_center / total_vertices
    return Vector((0, 0, 0))

def rotate_around_origin(obj, axis_name, angle_radians):
    """
    Rotates an object around the World Origin (0,0,0) accumulating the rotation.
    This works perfectly if the object has been centered at (0,0,0).
    """
    axis_map = {
        'X': Vector((1, 0, 0)),
        'Y': Vector((0, 1, 0)),
        'Z': Vector((0, 0, 1))
    }
    rotation_axis = axis_map[axis_name]
    
    # Create rotation matrix
    rot_matrix = Matrix.Rotation(angle_radians, 4, rotation_axis)
    
    # Apply rotation: New = Rotation @ Old
    obj.matrix_world = rot_matrix @ obj.matrix_world

# -----------------------------------------------------------------------------
# MAIN EXECUTION
# -----------------------------------------------------------------------------

# 1. Setup Scene
clear_scene()

# 2. Import OBJ
bpy.ops.wm.obj_import(
    filepath=bpy.path.abspath(obj_path),
    use_split_objects=True,
    use_split_groups=True,
    validate_meshes=False
)

# 3. Organize Collection
new_collection = bpy.data.collections.new(collection_name)
bpy.context.scene.collection.children.link(new_collection)
for obj in bpy.data.objects:
    if obj.users_collection: # Unlink from default collections
        for c in obj.users_collection:
            c.objects.unlink(obj)
    new_collection.objects.link(obj)

# 4. Fix Normals & Calculate Center
for obj in new_collection.objects:
    if obj.type == 'MESH':
        recalculate_normals(obj)

# Calculate where the object currently is
current_mass_center = get_collection_center(new_collection)
print(f"Original Center of Mass: {current_mass_center}")

# 5. CENTER TO WORLD ORIGIN (The 'Justification' Step)
# We move all objects by the inverse of their mass center.
offset_vector = -current_mass_center
for obj in new_collection.objects:
    obj.matrix_world = Matrix.Translation(offset_vector) @ obj.matrix_world

# Now the "Mass Center" is effectively (0,0,0)
world_origin = Vector((0, 0, 0))

# 6. Create Control Empty at Origin
bpy.ops.object.empty_add(type='PLAIN_AXES', location=world_origin)
parent_empty = bpy.context.object
parent_empty.name = "WorldRotationPivot"

# Parent objects to this empty
for obj in new_collection.objects:
    obj.parent = parent_empty

# 7. Rendering Setup (Workbench)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1080
scene.render.resolution_y = 1080
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.background_type = 'WORLD'
scene.display.shading.show_backface_culling = True
scene.render.film_transparent = True

# 8. Camera Setup (Looking at 0,0,0)
if not any(o for o in scene.objects if o.type == 'CAMERA'):
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    scene.camera = camera

# Position camera
camera_distance = 3.0
camera.location = world_origin + Vector((0, -camera_distance, 0))
camera.rotation_euler = (math.radians(90), 0, 0) # Face forward

# Track the World Origin
bpy.ops.object.empty_add(type='PLAIN_AXES', location=world_origin)
target_empty = bpy.context.object
target_empty.name = "CameraTarget"

track = camera.constraints.new(type='TRACK_TO')
track.target = target_empty
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

# -----------------------------------------------------------------------------
# RENDER LOOP
# -----------------------------------------------------------------------------

rotation_order_str = "base"

# Initial render (Canonical View)
scene.render.filepath = os.path.join(output_path, f"sample_{rotation_order_str}.png")
bpy.ops.render.render(write_still=True)
print(f"Rendered base view")

# Perform Incremental Rotations
for i in range(1, loop):
    # Select random axis and direction
    axis = random.choice(['X', 'Y', 'Z'])
    direction = random.choice([-1, 1])
    angle = direction * rotation_increment

    # Update naming
    rot_symbol = f"{'-' if direction == -1 else ''}{axis}"
    rotation_order_str += f"_{rot_symbol}"

    # Apply rotation to the PARENT EMPTY
    # Since the empty is at (0,0,0) and holds the object, this rotates the object around its center.
    rotate_around_origin(parent_empty, axis, angle)

    # Render
    scene.render.filepath = os.path.join(output_path, f"sample_{rotation_order_str}.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered step {i}: {rotation_order_str}")

print("Rendering complete!")
