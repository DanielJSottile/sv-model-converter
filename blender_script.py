import bpy
from bpy import ops
import os
import shutil
import sys

def delete_existing_objects():
    # Deselect all objects first
    bpy.ops.object.select_all(action='DESELECT')

    # Select and remove all objects in the scene
    for obj in bpy.context.scene.objects:
        obj.select_set(True)
    bpy.ops.object.delete()  # Delete selected objects

    # Remove orphaned data to fully clear everything (optional)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

def bake_eye_texture(trmdl_dir, texture_name):
    # Create a plane for the eye texture
    bpy.ops.mesh.primitive_plane_add(size=2)
    plane = bpy.context.object

    # Apply the "eye" material to the plane
    materials = [mat for mat in bpy.data.materials if "eye" in mat.name.lower()]
    if materials:
        eye_material = materials[0]
        if not plane.data.materials:
            plane.data.materials.append(eye_material)
        else:
            plane.data.materials[0] = eye_material

    # Set the viewport to Material Preview mode
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'

    # Set up the shader editor to work with the material nodes
    for area in bpy.context.screen.areas:
        if area.type == 'NODE_EDITOR':
            bpy.context.area.ui_type = 'ShaderNodeTree'
            bpy.context.space_data.shader_type = 'OBJECT'
            break

    # Node setup for baking the texture
    mat_node_tree = plane.active_material.node_tree
    nodes = mat_node_tree.nodes
    links = mat_node_tree.links

    image_texture_node = nodes.new(type="ShaderNodeTexImage")
    baked_image = bpy.data.images.new(texture_name, width=1024, height=1024)
    image_texture_node.image = baked_image

    output_node = None
    for node in nodes:
        if node.type == 'OUTPUT_MATERIAL':
            output_node = node
            break

    if not output_node:
        output_node = nodes.new(type="ShaderNodeOutputMaterial")

    diffuse_node = None
    for node in nodes:
        if node.type == 'BSDF_DIFFUSE':
            diffuse_node = node
            break

    if diffuse_node:
        links.new(image_texture_node.outputs['Color'], diffuse_node.inputs['Color'])

    # Switch to Cycles for baking
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.bake_type = 'DIFFUSE'
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False

    # Make the plane the active object and bake the texture
    bpy.context.view_layer.objects.active = plane
    image_texture_node.select = True
    plane.active_material.node_tree.nodes.active = image_texture_node

    bpy.ops.object.bake(type='DIFFUSE')

    # Save the baked texture in the same directory as the .trmdl file
    image_save_path = os.path.join(trmdl_dir, texture_name + ".png")

    baked_image.filepath_raw = image_save_path
    baked_image.file_format = 'PNG'
    baked_image.save()

    print(f"{texture_name} saved at: {image_save_path}")

def prepare_gfbanm_files(inner_dir, gfbanm_dir):
    # Loop through files in the inner directory
    for file_name in os.listdir(inner_dir):
        if file_name.endswith('.tranm'):
            file_path = os.path.join(inner_dir, file_name)
            
            # Construct the new file name with .gfbanm extension
            new_file_name = file_name.replace('.tranm', '.gfbanm')
            new_file_path = os.path.join(gfbanm_dir, new_file_name)
            
            # Move and rename the file
            shutil.move(file_path, new_file_path)
        
    gfbanm_files_count = len([f for f in os.listdir(gfbanm_dir) if f.endswith('.gfbanm')])

    # Output the count of .tranm files processed for this model directory
    print(f"Processed {gfbanm_files_count} files in {trmdl_dir}")

# Get the file path from the command-line arguments
trmdl_filepath = sys.argv[-1]

# Get the directory where the .trmdl file is located
trmdl_dir = os.path.dirname(trmdl_filepath)

# inner path (model name / model name directory)
inner_dir = os.path.join(trmdl_dir, os.path.basename(trmdl_dir))

# Path to the gfbanm directory containing game freak animation files
gfbanm_dir = os.path.join(inner_dir, "_gfbanm")

# Create the target folders if they don't exist
os.makedirs(gfbanm_dir, exist_ok=True)

prepare_gfbanm_files(inner_dir, gfbanm_dir)

delete_existing_objects()

# Load the regular model
bpy.ops.custom_import_scene.pokemonscarletviolet(filepath=trmdl_filepath)

bpy.context.view_layer.update()

# Rotate the imported object (assuming it's the last selected object)
imported_object =  bpy.context.view_layer.objects.active
print(f"Last selected object: {imported_object.name}")
if imported_object:
    bpy.ops.object.editmode_toggle()

    # Set the rotation to 90 degrees around the X-axis (in radians)
    imported_object.rotation_euler[0] = 1.5708

    # Toggle back to Object Mode
    bpy.ops.object.editmode_toggle()

# Import all gfbanm files from the extracted directory
gfbanm_files = [f for f in os.listdir(gfbanm_dir) if f.endswith('.gfbanm')]
for gfbanm_file in gfbanm_files:
    gfbanm_filepath = os.path.join(gfbanm_dir, gfbanm_file)
    print(f"Importing GFBANM file: {gfbanm_filepath}")
    gfbanm = getattr(ops, 'import').gfbanm
    gfbanm(filepath=gfbanm_filepath)

# Select both armature and mesh for export
for obj in bpy.context.scene.objects:
    if obj.type in ['ARMATURE', 'MESH']:
        obj.select_set(True)

# Export as FBX, including both armature and mesh
output_fbx = trmdl_filepath.replace(".trmdl", ".fbx")
bpy.ops.export_scene.fbx(filepath=output_fbx, use_selection=True, add_leaf_bones=False)

print(f"Exported FBX: {output_fbx}")

# Run the eye texture bake for regular model
bake_eye_texture(trmdl_dir, "BakedTexture")


# Now repeat the process with the "Load Shiny" option
delete_existing_objects()

# Load the shiny version of the model
bpy.ops.custom_import_scene.pokemonscarletviolet(filepath=trmdl_filepath, rare=True)
bpy.context.view_layer.update()

# Rotate the imported shiny object (assuming it's the last selected object)
imported_object = bpy.context.view_layer.objects.active
print(f"Last selected shiny object: {imported_object.name}")
if imported_object:
    bpy.ops.object.editmode_toggle()

    # Set the rotation to 90 degrees around the X-axis (in radians)
    imported_object.rotation_euler[0] = 1.5708

    # Toggle back to Object Mode
    bpy.ops.object.editmode_toggle()

# Run the eye texture bake for shiny model
bake_eye_texture(trmdl_dir, "BakedTextureShiny")
