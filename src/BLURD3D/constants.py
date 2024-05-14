GENDERS = ["male", "female"]
OBJECTS = ["HG_Body", "HG_Eyes", "HG_TeethLower", "HG_TeethUpper"]
MATERIALS = [".HG_Hair_Eye", ".HG_Hair_Face", ".HG_Hair_Head", ".Human", ".HG_Eyelash"]
PASS_IDX_OFFSET = 20
AGES = [30, 70]
FEMALE_OUTFIT = "outfits/female/Summer/Beach_Day.blend"
MALE_OUTFIT = "outfits/male/Office/Stock_Exchange.blend"
FEMALE_HAIR = {
    "buzzcut": "hair/head/female/Short/Buzzcut Fade.json",
    "undercut": "hair/head/female/Long/Undercut.json",
    "afro_dreads": "hair/head/female/Curls/Afro Dreads.json",
    "bob_long": "hair/head/female/Long/Bob Long.json",
}
MALE_HAIR = {
    "none": None,
    "bald_top": "hair/head/male/Aged/Bald Top.json",
    "short_combed": "hair/head/male/Short/Short Combed.json",
}
MALE_FACIAL_HAIR = {
    "none": None,
    "full_beard": "hair/face_hair/Beard/Full_Beard_1.json",
}
RACES_FEMALE = {
    "caucasian": "models/female/Caucasian presets/Caucasian 1.json",
    "asian": "models/female/Asian presets/Asian 1.json",
    "hispanic": "models/female/Hispanic/Aria.json",
    "african": "models/female/Black presets/Black 2.json",
}
RACES_MALE = {
    "caucasian": "models/male/Caucasian Presets/Caucasian 1.json",
    "asian": "models/male/Asian presets/Asian 1.json",
    "hispanic": "models/male/Hispanic/John.json",
    "african": "models/male/Black presets/Black 1.json",
}
# colors hue values
COLORS = {
    "red": 0.0,
    "orange": 10 / 360,
    "yellow": 40 / 360,
    "green": 120 / 360,
    "cyan": 180 / 360,
    "blue": 240 / 360,
    "violet": 270 / 360,
    "magenta": 300 / 360,
}
HAIR_COLOR_OFFSETS = {
    "red": -0.045,
    "orange": -0.04,
    "yellow": -0.05,
    "green": -0.05,
    "cyan": -0.05,
    "blue": -0.05,
    "violet": -0.05,
    "magenta": -0.05,
}
EYE_COLOR = {
    "blue": (0.278196, 0.655529, 1.0, 1.0),
    "green": (0.319608, 1.0, 0.285339, 1.0),
    "brown": (0.361307, 0.187821, 0.07036, 1.0),
}
WORLD_HDRS = ["alps_field", "lebombo"]
WORLD_ROTATION = [0.0, 45.0, 90.0]
