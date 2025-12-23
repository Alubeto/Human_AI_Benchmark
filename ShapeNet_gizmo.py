import bpy
import math
import random
from mathutils import Matrix, Vector, Euler
import os

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
collection_name = "ImportedMeshes"
rotation_increment = math.radians(45)
loop = 7

# Paths
filepath_name = '/Users/albert'
#relative_path = '02747177/60b743e913182e9ad5067eac75a07f7'
# relative_path = '03325088/28568aa9e333a421c36fb70296e45483'
# relative_path = '03636649/b474613907b293682f8b82e61bb347fa'
relative_path = '03325088/a851047aeb3793403ca0c4be71e7b721'
obj_path = f'{filepath_name}/.cache/huggingface/hub/datasets--ShapeNet--ShapeNetCore/blobs/{relative_path}/models/model_normalized.obj'

current_dir = os.getcwd()
output_path = os.path.join(current_dir, "test","3")
os.makedirs(output_path, exist_ok=True)

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def clear_scene():
    """Clears everything: Meshes, Lights, Cameras."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Purge orphan data
    for block in bpy.data.meshes: bpy.data.meshes.remove(block)
    for block in bpy.data.materials: bpy.data.materials.remove(block)
    for block in bpy.data.textures: bpy.data.textures.remove(block)
    for block in bpy.data.images: bpy.data.images.remove(block)

def create_color_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = False
    mat.diffuse_color = color
    return mat

def create_visual_aids(scale=1.0):
    """Creates renderable Axes (RGB) and a Center Sphere (Yellow)."""
    
    # Materials
    mat_x = create_color_material("Mat_Axis_X", (1.0, 0.0, 0.0, 1.0)) # Red
    mat_y = create_color_material("Mat_Axis_Y", (0.0, 1.0, 0.0, 1.0)) # Green
    mat_z = create_color_material("Mat_Axis_Z", (0.0, 0.0, 1.0, 1.0)) # Blue
    mat_center = create_color_material("Mat_Center", (1.0, 1.0, 0.0, 1.0)) # Yellow

    radius = 0.001 * scale
    length = 1.0 * scale # Long enough to go THROUGH (-1 to +1)
    
    # 1. Center Sphere
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius*3, location=(0,0,0))
    center_sphere = bpy.context.object
    center_sphere.name = "Visual_Center"
    center_sphere.active_material = mat_center
    center_sphere.show_in_front = True # <--- X-RAY EFFECT

    # 2. X Axis (Red)
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, location=(0, 0, 0))
    x_axis = bpy.context.object
    x_axis.rotation_euler = (0, math.radians(90), 0)
    x_axis.active_material = mat_x

    # 3. Y Axis (Green)
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, location=(0, 0, 0))
    y_axis = bpy.context.object
    y_axis.rotation_euler = (math.radians(90), 0, 0)
    y_axis.active_material = mat_y

    # 4. Z Axis (Blue)
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, location=(0, 0, 0))
    z_axis = bpy.context.object
    z_axis.active_material = mat_z

    # Group Axes
    bpy.ops.object.select_all(action='DESELECT')
    x_axis.select_set(True)
    y_axis.select_set(True)
    z_axis.select_set(True)
    bpy.context.view_layer.objects.active = x_axis
    bpy.ops.object.join()
    x_axis.name = "Visual_Axes"
    
    # Enable X-Ray ("In Front") for the joined axes
    x_axis.show_in_front = True
    
    return center_sphere, x_axis

def get_collection_center(objects):
    """Calculates the center of mass (Average of all Vertices)."""
    total_center = Vector((0, 0, 0))
    total_vertices = 0
    
    for obj in objects:
        if obj.type == 'MESH':
            world_matrix = obj.matrix_world
            for v in obj.data.vertices:
                world_v = world_matrix @ v.co
                total_center += world_v
                total_vertices += 1
    
    if total_vertices > 0:
        return total_center / total_vertices
    return Vector((0, 0, 0))

# -----------------------------------------------------------------------------
# MAIN EXECUTION
# -----------------------------------------------------------------------------

clear_scene()

# 1. Create Visuals (Gizmo)
print("Creating Visual Aids...")
center_sphere, axes_obj = create_visual_aids(scale=1.5)

# 2. Import
print(f"Loading OBJ: {obj_path}")
bpy.ops.wm.obj_import(
    filepath=bpy.path.abspath(obj_path),
    use_split_objects=True,
    use_split_groups=True,
    validate_meshes=False
)

visual_names = [center_sphere.name, axes_obj.name]
imported_objects = [o for o in bpy.context.selected_objects if o.type == 'MESH' and o.name not in visual_names]

# 3. Organize Collection
new_collection = bpy.data.collections.new(collection_name)
bpy.context.scene.collection.children.link(new_collection)
for obj in imported_objects:
    if obj.users_collection:
        for c in obj.users_collection:
            c.objects.unlink(obj)
    new_collection.objects.link(obj)

# 4. CENTER ONLY (No Flip)
print("Normalizing Object Position...")
c1 = get_collection_center(imported_objects)
for obj in imported_objects:
    obj.matrix_world = Matrix.Translation(-c1) @ obj.matrix_world

print("Object Centered.")

# 5. PARENTING
world_origin = Vector((0, 0, 0))
bpy.ops.object.empty_add(type='PLAIN_AXES', location=world_origin)
parent_empty = bpy.context.object
parent_empty.name = "RotationPivot"

# Parent the OBJECTS to the empty
for obj in imported_objects:
    obj.parent = parent_empty

# Parent the GIZMO to the empty (It now rotates WITH the object)
axes_obj.parent = parent_empty

# 6. CAMERA SETUP (Strictly -Y)
bpy.ops.object.camera_add()
camera = bpy.context.object
scene = bpy.context.scene
scene.camera = camera
camera.location = Vector((0, -3.0, 0))
camera.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ')

# 7. RENDER SETTINGS
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1080
scene.render.resolution_y = 1080
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_backface_culling = False
scene.render.film_transparent = True

# -----------------------------------------------------------------------------
# RENDER LOOP
# -----------------------------------------------------------------------------
rotation_order_str = "base"

scene.render.filepath = os.path.join(output_path, f"{rotation_order_str}.png")
bpy.ops.render.render(write_still=True)
print(f"Rendered: {rotation_order_str}")

def rotate_pivot_locally(angle_rad, axis_name):
    """
    Rotates the Pivot (and thus the Object + Axes) around its OWN current local axis.
    """
    axis_map = {
        'X': Vector((1, 0, 0)),
        'Y': Vector((0, 1, 0)),
        'Z': Vector((0, 0, 1))
    }
    vec = axis_map[axis_name]
    rot_mat = Matrix.Rotation(angle_rad, 4, vec)
    
    # Local Rotation: Old @ Rotation
    parent_empty.matrix_world = parent_empty.matrix_world @ rot_mat
    
    # Force Pivot back to 0,0,0 (Keep center constant)
    parent_empty.location = Vector((0,0,0))

for i in range(1, loop):
    axis = random.choice(['X', 'Y', 'Z'])
    direction = random.choice([-1, 1])
    angle = direction * rotation_increment

    rot_symbol = f"{'-' if direction == -1 else ''}{axis}"
    rotation_order_str += f"_{rot_symbol}"

    rotate_pivot_locally(angle, axis)
    
    scene.render.filepath = os.path.join(output_path, f"{rotation_order_str}.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered step {i}: {rotation_order_str}")

print("Complete.")
