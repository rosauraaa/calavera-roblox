"""Exporta la plantilla UV de la malla facial y renderiza la mascara aplicada en Blender.

Uso (desde la raiz del repo):
    blender -b -P blender/uv_y_preview.py

Salida:
    docs/uv-plantilla.svg        - UV Editor -> Export UV Layout (base para pintar la mascara)
    docs/preview-<paleta>.png    - la textura aplicada sobre la malla canonica de MediaPipe
"""
import math
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(ROOT, "assets", "mesh", "canonical_face_model.obj")
TEX = os.path.join(ROOT, "assets", "textures")
DOCS = os.path.join(ROOT, "docs")


def import_face():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=OBJ)
    face = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = face
    return face


def export_uv_template(face):
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    path = os.path.join(DOCS, "uv-plantilla.svg")  # SVG: el modo PNG necesita GPU y falla con -b
    bpy.ops.uv.export_layout(filepath=path, size=(1024, 1024), mode="SVG", export_all=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    print("OK", path)


def textured_material(image_path):
    m = bpy.data.materials.new("Calavera")
    try:
        m.use_nodes = True
    except AttributeError:
        pass
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(image_path)
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    return m


def render_preview(face, palette):
    face.data.materials.clear()
    face.data.materials.append(textured_material(os.path.join(TEX, f"calavera-{palette}.png")))
    bpy.ops.object.shade_smooth()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.render.resolution_x, scene.render.resolution_y = 800, 900
    scene.render.film_transparent = True
    if not scene.camera:
        cam_data = bpy.data.cameras.new("cam")
        cam = bpy.data.objects.new("cam", cam_data)
        scene.collection.objects.link(cam)
        # la cara del OBJ mira hacia +Z (Y arriba); al importarla en Blender mira hacia -Y
        cam.location = (9, -38, 2)
        cam.rotation_euler = (math.radians(87), 0, math.radians(13))
        cam_data.lens = 58
        scene.camera = cam
    scene.render.filepath = os.path.join(DOCS, f"preview-{palette}.png")
    bpy.ops.render.render(write_still=True)
    print("OK", scene.render.filepath)


if __name__ == "__main__":
    os.makedirs(DOCS, exist_ok=True)
    face = import_face()
    export_uv_template(face)
    for palette in ("clasica", "turquesa", "dorada"):
        render_preview(face, palette)
