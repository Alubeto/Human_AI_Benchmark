import bpy
import math
import random
import os
from mathutils import Matrix, Vector, Euler

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
BASE_OUTPUT_DIR = "/Users/albert/Documents/GitHub/Human_AI_Benchmark/ShapeGen"

# angles_to_process = [15, 30, 45, 60, 75]  # Loop over these angles
angles_to_process = [60,75] 
amount_count = 10                         # 1 to 10 extrusions
rotate_num = 1800                         # 0 to 1799 iterations per amount
loop_count = 7                           # Number of rotations per shape

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def clear_scene():
    """Clears everything: Meshes, Lights, Cameras, Collections."""
    for collection in list(bpy.data.collections):
        for obj in collection.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
    
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.textures, bpy.data.images]:
        for item in block:
            block.remove(item)

def rotate_pivot_locally(pivot_obj, angle_rad, axis_name):
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

def shapeGenGenerator(amount, seed):
    """Generates the shape and applies Baking (Clay look)."""
    # 1. GENERATE
    bpy.ops.mesh.shape_generator()
    gen_collection = bpy.data.collections.get("Generated Shape Collection")
    
    if not gen_collection:
        return None

    try:
        props = gen_collection.shape_generator_properties
        props.random_seed = seed
        props.amount = amount
        props.mirror_x = False; props.mirror_y = False; props.mirror_z = False
        
        # 2. STANDARD SMOOTHING
        props.is_bevel = True; props.bevel_segments = 10
        props.is_subsurf = True; props.subsurf_segments = 2
        
        # Apply standard modifiers NOW to freeze geometry
        # We look up the object fresh to avoid stale references
        obj_ref = bpy.data.objects.get('Generated Shape')
        if obj_ref:
            bpy.context.view_layer.objects.active = obj_ref
            for mod in ["Bevel", "Mirror", "Subdivision"]:
                if mod in obj_ref.modifiers:
                    bpy.ops.object.modifier_apply(modifier=mod)

        # 3. BAKING (The Destructive Step)
        # Force select ALL parts so 'Join Objects' finds them
        bpy.ops.object.select_all(action='DESELECT')
        for obj in gen_collection.objects:
            obj.select_set(True)
            # Make the main shape active if possible, to ensure it survives the join
            if obj.name == 'Generated Shape':
                bpy.context.view_layer.objects.active = obj

        # Enable Baking Props
        props.join_objects = True        # <--- This likely deletes old references!
        props.bake_smooth_result = True
        props.bake_object = True
        
        # 4. APPLY BAKE & POLISH
        # CRITICAL: Re-fetch the object. The old pointer is likely dead.
        final_obj = bpy.data.objects.get('Generated Shape')
        
        if final_obj:
            bpy.context.view_layer.objects.active = final_obj
            final_obj.select_set(True)
            
            # Apply Bake Modifiers
            if "Shape Generator Remesh" in final_obj.modifiers:
                bpy.ops.object.modifier_apply(modifier="Shape Generator Remesh")
            
            if "Shape Generator Smooth" in final_obj.modifiers:
                bpy.ops.object.modifier_apply(modifier="Shape Generator Smooth")
            
            # Force Smooth Shading
            bpy.ops.object.shade_smooth()
            
            # Center Origin & Apply Scale
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            
            return final_obj
        else:
            print("Error: 'Generated Shape' lost after bake.")
            return None

    except Exception as e:
        print(f"Error in shapeGenGenerator: {e}")
        return None

# -----------------------------------------------------------------------------
# MAIN EXECUTION LOOP
# -----------------------------------------------------------------------------

# --- LOOP 1: ANGLES (15, 30, 45, 60, 75) ---
for angle_deg in angles_to_process:
    rotation_increment = math.radians(angle_deg)
    print(f"--- Starting Batch for Angle: {angle_deg}° ---")
    
    current_angle_path = os.path.join(BASE_OUTPUT_DIR, str(angle_deg))
    
    # --- LOOP 2: AMOUNT (1 to 10) ---
    for amount in range(1, amount_count + 1):
        
        # --- LOOP 3: ITERATIONS (0 to 1799) ---
        for i in range(rotate_num):
            seed = i  # The seed is simply the current index
            
            # Construct the path first to check existence
            base_path = os.path.join(current_angle_path, str(amount), str(seed))
            
            # --- SKIP LOGIC ---
            # If the folder exists AND contains files, skip this iteration
            if os.path.exists(base_path) and os.listdir(base_path):
                print(f"Skipping existing data: {base_path}")
                continue
            
            # If we didn't skip, create the folder and proceed
            os.makedirs(base_path, exist_ok=True)
            
            clear_scene()
            
            # 2. Generate Object
            shape_obj = shapeGenGenerator(amount, seed)
            if not shape_obj: continue

            # 3. Setup Pivot
            shape_obj.location = Vector((0, 0, 0))
            shape_obj.rotation_euler = (0, 0, 0)
            
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
            parent_empty = bpy.context.object
            parent_empty.name = "RotationPivot"
            
            shape_obj.parent = parent_empty
            
            # 4. Setup Camera
            bpy.ops.object.camera_add()
            camera = bpy.context.object
            camera.location = Vector((0, -7.0, 0))
            camera.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ')
            
            # 5. Render Settings
            scene = bpy.context.scene
            scene.camera = camera
            scene.render.engine = 'BLENDER_WORKBENCH'
            scene.render.resolution_x = 1080
            scene.render.resolution_y = 1080
            scene.display.shading.light = 'STUDIO'
            scene.display.shading.color_type = 'MATERIAL'
            scene.display.shading.show_backface_culling = True
            scene.render.film_transparent = True
            
            # 6. Render Loop (Base + Rotations)
            rotation_order_str = "base"
            
            # Render Base
            scene.render.filepath = os.path.join(base_path, f"{rotation_order_str}.png")
            bpy.ops.render.render(write_still=True)
            
            # Rotation Steps
            for step in range(loop_count):
                axis = random.choice(['X', 'Y', 'Z'])
                direction = random.choice([-1, 1])
                angle = direction * rotation_increment
                
                rot_symbol = f"{'-' if direction == -1 else ''}{axis}"
                rotation_order_str += f"_{rot_symbol}"
                
                rotate_pivot_locally(parent_empty, angle, axis)
                
                scene.render.filepath = os.path.join(base_path, f"{rotation_order_str}.png")
                bpy.ops.render.render(write_still=True)

print("All angles processed successfully!")
