import bpy
import math
import random
from mathutils import Matrix, Vector
import sys

# Configuration
rotation_increment = math.radians(45)
filepath_name = '/Users/albert'

# Cleanup function
def clear_scene():
    # Remove existing collection
    for collection in bpy.data.collections:  
        if collection:
            for obj in collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
    
    # Clear remaining objects
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
clear_scene()    
#setup_cam(bpy.context.scene)
bpy.ops.mesh.shape_generator()

# Create a new collection and move imported objects
collection = bpy.data.collections['Generated Shape Collection']

scene = bpy.context.scene

bpy.ops.object.camera_add()
camera = bpy.context.object
scene.camera = camera

# Adjust camera position to directly face the object's mass center
camera_distance = 10.0  # Adjust as needed
camera.location = Vector((0, -camera_distance, 0))
camera.rotation_euler = (math.radians(90), 0, 0)  # Face forward

# Set up Workbench rendering engine
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1080
scene.render.resolution_y = 1080

# Workbench shading settings for white background
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.background_type = 'WORLD'  # Force a solid background
#scene.display.shading.background_color = (1, 1, 1)  # White background

scene.display.shading.show_backface_culling = True  # Optional, but can help with transparency
scene.render.film_transparent = True  # Enable transparent background


#for obj in bpy.data.objects:
#    collection.objects.link(obj)
shapeGenObj = bpy.data.objects['Generated Shape']
#rotate_around_world(shapeGenObj, 'X', rotation_increment)

#shapeGenObj.rotatation_euler = (value=0.813503, orient_axis='Y', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False, snap_elements={'INCREMENT'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=True, use_snap_edit=True, use_snap_nonedit=True, use_snap_selectable=False, release_confirm=True)

#bpy.ops.object.select_all(action='SELECT')
#bpy.ops.object.mode_set(mode = 'OBJECT')
shapeGenObj.rotation_euler = (math.radians(90), 0, 0)


# Initial render before rotation
scene.render.filepath = f"{filepath_name}/sample.png"
#bpy.ops.render.render(write_still=True)
