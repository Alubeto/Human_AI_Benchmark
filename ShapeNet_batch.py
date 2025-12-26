import bpy
import math
import random
from mathutils import Matrix, Vector, Euler
import os
import sys

# -----------------------------------------------------------------------------
# GLOBAL CONFIGURATION
# -----------------------------------------------------------------------------
INPUT_FILE_NAME = "directory.txt"

# Base directory for output
BASE_OUTPUT_DIR = "/Users/albert/Documents/GitHub/Human_AI_Benchmark/ShapeNet"

# Your specific root path setup
FILEPATH_NAME = '/Users/albert'

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def clear_scene():
    """Clears everything: Meshes, Lights, Cameras."""
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Purge orphan data
    for block in bpy.data.meshes: bpy.data.meshes.remove(block)
    for block in bpy.data.materials: bpy.data.materials.remove(block)
    for block in bpy.data.textures: bpy.data.textures.remove(block)
    for block in bpy.data.images: bpy.data.images.remove(block)

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

def rotate_via_unparent_reset(pivot_obj, child_objects, angle_rad, axis_name):
    """
    ROBUST ROTATION LOGIC:
    1. Rotate Pivot (Children follow).
    2. Clear Parent (Keep Transform) -> Children stay visually rotated.
    3. Reset Pivot to 0,0,0 -> Pivot axes re-align with World.
    4. Set Parent (Keep Transform) -> Children re-attach to clean Pivot.
    """
    # A. Rotate Pivot
    # Since pivot is reset to 0,0,0 every time, Local Rotation == Global Rotation
    axis_map = {'X': Vector((1, 0, 0)), 'Y': Vector((0, 1, 0)), 'Z': Vector((0, 0, 1))}
    vec = axis_map[axis_name]
    rot_mat = Matrix.Rotation(angle_rad, 4, vec)
    pivot_obj.matrix_world = pivot_obj.matrix_world @ rot_mat
    
    # Force update
    bpy.context.view_layer.update()
    
    # B. Unparent Children (Keep Transform)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in child_objects:
        obj.select_set(True)
    
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        
    # C. Reset Pivot Coordinate System (Aligns axes to World)
    pivot_obj.rotation_euler = (0, 0, 0)
    pivot_obj.location = (0, 0, 0)
    bpy.context.view_layer.update()
    
    # D. Reparent Children (Keep Transform)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in child_objects:
        obj.select_set(True)
    
    pivot_obj.select_set(True)
    bpy.context.view_layer.objects.active = pivot_obj
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

