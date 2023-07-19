# bge-imgui
Integrate pyimgui with the Blender Game Engine (and variants)
Currently works with RanGE engine, UPBGE 0.2.5, and UPBGE 0.4+.

# Usage
To use in your game, simply add the bgimgui folder alongside your game blend. 
Not much documentation, but there are some comments in the python scripts
and some example files to help you.

To make a custom GUI for your game, extend BGEImguiWrapper class and 
override the initializeGUI() and drawGUI() methods. 
An example is shown in `myGUI.py`, and a usage example in `main.py`

For both UPBGE and RanGE, the example's logic bricks look roughly like this:
![example bricks](doc/ExampleBricks.png)
But you can of course use Python Components or scripts however you want. 
By default, the BGEImguiWrapper stores the instance of itself in bge.logic.gui to make it easy to access from other scripts.