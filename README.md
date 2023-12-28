# bge-imgui
Integrate imgui_bundle with the Blender Game Engine (and variants)
Currently works with RanGE engine, UPBGE 0.2.5, and UPBGE 0.4+.

# Usage
To use in your game, simply add the bgimgui folder alongside your game blend. 
Not much documentation, but there are some comments in the python scripts
and some example files to help you.

To make a custom GUI for your game, extend BGEImguiWrapper class and 
override the setup_gui() and draw() methods. 
An example is shown in `my_gui.py`, and a usage example in `main.py`.

> If you just want a simple example for how to use imgui_bundle/pyimgui, refer to `example.py`.

For both UPBGE and RanGE, the example's logic bricks look roughly like this:

![example bricks](doc/ExampleBricksBetter.png)

But you can of course use Python Components or scripts however you want. 
By default, the BGEImguiWrapper stores the instance of itself in bge.logic.gui to make it easy to access from other scripts.

# Configuration
In order to set up `imgui_bundle` to work correctly in your game, there are a few steps involved.
First, install `imgui_bundle` and a few other libraries into the engine's python install.
Here's a video guide: https://cdn.discordapp.com/attachments/481036916427325441/1189919082124943360/2023-12-28_08-10-18.mp4

After that, there is currently a bug with using imgui_bundle in the **embedded** player. **Standalone**
works perfectly fine, however. To fix the embedded bug, you need to edit `__init__.py` located next
to your game engine .exe's python (for example, `upbge folder /3.6/lib/site-packages/imgui_bundle/__init__.py`)

Then, add a try-catch statement at the top like so
```py
try:
    from imgui_bundle._imgui_bundle import imgui as imgui  # type: ignore
    from imgui_bundle._imgui_bundle import hello_imgui as hello_imgui
    # lots of more import stuff in between
    from imgui_bundle.im_col32 import IM_COL32
except ImportError:
    pass
```
And that's it! Test out using the example blend files.

# Contribution
Simply make a pull request and/or add an issue for any bugs you find, I'm also active on the UPBGE discord as well as blenderartists.org
