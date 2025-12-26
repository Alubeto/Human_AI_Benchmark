import bpy
import math
import random
from mathutils import Matrix, Vector, Euler
import os

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
rotation_increment = math.radians(45)
loop = 7
filepath_name = "/Users/albert/Documents/GitHub/Human_AI_Benchmark"
output_path = os.path.join(filepath_name, "ShapeGen_Sequence")
os.makedirs(output_path, exist_ok=True)

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def clear_scene():
    for collection in bpy.data.collections:
        if collection:
            for obj in collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in bpy.data.meshes: bpy.data.meshes.remove(block)
    for block in bpy.data.materials: bpy.data.materials.remove(block)
    for block in bpy.data.textures: bpy.data.textures.remove(block)
    for block in bpy.data.images: bpy.data.images.remove(block)

def rotate_pivot_world_axis(pivot_obj, angle_rad, axis_name):
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
# MAIN EXECUTION
# -----------------------------------------------------------------------------

clear_scene()

# 1. Generate & Bake (Standard Setup)
bpy.ops.mesh.shape_generator()
gen_collection = bpy.data.collections.get("Generated Shape Collection")

if gen_collection:
    bpy.ops.object.select_all(action='DESELECT')
    for obj in gen_collection.objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

try:
    if gen_collection:
        props = gen_collection.shape_generator_properties
        props.random_seed = 97
        props.amount = 3
        props.mirror_x = False; props.mirror_y = False; props.mirror_z = False
        
        # Smooth Modifiers
        props.is_bevel = True; props.bevel_segments = 10
        props.is_subsurf = True; props.subsurf_segments = 2
        
        # Apply standard modifiers
        shapeGenObj = bpy.context.view_layer.objects.active
        if shapeGenObj:
            for mod in ["Bevel", "Mirror", "Subdivision"]:
                if mod in shapeGenObj.modifiers:
                    bpy.ops.object.modifier_apply(modifier=mod)

        # Bake Setup
        for obj in gen_collection.objects: obj.select_set(True)
        props.join_objects = True
        props.bake_smooth_result = True
        props.bake_object = True

        # Apply Bake Modifiers & Shade Smooth
        if shapeGenObj:
            bpy.context.view_layer.objects.active = shapeGenObj
            shapeGenObj.select_set(True)
            if "Shape Generator Remesh" in shapeGenObj.modifiers:
                bpy.ops.object.modifier_apply(modifier="Shape Generator Remesh")
            if "Shape Generator Smooth" in shapeGenObj.modifiers:
                bpy.ops.object.modifier_apply(modifier="Shape Generator Smooth")
            
            bpy.ops.object.shade_smooth()
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

except Exception as e:
    print(f"Error: {e}")

# 2. Parenting to Pivot
shapeGenObj = bpy.data.objects.get('Generated Shape')
world_origin = Vector((0, 0, 0))
bpy.ops.object.empty_add(type='PLAIN_AXES', location=world_origin)
parent_empty = bpy.context.object
parent_empty.name = "RotationPivot"

if shapeGenObj:
    shapeGenObj.location = Vector((0, 0, 0))
    shapeGenObj.rotation_euler = (0, 0, 0)
    shapeGenObj.parent = parent_empty

# 3. Camera Setup (Fixed looking at -Y)
scene = bpy.context.scene
bpy.ops.object.camera_add()
camera = bpy.context.object
scene.camera = camera
camera.location = Vector((0, -10.0, 0))
camera.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ')

# 4. Render Settings
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.render.film_transparent = True

# -----------------------------------------------------------------------------
# RENDER LOOP (WORLD AXIS ROTATION)
# -----------------------------------------------------------------------------
rotation_order_str = "base"

# Render Base
scene.render.filepath = os.path.join(output_path, f"{rotation_order_str}.png")
bpy.ops.render.render(write_still=True)
print(f"Rendered: {rotation_order_str}")

for i in range(1, loop):
    axis = random.choice(['X', 'Y', 'Z'])
    direction = random.choice([-1, 1])
    angle = direction * rotation_increment

    # Append to filename to record the step taken
    rot_symbol = f"{'-' if direction == -1 else ''}{axis}"
    rotation_order_str += f"_{rot_symbol}"

    # Perform WORLD rotation
    # This guarantees the visual change corresponds exactly to the World Axis
    rotate_pivot_world_axis(parent_empty, angle, axis)
    
    scene.render.filepath = os.path.join(output_path, f"{rotation_order_str}.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered step {i}: {rotation_order_str} (World Axis Rotation)")

print("Complete.")
