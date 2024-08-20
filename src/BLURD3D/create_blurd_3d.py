import colorsys
import itertools as it
import json
import os
import time
import uuid
from math import *

import bpy
from bpy import context as C
from bpy import data as D
from constants import *
from HumGen3D import Human
from mathutils import *

with open("config.json", "r") as file:
    config = json.load(file)

ROOTDIR = config.root_dir
VERSION = "Version_{}".format(str(config.version).zfill(3))

races = {"male": RACES_MALE, "female": RACES_FEMALE}
hairs = {"male": MALE_HAIR, "female": FEMALE_HAIR}

root_path = os.path.join(ROOTDIR, VERSION)
os.makedirs(root_path, exist_ok=True)
json_fname = os.path.join(root_path, "rendered_dataset.json")


def change_expression(human, expression):
    # change the facial expression.
    if expression not in EXPRESSIONS:
        return
    category = EXPRESSIONS[expression]
    for npz in human.expression.get_options(category=category, context=C):
        expression = expression.replace(" ", "_")
        if expression in os.path.basename(npz):
            human.expression.set(npz)


def change_file_outputs(render_uuid, gender):
    scene = C.scene
    for node in scene.node_tree.nodes:
        if node.type == "OUTPUT_FILE":
            l = node.base_path.split("/")
            l[-3] = render_uuid
            l[-4] = gender
            l[-5] = VERSION
            new_path = os.path.join(ROOTDIR, "/".join(l[-5:]))
            node.base_path = new_path


def toggle_gender_switch(gender):
    gender_switch = bpy.data.node_groups["gender_switch"]
    switches = [n for n in gender_switch.nodes if "Switch" in n.name]
    for n in switches:
        n.check = gender == "male"


def hsv_to_rgb(hue, saturation, value, alpha):
    if isinstance(hue, str):
        hue = 0.0 if hue not in COLORS else COLORS[hue]
    return colorsys.hsv_to_rgb(hue, saturation, value) + (alpha,)


def get_hair_hue(color):
    return (COLORS[color] + 0.5 + HAIR_COLOR_OFFSETS[color]) % 1


def update_hair_color(obj, color):
    if color == "white":
        obj.redness.value = 0.0
        obj.lightness.value = 4.0
    elif color == "black":
        obj.lightness.value = 0.0
    else:
        obj.redness.value = 1.0
        obj.lightness.value = 4.0
        obj.hue.value = get_hair_hue(color)


def update_eye_color(obj, color):
    obj.iris_color.value = color


def update_skin_color(human, tone):
    # tone should be between 0-1, with 0 being the darkest and 1 the lightest
    human.skin.tone.value = tone


def get_control_node(node_tree, control_node_name):
    control = [
        n
        for n in node_tree.nodes
        if isinstance(n, bpy.types.ShaderNodeGroup) and control_node_name in n.name
    ][0]
    return control


def change_color_with_control(control, input_label, hue, saturation, value, alpha):
    control.inputs[input_label].default_value = hsv_to_rgb(
        hue, saturation, value, alpha
    )


def update_clothes_color(control, hue, saturation, value, alpha):
    if hue == "white":
        saturation = 0.0
        value = min(value, 0.8)
    elif hue == "black":
        value = 0.0
    change_color_with_control(control, "Main Color_C0", hue, saturation, value, alpha)


def update_eyeshadow_color(control, hue, saturation, value, alpha):
    if hue == None:
        control.inputs["Eyeshadow Opacity"].default_value = 0.0
        return
    elif hue == "white":
        saturation = 0.0
        value = min(value, 0.8)
    elif hue == "black":
        value = 0.0

    control.inputs["Eyeshadow Opacity"].default_value = 0.7
    control.inputs["Eyeshadow Color"].default_value = hsv_to_rgb(
        hue, saturation, value, alpha
    )


def update_makeup(opacity_control, color_control, hue, saturation, value, alpha):
    if hue == None:
        opacity_control.value = 0.0
    elif hue == "white":
        opacity_control.value = 1.0
        saturation = 0.0
        value = min(value, 0.8)
    elif hue == "black":
        opacity_control.value = 1.0
        value = 0.0
    else:
        color_control.value = hsv_to_rgb(hue, saturation, value, alpha)


def render_animation(render_uuid, gender):
    change_file_outputs(render_uuid, gender)
    toggle_gender_switch(gender)
    bpy.ops.render.render(animation=True)


