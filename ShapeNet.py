import bpy
import math
import random
from mathutils import Matrix, Vector, Euler
import os


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

def rotate_pivot_locally(angle_rad, axis_name):
    # Standard World Axes (Fixed)
    axis_map = {
        'X': Vector((1, 0, 0)),
        'Y': Vector((0, 1, 0)),
        'Z': Vector((0, 0, 1))
    }
    vec = axis_map[axis_name]
    rot_mat = Matrix.Rotation(angle_rad, 4, vec)
    
    # GLOBAL ROTATION: Put rot_mat FIRST
    # This applies the rotation along the fixed World Axis
    parent_empty.matrix_world = rot_mat @ parent_empty.matrix_world
    
    # Ensure it stays at center
    parent_empty.location = Vector((0,0,0))
    
# -----------------------------------------------------------------------------
# RENDER LOGIC
# -----------------------------------------------------------------------------
def process_model(relative_path, rotation_degree):
    loop = 7
    clear_scene()

    # 2. Import
    print(f"Loading OBJ: {obj_path}")
    bpy.ops.wm.obj_import(
        filepath=bpy.path.abspath(obj_path),
        use_split_objects=True,
        use_split_groups=True,
        validate_meshes=False
    )

    imported_objects = [o for o in bpy.context.selected_objects if o.type == 'MESH']

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

    # 6. CAMERA SETUP (Strictly -Y)
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    scene = bpy.context.scene
    scene.camera = camera
    camera.location = Vector((0, -3.0, 0))
    camera.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ')

    # 7. RENDER SETTINGS
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_backface_culling = False
    scene.render.film_transparent = True

    # -----------------------------------------------------------------------------
    # RANDOM SEED SETUP
    # -----------------------------------------------------------------------------
    # Extract the unique model ID (e.g. 'a851...721') from the path
    model_id_str = relative_path.split('/')[-1]

    # Convert the last 6 characters of the hex string to an integer
    # This ensures every unique model gets a unique seed.
    try:
        # int('7b721', 16) -> converts hex to int
        model_id_int = int(model_id_str[-6:], 16)
    except:
        # Fallback if path is weird
        model_id_int = 12345
    # Add the rotation angle to the seed to avoid same image set rotation order is fixed
    # Using degrees (45) instead of radians to keep the number clean
    seed_val = model_id_int + int(math.degrees(rotation_increment))
    random.seed(seed_val)
    # -----------------------------------------------------------------------------
    # RENDER LOOP
    # -----------------------------------------------------------------------------
    rotation_order_str = "base"

    scene.render.filepath = os.path.join(output_path, f"{rotation_order_str}.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {rotation_order_str}")

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

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
collection_name = "ImportedMeshes"
BASE_OUTPUT_DIR = os.path.join(os.getcwd(), "test")
INPUT_FILE_NAME = "directory.txt"

# Paths
filepath_name = '/Users/albert'
relative_path = '03325088/a851047aeb3793403ca0c4be71e7b721'
obj_path = f'{filepath_name}/.cache/huggingface/hub/datasets--ShapeNet--ShapeNetCore/blobs/{relative_path}/models/model_normalized.obj'

current_dir = os.getcwd()
output_path = os.path.join(current_dir, "test","5")
os.makedirs(output_path, exist_ok=True)


# -----------------------------------------------------------------------------
# MAIN ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
    else:
        args = []

    if len(args) < 1:
        print("❌ Error: Missing Rotation Degree.")
        print("Usage: blender -b -P ShapeNet.py -- <DEGREE>")
        sys.exit(1)
    
    try:
        rotation_input = float(args[0])
    except ValueError:
        print("❌ Error: Rotation degree must be a number.")
        sys.exit(1)

    current_cwd = os.getcwd()
    file_list_path = os.path.join(current_cwd, INPUT_FILE_NAME)

    print(f"🚀 Starting Batch | Rotation: {rotation_input}°")
    
    if not os.path.exists(file_list_path):
        print(f"❌ Error: '{INPUT_FILE_NAME}' not found in {current_cwd}")
        sys.exit(1)

    with open(file_list_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    total_models = len(lines)
    print(f"📂 Found {total_models} models.")

    for i, line in enumerate(lines):
        print(f"[{i+1}/{total_models}] Processing...")
        process_model(line, rotation_input)

    print("🎉 All tasks completed.")
