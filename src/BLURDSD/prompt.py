class PromptGenerator:

    PROMPT_TEMPLATE = "RAW photo of a {bald}{race} {age} {gender} {hair}wearing {clothing}, background is a grassy meadow, 8k uhd, dslr, soft lighting, high quality, film grain, Fujifilm XT3"
    CLASSIFY_TEMPLATE = "A picture of a {age} {race} {gender}"
    NEGATIVE_PROMPT = "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime, mutated hands and fingers:1.4), (deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, disconnected limbs, mutation, mutated, ugly, disgusting, amputation"

    @classmethod
    def get_prompt(cls, factors):
        prompt_kwarg = {
            "race": factors["race"].capitalize(),
            "age": f"{factors['age']} y.o.",
            "gender": "man" if factors["gender"] == "male" else "woman",
        }

        if factors["gender"] == "male":
            if factors["hair"] != "none":
                hair_style = (
                    "{} bald top" if factors["hair"] == "bald_top" else "{} short"
                )
                hair_style = hair_style.format(factors["hair_color"])
            else:
                hair_style = None

            if factors["beard"] != "none":
                beard = "{} beard"
                beard = beard.format(factors["beard_color"])
            else:
                beard = None

            if hair_style is None and beard is None:
                hair = ""
            elif hair_style is not None and beard is None:
                hair = f"with {hair_style} haircut, "
            elif hair_style is None and beard is not None:
                hair = f"with a {beard}, "
            else:
                hair = f"with {hair_style} haircut and a {beard}, "

            clothing = (
                f"a {factors['shirt_color']} shirt and {factors['tie_color']} tie"
            )

            prompt_kwarg["hair"] = hair
            prompt_kwarg["clothing"] = clothing
            prompt_kwarg["bald"] = "bald " if hair_style is None else ""

        elif factors["gender"] == "female":
            if factors["hair"] != "none":
                hair_style = "{}" + f" {factors['hair'].replace('_', ' ')} hair"
                hair_style = hair_style.format(factors["hair_color"])
            else:
                hair_style = None

            if hair_style is None:
                hair = ""
            else:
                hair = f"with {hair_style}, "

            clothing = f"a {factors['shirt_color']} shirt"

            prompt_kwarg["hair"] = hair
            prompt_kwarg["clothing"] = clothing
            prompt_kwarg["bald"] = "bald " if hair_style is None else ""

        prompt = cls.PROMPT_TEMPLATE.format(**prompt_kwarg)
        return prompt

    @classmethod
    def get_classify_str(cls, instance):
        if isinstance(instance, dict):
            instance = instance.items()
        prompt_kwarg = {k: v for k, v in instance}

        if "gender" not in prompt_kwarg:
            prompt_kwarg["gender"] = "person"

        if "race" not in prompt_kwarg:
            prompt_kwarg["race"] = ""

        if "age" not in prompt_kwarg:
            prompt_kwarg["age"] = ""

        with_to_add = ""
        prompt_to_add = []
        if len(prompt_kwarg.keys()) > 3:
            with_to_add = " with "

        for k, v in instance:
            if k == "gender" or k == "race":
                pass
            elif k == "hair":
                if v == "none":
                    v = "bald"
                prompt_to_add.append(f'a {v.replace("_"," ")} hair style')
            elif prompt_kwarg["gender"] == "male" and k == "beard":
                if v.lower() == "none":
                    prompt_to_add.append("no beard")
                else:
                    prompt_to_add.append(f'a {v.replace("_"," ")}')
            elif k == "age":
                prompt_kwarg[k] = v if v == "" else f"{v} y.o. "
            elif k == "shirt_color":
                prompt_to_add.append(f"wearing a {v} shirt")
            elif prompt_kwarg["gender"] == "male" and k == "tie_color":
                prompt_to_add.append(f"with a {v} tie")
            elif (
                "hair" in prompt_kwarg
                and prompt_kwarg["hair"].lower() != "none"
                and k == "hair_color"
            ):
                prompt_to_add.append(f"{v} hair")
            elif (
                "beard" in prompt_kwarg
                and prompt_kwarg["beard"].lower() != "none"
                and k == "beard_color"
            ):
                prompt_to_add.append(f"{v} colored beard")

        prompt_kwarg = {
            k: v for k, v in prompt_kwarg.items() if k in ["age", "gender", "race"]
        }
        prompt_str = cls.CLASSIFY_TEMPLATE.format(**prompt_kwarg)
        prompt_to_add_str = with_to_add + ", ".join(prompt_to_add)
        prompt_str += prompt_to_add_str
        prompt_str = " ".join(prompt_str.split())

        return prompt_str
