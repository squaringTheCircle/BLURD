import json
import os
from glob import glob
from uuid import uuid4

import torch
import yaml
from diffusers import (
    ControlNetModel,
    MultiAdapter,
    StableDiffusionAdapterPipeline,
    StableDiffusionControlNetImg2ImgPipeline,
    StableDiffusionControlNetPipeline,
    StableDiffusionPipeline,
    T2IAdapter,
    UniPCMultistepScheduler,
)
from PIL import Image
from prompt import PromptGenerator

JSON_FNAME = "rendered_dataset.json"

with open("config.yaml", "r") as file:
    cfg = yaml.safe_load(file)


def read_images(uuid: str, angle: int):
    angle = str(angle).zfill(4)
    factors = render_data[uuid]
    gender = factors["gender"]
    img_paths = glob(os.path.join(cfg.ROOT_DIR, gender, uuid, "**", "*.png"))

    image_pth = [
        p for p in img_paths if f"render-bg_{angle}.png" in os.path.basename(p)
    ][0]
    depth_pth = [p for p in img_paths if f"depth_{angle}.png" in os.path.basename(p)][0]
    normal_pth = [
        p for p in img_paths if f"normalmap_{angle}.png" in os.path.basename(p)
    ][0]

    image = Image.open(image_pth)
    depth = Image.open(depth_pth)
    normal = Image.open(normal_pth)
    pixel = image.resize((32, 32))
    pixel = pixel.resize((512, 512), resample=Image.Resampling.NEAREST)

    return {"image": image, "depth": depth, "normal": normal, "pixel": pixel}


def save_image(image, pth, fname):
    os.makedirs(pth, exist_ok=True)
    full_pth = os.path.join(pth, fname)
    image.save(full_pth)


def save_results(results, basepath_sd, angle=None, mode="images"):
    if isinstance(angle, int):
        str(angle).zfill(4)
    for result in results:
        out_uuid = str(uuid4())
        if angle is None:
            out_fname = f"sd_{out_uuid}.png"
        else:
            out_fname = f"sd_{angle}_{out_uuid}.png"

        out_pth = os.path.join(basepath_sd, mode)
        save_image(result, out_pth, out_fname)


with open("config.yml", "r") as file:
    cfg = yaml.safe_load(file)

with open(os.path.join(cfg.ROOT_DIR, JSON_FNAME), "r") as file:
    render_data = json.load(file)

controlnet = [
    ControlNetModel.from_single_file(
        cfg.DEPTH_CHECKPOINT,
        original_config_file=cfg.DEPTH_CONFIG,
        add_watermarker=False,
        local_files_only=True,
        torch_dtype=torch.float16,
    ),
    ControlNetModel.from_single_file(
        cfg.NORMAL_CHECKPOINT,
        original_config_file=cfg.NORMAL_CONFIG,
        add_watermarker=False,
        local_files_only=True,
        torch_dtype=torch.float16,
    ),
]

adaptor = [
    T2IAdapter.from_pretrained(cfg.T2IADATOR_CHECKPOINT, torch_dtype=torch.float16)
]

unconditioned_pipe = StableDiffusionPipeline.from_single_file(
    cfg.SD_CHECKPOINT, torch_dtype=torch.float16
)
unconditioned_pipe.scheduler = UniPCMultistepScheduler.from_config(
    unconditioned_pipe.scheduler.config
)

unconditioned_pipe.enable_xformers_memory_efficient_attention()
unconditioned_pipe.enable_model_cpu_offload()

controlnet_pipe = StableDiffusionControlNetPipeline.from_single_file(
    cfg.SD_CHECKPOINT, controlnet=controlnet, torch_dtype=torch.float16
)
controlnet_pipe.scheduler = UniPCMultistepScheduler.from_config(
    controlnet_pipe.scheduler.config
)

controlnet_pipe.enable_xformers_memory_efficient_attention()
controlnet_pipe.enable_model_cpu_offload()


img2img_pipe = StableDiffusionControlNetImg2ImgPipeline.from_single_file(
    cfg.SD_CHECKPOINT, controlnet=controlnet + adaptor, torch_dtype=torch.float16
)
img2img_pipe.scheduler = UniPCMultistepScheduler.from_config(
    img2img_pipe.scheduler.config
)

img2img_pipe.enable_xformers_memory_efficient_attention()
img2img_pipe.enable_model_cpu_offload()


for uuid, factors in render_data.items():

    basepath_uuid = os.path.join(cfg.SAVE_DIR, factors["gender"], uuid)
    basepath_sd = os.path.join(basepath_uuid, "sd")
    os.makedirs(basepath_sd, exist_ok=True)

    prompt = PromptGenerator.get_prompt(factors)
    negative_prompt = PromptGenerator.NEGATIVE_PROMPT

    results = unconditioned_pipe(
        prompt,
        num_inference_steps=20,
        negative_prompt=negative_prompt,
    ).images

    save_results(results, basepath_sd, mode="images")

    for angle in range(0, 21, 5):
        images = read_images(uuid, angle)
        control_images = [images["depth"], images["normal"]]

        results = controlnet_pipe(
            prompt,
            control_images,
            num_inference_steps=20,
            negative_prompt=negative_prompt,
            controlnet_conditioning_scale=[0.8, 0.8],
        ).images
        save_results(results, basepath_sd, angle=angle, mode="images_w_depth_normal")

    for angle in range(0, 21, 5):
        images = read_images(uuid, angle)
        control_images = [images["depth"], images["normal"], images["pixel"]]

        results = img2img_pipe(
            prompt,
            image=images["image"],
            strength=0.20,
            control_image=control_images,
            num_inference_steps=20,
            negative_prompt=negative_prompt,
            controlnet_conditioning_scale=[0.8, 0.8],
        ).images
        save_results(
            results,
            basepath_sd,
            angle=angle,
            mode="images_w_img2img_depth_normal_color",
        )
