import site
import pathlib

# What follows is an incredibly cursed workaround for a bug when importing imgui_bundle
# via the embedded player multiple times.

user_package_path = site.getusersitepackages()
imgui_path = pathlib.Path(f"{user_package_path}/imgui_bundle/__init__.py")
if not imgui_path.exists():
    msg = "imgui_bundle is not installed. Please refer to the bgimgui config instructions."
    print(msg)
    raise ImportError(msg)

with open(imgui_path, 'r') as init_file:
    src = init_file.readlines()

if src[0] != "#BGE_PATCHED\n":
    print("Patching imgui_bundle for BGE...")
    src.insert(0, "try:\n")
    src.insert(0, "#BGE_PATCHED\n")
    for index, line in enumerate(src):
        if line.startswith("from"):
            src[index] = f"    {line}"
        if "glfw" in line:
            insert_point = index
            break
    src.insert(insert_point,
               "except (ImportError, ModuleNotFoundError):\n    pass\n")

    with open(imgui_path, 'w+') as init_file:
        init_file.write("".join(src))
    print("Patch complete!")

# Now that the patch is complete, resume normal imports
if True:
    from .imgui_wrapper import BGEImguiWrapper
    from .image import *
    from .gui_style import *
