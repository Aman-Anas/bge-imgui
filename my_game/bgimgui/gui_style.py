from typing import TYPE_CHECKING

from imgui_bundle import imgui
import tomli

if TYPE_CHECKING:
    from imgui_bundle.imgui import Style


def getDirection(direction: str):
    match direction:
        case "Left":
            return imgui.Dir_.left
        case "Right":
            return imgui.Dir_.right
        case "Up":
            return imgui.Dir_.up
        case "Down":
            return imgui.Dir_.down
        case _:
            return imgui.Dir_.none


def style_gui_from_file(styleConfigPath: str):

    with open(styleConfigPath, "rb") as styleFile:
        data = tomli.load(styleFile)

    # Style GUI from file data
    style = imgui.get_style()  # override active style
    imgui.style_colors_dark()

    style.alpha = data["alpha"]
    style.window_padding = data["windowPadding"]
    style.window_rounding = data["windowRounding"]
    style.window_border_size = data["windowBorderSize"]
    style.window_min_size = data["windowMinSize"]
    style.window_title_align = data["windowTitleAlign"]
    style.window_menu_button_position = getDirection(
        data["windowMenuButtonPosition"])
    style.child_rounding = data["childRounding"]
    style.child_border_size = data["childBorderSize"]
    style.popup_rounding = data["popupRounding"]
    style.popup_border_size = data["popupBorderSize"]
    style.frame_padding = data["framePadding"]
    style.frame_rounding = data["frameRounding"]
    style.frame_border_size = data["frameBorderSize"]
    style.item_spacing = data["itemSpacing"]
    style.item_inner_spacing = data["itemInnerSpacing"]
    style.cell_padding = data["cellPadding"]
    style.indent_spacing = data["indentSpacing"]
    style.columns_min_spacing = data["columnsMinSpacing"]
    style.scrollbar_size = data["scrollbarSize"]
    style.scrollbar_rounding = data["scrollbarRounding"]
    style.grab_min_size = data["grabMinSize"]
    style.grab_rounding = data["grabRounding"]
    style.tab_rounding = data["tabRounding"]
    style.tab_border_size = data["tabBorderSize"]
    style.tab_min_width_for_close_button = data["tabMinWidthForCloseButton"]
    style.color_button_position = getDirection(data["colorButtonPosition"])
    style.button_text_align = data["buttonTextAlign"]
    style.selectable_text_align = data["selectableTextAlign"]

    # Get colors from the data
    colorData = data["colors"]

    def fixColorRange(color: tuple, maxVal: float):
        color[0] = color[0]/maxVal
        color[1] = color[1]/maxVal
        color[2] = color[2]/maxVal
        return color
    colorData = {color: fixColorRange(
        colorData[color], 255.0) for color in colorData}

    style.set_color_(imgui.Col_.text, colorData["Text"])
    style.set_color_(imgui.Col_.text_disabled, colorData["TextDisabled"])
    style.set_color_(imgui.Col_.window_bg, colorData["WindowBg"])
    style.set_color_(imgui.Col_.child_bg, colorData["ChildBg"])
    style.set_color_(imgui.Col_.popup_bg, colorData["PopupBg"])
    style.set_color_(imgui.Col_.border, colorData["Border"])
    style.set_color_(imgui.Col_.border_shadow, colorData["BorderShadow"])
    style.set_color_(imgui.Col_.frame_bg, colorData["FrameBg"])
    style.set_color_(imgui.Col_.frame_bg_hovered,
                     colorData["FrameBgHovered"])
    style.set_color_(imgui.Col_.frame_bg_active,
                     colorData["FrameBgActive"])
    style.set_color_(imgui.Col_.title_bg, colorData["TitleBg"])
    style.set_color_(imgui.Col_.title_bg_active,
                     colorData["TitleBgActive"])
    style.set_color_(imgui.Col_.title_bg_collapsed,
                     colorData["TitleBgCollapsed"])
    style.set_color_(imgui.Col_.menu_bar_bg, colorData["MenuBarBg"])
    style.set_color_(imgui.Col_.scrollbar_bg,
                     colorData["ScrollbarBg"])
    style.set_color_(imgui.Col_.scrollbar_grab, colorData["ScrollbarGrab"])
    style.set_color_(imgui.Col_.scrollbar_grab_hovered,
                     colorData["ScrollbarGrabHovered"])
    style.set_color_(imgui.Col_.scrollbar_grab_active,
                     colorData["ScrollbarGrabActive"])
    style.set_color_(imgui.Col_.check_mark, colorData["CheckMark"])
    style.set_color_(imgui.Col_.slider_grab, colorData["SliderGrab"])
    style.set_color_(imgui.Col_.button, colorData["Button"])
    style.set_color_(imgui.Col_.button_hovered, colorData["ButtonHovered"])
    style.set_color_(imgui.Col_.button_active, colorData["ButtonActive"])
    style.set_color_(imgui.Col_.header, colorData["Header"])
    style.set_color_(imgui.Col_.header_hovered, colorData["HeaderHovered"])
    style.set_color_(imgui.Col_.header_active, colorData["HeaderActive"])
    style.set_color_(imgui.Col_.separator, colorData["Separator"])
    style.set_color_(imgui.Col_.separator_hovered,
                     colorData["SeparatorHovered"])
    style.set_color_(imgui.Col_.separator_active,
                     colorData["SeparatorActive"])
    style.set_color_(imgui.Col_.resize_grip, colorData["ResizeGrip"])
    style.set_color_(imgui.Col_.resize_grip_hovered,
                     colorData["ResizeGripHovered"])
    style.set_color_(imgui.Col_.resize_grip_active,
                     colorData["ResizeGripActive"])
    style.set_color_(imgui.Col_.tab, colorData["Tab"])
    style.set_color_(imgui.Col_.tab_hovered, colorData["TabHovered"])
    style.set_color_(imgui.Col_.tab_active, colorData["TabActive"])
    style.set_color_(imgui.Col_.tab_unfocused, colorData["TabUnfocused"])
    style.set_color_(imgui.Col_.tab_unfocused_active,
                     colorData["TabUnfocusedActive"])
    style.set_color_(imgui.Col_.plot_lines, colorData["PlotLines"])
    style.set_color_(imgui.Col_.plot_lines_hovered,
                     colorData["PlotLinesHovered"])
    style.set_color_(imgui.Col_.plot_histogram, colorData["PlotHistogram"])
    style.set_color_(imgui.Col_.plot_histogram_hovered,
                     colorData["PlotHistogramHovered"])
    style.set_color_(imgui.Col_.table_header_bg,
                     colorData["TableHeaderBg"])
    style.set_color_(imgui.Col_.table_border_strong,
                     colorData["TableBorderStrong"])
    style.set_color_(imgui.Col_.table_border_light,
                     colorData["TableBorderLight"])
    style.set_color_(imgui.Col_.table_row_bg, colorData["TableRowBg"])
    style.set_color_(imgui.Col_.table_row_bg_alt,
                     colorData["TableRowBgAlt"])
    style.set_color_(imgui.Col_.text_selected_bg,
                     colorData["TextSelectedBg"])
    style.set_color_(imgui.Col_.drag_drop_target, colorData["DragDropTarget"])
    style.set_color_(imgui.Col_.nav_highlight, colorData["NavHighlight"])
    style.set_color_(imgui.Col_.nav_windowing_highlight,
                     colorData["NavWindowingHighlight"])
    style.set_color_(imgui.Col_.nav_windowing_dim_bg,
                     colorData["NavWindowingDimBg"])
    style.set_color_(imgui.Col_.modal_window_dim_bg,
                     colorData["ModalWindowDimBg"])
