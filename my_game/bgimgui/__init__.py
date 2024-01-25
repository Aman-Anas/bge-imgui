import os
import sys
import pathlib
import numpy as np
from . import import_fix
# What follows is an incredibly cursed workaround for a bug when importing imgui_bundle
# via the embedded player multiple times.

user_package_path = os.path.join(sys.prefix, 'lib', 'site-packages')

# Ensure the packages from range site-packages are installed first priority
sys.path.insert(0, user_package_path)

imgui_path = pathlib.Path(f"{user_package_path}/imgui_bundle/__init__.py")
if not imgui_path.exists():
    msg = "imgui_bundle is not installed. Please refer to the bgimgui config instructions."
    print(msg)
    raise ImportError(msg)

with open(imgui_path, 'r') as init_file:
    src = init_file.readlines()

if src[0] != "#BGE_PATCHED_2\n":
    print("Patching imgui_bundle for BGE...")
    with open(imgui_path, 'w+') as init_file:
        init_file.write(import_fix.data)
    print("Patch complete!")

# Now that the patch is complete, resume normal imports
if True:
    from .imgui_wrapper import BGEImguiWrapper
    from .renderer import BGEImguiRenderer
    from .image import *
    from .gui_style import *