# -----------------------------------------------------------------------------
# RENDER LOGIC
# -----------------------------------------------------------------------------
def process_model(full_obj_path, target_output_path, model_id_str, rotation_degree):
    loop = 7
    collection_name = "ImportedMeshes"
    rotation_increment = math.radians(rotation_degree)

    clear_scene()

    # 1. Import
    if not os.path.exists(full_obj_path):
        print(f"❌ Error: Model file not found at {full_obj_path}")
        return

    try:
        bpy.ops.wm.obj_import(
            filepath=full_obj_path,
            use_split_objects=True,
            use_split_groups=True,
            validate_meshes=False
        )
    except Exception as e:
        print(f"❌ Import Failed: {e}")
        return

    imported_objects = [o for o in bpy.context.selected_objects if o.type == 'MESH']
    
    if not imported_objects:
        print("❌ Warning: No meshes found in OBJ.")
        return

    # 2. Organize Collection
    new_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(new_collection)
    for obj in imported_objects:
        if obj.users_collection:
            for c in obj.users_collection:
                c.objects.unlink(obj)
        new_collection.objects.link(obj)

    # 3. Center Object
    c1 = get_collection_center(imported_objects)
    for obj in imported_objects:
        obj.matrix_world = Matrix.Translation(-c1) @ obj.matrix_world

    # 4. Parenting
    world_origin = Vector((0, 0, 0))
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=world_origin)
    parent_empty = bpy.context.object
    parent_empty.name = "RotationPivot"

    # Initial Parent Set (Robust)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported_objects:
        obj.select_set(True)
    parent_empty.select_set(True)
    bpy.context.view_layer.objects.active = parent_empty
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

    # 5. Camera
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    scene = bpy.context.scene
    scene.camera = camera
    camera.location = Vector((0, -3.0, 0))
    camera.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ')

    # 6. Render Settings
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_backface_culling = False
    scene.render.film_transparent = True

    # 7. Random Seed
    try:
        model_id_int = int(model_id_str[-6:], 16)
    except:
        model_id_int = 12345
    
    seed_val = model_id_int + int(rotation_degree)
    random.seed(seed_val)

    # 8. Render Loop
    rotation_order_str = "base"

    scene.render.filepath = os.path.join(target_output_path, f"{rotation_order_str}.png")
    bpy.ops.render.render(write_still=True)
    
    for i in range(1, loop):
        axis = random.choice(['X', 'Y', 'Z'])
        direction = random.choice([-1, 1])
        angle = direction * rotation_increment

        rot_symbol = f"{'-' if direction == -1 else ''}{axis}"
        rotation_order_str += f"_{rot_symbol}"

        # USE ROBUST ROTATION LOGIC
        # We pass the list of objects so they can be detached and re-attached
        rotate_via_unparent_reset(parent_empty, imported_objects, angle, axis)
        
        scene.render.filepath = os.path.join(target_output_path, f"{rotation_order_str}.png")
        bpy.ops.render.render(write_still=True)

# -----------------------------------------------------------------------------
# MAIN ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
    else:
        args = []

    if len(args) < 1:
        print("\n❌ Error: Missing Rotation Degree.")
        print("Usage: blender -b -P script.py -- <DEGREE>")
        sys.exit(1)
    
    try:
        rotation_input = float(args[0])
    except ValueError:
        print("❌ Error: Rotation degree must be a number.")
        sys.exit(1)

    # Define Batch Name based on rotation
    if rotation_input.is_integer():
        batch_name = str(int(rotation_input))
    else:
        batch_name = str(rotation_input)

    current_cwd = os.getcwd()
    file_list_path = os.path.join(current_cwd, INPUT_FILE_NAME)
    
    if not os.path.exists(file_list_path):
        print(f"❌ Error: '{INPUT_FILE_NAME}' not found in {current_cwd}")
        sys.exit(1)

    with open(file_list_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    total_models = len(lines)
    print(f"🚀 Starting Batch: '{batch_name}' (Rotation: {rotation_input}°)")
    print(f"📂 Found {total_models} models to process.\n")

    for i, relative_path in enumerate(lines):
        parts = relative_path.split('/')
        if len(parts) < 2:
            continue

        folder_category = parts[0]
        subfolder_id = parts[1]

        # Output Directory
        target_output_dir = os.path.join(BASE_OUTPUT_DIR, batch_name, folder_category, subfolder_id)

        # Skip if exists
        if os.path.exists(target_output_dir) and os.path.isdir(target_output_dir):
            if os.listdir(target_output_dir):
                print(f"[{i+1}/{total_models}] ✅ Exists, skipping: {subfolder_id}")
                continue
        
        os.makedirs(target_output_dir, exist_ok=True)

        # -------------------------------------------------------
        # ORIGINAL PATH LOGIC RESTORED
        # -------------------------------------------------------
        obj_path = f'{FILEPATH_NAME}/.cache/huggingface/hub/datasets--ShapeNet--ShapeNetCore/blobs/{relative_path}/models/model_normalized.obj'

        print(f"[{i+1}/{total_models}] 🆕 Processing: {subfolder_id}")
        
        process_model(obj_path, target_output_dir, subfolder_id, rotation_input)

    print("\n🎉 Script execution completed.")