def _get_mats_and_images(obj):
    print(obj)
    images = []
    materials = []
    if obj.type != "MESH":
        return [], []
    for mat in obj.data.materials:
        if mat is not None:
            materials.append(mat)
            nodes = mat.node_tree.nodes
            for node in [n for n in nodes if n.bl_idname == "ShaderNodeTexImage"]:
                images.append(node.image)
    return list(set(images)), materials


def already_rendered(rendered_set, entry):
    sorted_k = sorted(entry.keys())
    data_id = tuple([entry[k] for k in sorted_k])
    return data_id in rendered_set


# script starts here
json_data = {}
rendered_set = set()
if os.path.isfile(json_fname):
    with open(json_fname, "r") as file:
        json_data = json.load(file)
    for v in json_data.values():
        sorted_keys = sorted(v.keys())
        rendered_set.add(tuple([v[k] for k in sorted_keys]))

for gender in GENDERS:
    for world_hdr in WORLD_HDRS:
        for race in races[gender]:
            # create human
            human_preselect = races[gender][race]  # human_options[HUMAN_IDX]
            human = Human.from_preset(human_preselect, context=C)
            bobjects = bpy.data.objects

            # Align camera to eyes
            camera = bobjects["camera-orbit"]
            eyes = human.objects.eyes
            eyes_loc = eyes.matrix_world @ (
                0.125 * sum((Vector(o) for o in eyes.bound_box), Vector())
            )
            camera.location[2] = eyes_loc[2]

            hair_iter = hairs[gender].keys()
            beard_iter = MALE_FACIAL_HAIR.keys() if gender == "male" else [None]
            meta_params_iter = it.product(hair_iter, beard_iter, AGES)
            for k_hair, k_beard, age in meta_params_iter:
                hair_style = hairs[gender][k_hair]
                beard_style = None if k_beard is None else MALE_FACIAL_HAIR[k_beard]

                # remove hair
                for hair in human.hair.regular_hair.particle_systems:
                    human.hair.remove_system_by_name(hair.name)

                if gender == "male":
                    human.hair.face_hair.remove_all()
                    human.clothing.outfit.set(MALE_OUTFIT)
                    if beard_style is not None:
                        human.hair.face_hair.set(beard_style)
                else:
                    # Set clothing and hair
                    human.clothing.outfit.set(FEMALE_OUTFIT)

                if hair_style is not None:
                    human.hair.regular_hair.set(hair_style)

                # Age
                human.age.set(age)
                salt_and_pepper = min(age - 30, 0) / 70
                human.hair.regular_hair.salt_and_pepper.value = salt_and_pepper
                if gender == "male":
                    human.hair.face_hair.salt_and_pepper.value = salt_and_pepper

                # Set object pass indexes:
                for i, obj in enumerate(OBJECTS):
                    cur_object = bobjects[obj]
                    cur_object.pass_index = i + 1

                for i, obj in enumerate(human.clothing.outfit.objects):
                    obj.pass_index = i + PASS_IDX_OFFSET * 2 + 1

                # Seperate eyebrows and eyelashes
                hair_eye_mat = human.hair.eyebrows.materials[0].copy()
                if hair_eye_mat.name != ".HG_Eyelash":
                    hair_eye_mat.name = ".HG_Eyelash"
                    human.objects.body.data.materials.append(hair_eye_mat)
                    eyelashes = human.objects.body.particle_systems[
                        "Eyelashes_{}".format(gender.capitalize())
                    ]
                    eyelashes.settings.material = 5

                # Set material pass indexes:
                bmat = bpy.data.materials
                for i, mat in enumerate(MATERIALS):
                    cur_mat = bmat[mat]
                    cur_mat.pass_index = i + PASS_IDX_OFFSET + 1

                # Set render defaults
                human.skin.set_subsurface_scattering(True)
                human.hair.set_hair_quality("high")
                human.skin.texture.set_resolution("high")
                human.hair.update_hair_shader_type("accurate")

                color_iter = ["white", "black"] + list(COLORS.keys())
                col_with_none = [None] + color_iter
                if gender == "male":
                    hair_color_iter = (
                        [None]
                        if (hair_style is None and beard_style is None)
                        else color_iter
                    )
                    render_iter = it.product(color_iter, hair_color_iter)
                else:
                    render_iter = it.product(color_iter, color_iter)

                for render_params in render_iter:
                    if gender == "male":
                        shirt_color, hair_color = render_params
                        world_rotation = WORLD_ROTATION[0]
                        beard_color = hair_color
                        tie_color = shirt_color
                        eye_color = "brown"
                        eyebrow_color = "black"
                        eyeshadow_color = None
                        eyeliner_color = None
                        lipstick_color = None
                    else:
                        shirt_color, hair_color = render_params
                        world_rotation = WORLD_ROTATION[0]
                        lipstick_color = None
                        eye_color = "brown"
                        eyeshadow_color = None
                        tie_color = None
                        eyeliner_color = eyeshadow_color
                        eyebrow_color = (
                            "black" if eyeshadow_color is None else eyeshadow_color
                        )
                        beard_color = None

                    # Select world hdr
                    world = bpy.data.worlds[world_hdr]
                    C.scene.world = world

                    # Set world rotation
                    world_control = get_control_node(C.scene.world.node_tree, "Group")
                    world_control.inputs["Rotation"].default_value = world_rotation

                    # Change eyebrow color
                    update_hair_color(human.hair.eyebrows, eyebrow_color)

                    # Change hair color
                    if hair_style is not None:
                        update_hair_color(human.hair.regular_hair, hair_color)

                    # Change eye colour
                    update_eye_color(human.eyes, EYE_COLOR[eye_color])

                    # Gender specific changes
                    if gender == "female":
                        # Change lipstick
                        update_makeup(
                            human.skin.gender_specific.lipstick_opacity,
                            human.skin.gender_specific.lipstick_color,
                            lipstick_color,
                            1.0,
                            0.309741,
                            1.0,
                        )

                        # Change eyeliner
                        update_makeup(
                            human.skin.gender_specific.eyeliner_opacity,
                            human.skin.gender_specific.eyeliner_color,
                            eyeliner_color,
                            0.9,
                            1.0,
                            1.0,
                        )

                        # Change eyeshadow
                        hg_control_makeup = get_control_node(
                            human.skin.gender_specific, "Gender_Group"
                        )
                        update_eyeshadow_color(
                            hg_control_makeup, eyeshadow_color, 0.9, 1, 1
                        )

                        # Change shirt color
                        female_shirt = [
                            o
                            for o in human.clothing.outfit.objects
                            if "HG_TSHIRT_Female" in o.name
                        ][0]
                        hg_control_shirt = get_control_node(
                            female_shirt.active_material.node_tree, "HG_Control"
                        )
                        update_clothes_color(hg_control_shirt, shirt_color, 1, 1, 1)
                    else:
                        # Change shirt color
                        male_shirt = [
                            o
                            for o in human.clothing.outfit.objects
                            if "HG_Dress_Shirt_Male" in o.name
                        ][0]
                        hg_control_shirt = get_control_node(
                            male_shirt.active_material.node_tree, "HG_Control"
                        )
                        update_clothes_color(hg_control_shirt, shirt_color, 0.9, 1, 1)

                        # Change tie color
                        male_tie = [
                            o
                            for o in human.clothing.outfit.objects
                            if "HG_Tie_Male" in o.name
                        ][0]
                        hg_control_tie = get_control_node(
                            male_tie.active_material.node_tree, "HG_Control"
                        )
                        update_clothes_color(hg_control_tie, tie_color, 0.95, 0.5, 1)

                        # Change beard color
                        if beard_style is not None:
                            update_hair_color(human.hair.face_hair, beard_color)

                    dataset_entry = {
                        k: str(v)
                        for k, v in {
                            "gender": gender,
                            "race": race,
                            "hair": k_hair,
                            "beard": k_beard,
                            "age": age,
                            "shirt_color": shirt_color,
                            "tie_color": tie_color,
                            "eye_color": eye_color,
                            "hair_color": hair_color,
                            "beard_color": beard_color,
                            "background": world_hdr,
                            "world_rotation": world_rotation,
                            "eyeshadow_color": eyeshadow_color,
                            "eyeliner_color": eyeliner_color,
                            "eyebrow_color": eyebrow_color,
                            "lipstick_color": lipstick_color,
                        }.items()
                    }
                    if not already_rendered(rendered_set, dataset_entry):
                        render_uuid = str(uuid.uuid4())
                        render_animation(render_uuid, gender)
                        json_data[render_uuid] = dataset_entry
                        with open(json_fname, "w") as file:
                            json.dump(json_data, file)

            human.delete()
