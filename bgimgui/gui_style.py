from typing import TYPE_CHECKING

from imgui_bundle import imgui
import tomli

if TYPE_CHECKING:
    from imgui_bundle.imgui import Style


def getDirection(direction: str):
    match direction:
        case "Left":
            return imgui.DIRECTION_LEFT
        case "Right":
            return imgui.DIRECTION_RIGHT
        case "Up":
            return imgui.DIRECTION_UP
        case "Down":
            return imgui.DIRECTION_DOWN
        case _:
            return imgui.DIRECTION_NONE


def styleGUI(styleConfigPath: str):

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

    colors = style.colors

    colors[imgui.COLOR_TEXT] = colorData["Text"]
    colors[imgui.COLOR_TEXT_DISABLED] = colorData["TextDisabled"]
    colors[imgui.COLOR_WINDOW_BACKGROUND] = colorData["WindowBg"]
    colors[imgui.COLOR_CHILD_BACKGROUND] = colorData["ChildBg"]
    colors[imgui.COLOR_POPUP_BACKGROUND] = colorData["PopupBg"]
    colors[imgui.COLOR_BORDER] = colorData["Border"]
    colors[imgui.COLOR_BORDER_SHADOW] = colorData["BorderShadow"]
    colors[imgui.COLOR_FRAME_BACKGROUND] = colorData["FrameBg"]
    colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = colorData["FrameBgHovered"]
    colors[imgui.COLOR_FRAME_BACKGROUND_ACTIVE] = colorData["FrameBgActive"]
    colors[imgui.COLOR_TITLE_BACKGROUND] = colorData["TitleBg"]
    colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE] = colorData["TitleBgActive"]
    colors[imgui.COLOR_TITLE_BACKGROUND_COLLAPSED] = colorData["TitleBgCollapsed"]
    colors[imgui.COLOR_MENUBAR_BACKGROUND] = colorData["MenuBarBg"]
    colors[imgui.COLOR_SCROLLBAR_BACKGROUND] = colorData["ScrollbarBg"]
    colors[imgui.COLOR_SCROLLBAR_GRAB] = colorData["ScrollbarGrab"]
    colors[imgui.COLOR_SCROLLBAR_GRAB_HOVERED] = colorData["ScrollbarGrabHovered"]
    colors[imgui.COLOR_SCROLLBAR_GRAB_ACTIVE] = colorData["ScrollbarGrabActive"]
    colors[imgui.COLOR_CHECK_MARK] = colorData["CheckMark"]
    colors[imgui.COLOR_SLIDER_GRAB] = colorData["SliderGrab"]
    colors[imgui.COLOR_BUTTON] = colorData["Button"]
    colors[imgui.COLOR_BUTTON_HOVERED] = colorData["ButtonHovered"]
    colors[imgui.COLOR_BUTTON_ACTIVE] = colorData["ButtonActive"]
    colors[imgui.COLOR_HEADER] = colorData["Header"]
    colors[imgui.COLOR_HEADER_HOVERED] = colorData["HeaderHovered"]
    colors[imgui.COLOR_HEADER_ACTIVE] = colorData["HeaderActive"]
    colors[imgui.COLOR_SEPARATOR] = colorData["Separator"]
    colors[imgui.COLOR_SEPARATOR_HOVERED] = colorData["SeparatorHovered"]
    colors[imgui.COLOR_SEPARATOR_ACTIVE] = colorData["SeparatorActive"]
    colors[imgui.COLOR_RESIZE_GRIP] = colorData["ResizeGrip"]
    colors[imgui.COLOR_RESIZE_GRIP_HOVERED] = colorData["ResizeGripHovered"]
    colors[imgui.COLOR_RESIZE_GRIP_ACTIVE] = colorData["ResizeGripActive"]
    colors[imgui.COLOR_TAB] = colorData["Tab"]
    colors[imgui.COLOR_TAB_HOVERED] = colorData["TabHovered"]
    colors[imgui.COLOR_TAB_ACTIVE] = colorData["TabActive"]
    colors[imgui.COLOR_TAB_UNFOCUSED] = colorData["TabUnfocused"]
    colors[imgui.COLOR_TAB_UNFOCUSED_ACTIVE] = colorData["TabUnfocusedActive"]
    colors[imgui.COLOR_PLOT_LINES] = colorData["PlotLines"]
    colors[imgui.COLOR_PLOT_LINES_HOVERED] = colorData["PlotLinesHovered"]
    colors[imgui.COLOR_PLOT_HISTOGRAM] = colorData["PlotHistogram"]
    colors[imgui.COLOR_PLOT_HISTOGRAM_HOVERED] = colorData["PlotHistogramHovered"]
    colors[imgui.COLOR_TABLE_HEADER_BACKGROUND] = colorData["TableHeaderBg"]
    colors[imgui.COLOR_TABLE_BORDER_STRONG] = colorData["TableBorderStrong"]
    colors[imgui.COLOR_TABLE_BORDER_LIGHT] = colorData["TableBorderLight"]
    colors[imgui.COLOR_TABLE_ROW_BACKGROUND] = colorData["TableRowBg"]
    colors[imgui.COLOR_TABLE_ROW_BACKGROUND_ALT] = colorData["TableRowBgAlt"]
    colors[imgui.COLOR_TEXT_SELECTED_BACKGROUND] = colorData["TextSelectedBg"]
    colors[imgui.COLOR_DRAG_DROP_TARGET] = colorData["DragDropTarget"]
    colors[imgui.COLOR_NAV_HIGHLIGHT] = colorData["NavHighlight"]
    colors[imgui.COLOR_NAV_WINDOWING_HIGHLIGHT] = colorData["NavWindowingHighlight"]
    colors[imgui.COLOR_NAV_WINDOWING_DIM_BACKGROUND] = colorData["NavWindowingDimBg"]
    colors[imgui.COLOR_MODAL_WINDOW_DIM_BACKGROUND] = colorData["ModalWindowDimBg"]
