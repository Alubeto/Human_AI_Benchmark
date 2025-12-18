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
bpy.data.collections["Generated Shape Collection"].shape_generator_properties.is_bevel = True
bpy.data.collections["Generated Shape Collection"].shape_generator_properties.bevel_segments = 10
bpy.data.collections["Generated Shape Collection"].shape_generator_properties.amount = 4
bpy.data.collections["Generated Shape Collection"].shape_generator_properties.bevel_clamp_overlap = True


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

shapeGenObj.rotation_euler = (math.radians(90), math.radians(45), math.radians(45))


# Initial render before rotation
scene.render.filepath = f"{filepath_name}/sample.png"
bpy.ops.render.render(write_still=True)r
