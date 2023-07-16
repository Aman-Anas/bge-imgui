from __future__ import annotations
import pygui
import math
import time
from PIL import Image
from enum import Enum, auto


def help_marker(desc: str):
    pygui.text_disabled("(?)")
    if pygui.is_item_hovered(pygui.HOVERED_FLAGS_DELAY_SHORT) and pygui.begin_tooltip():
        pygui.push_text_wrap_pos(pygui.get_font_size() * 35)
        pygui.text_unformatted(desc)
        pygui.pop_text_wrap_pos()
        pygui.end_tooltip()


def show_docking_disabled_message():
    io = pygui.get_io()
    pygui.text("ERROR: Docking is not enabled! See Demo > Configuration.")
    pygui.text("Set io.ConfigFlags |= ImGuiConfigFlags_DockingEnable in your code, or ")
    pygui.same_line(0, 0)
    if pygui.small_button("click here"):
        io.config_flags |= pygui.CONFIG_FLAGS_DOCKING_ENABLE


class ExampleAppConsole:
    def __init__(self):
        self.input_buf = pygui.String()
        self.items = []
        self.commands = [
            "HELP",
            "HISTORY",
            "CLEAR",
            "CLASSIFY",
        ]
        self.history = []
        # -1: new line, 0..History.Size-1 browsing history.
        self.history_pos = -1
        self.imgui_filter = pygui.ImGuiTextFilter.create()
        self.auto_scroll = pygui.Bool(True)
        self.scroll_to_bottom = pygui.Bool(False)
    
    def __del__(self):
        self.imgui_filter.destroy()
    
    def clear_log(self):
        self.items.clear()
    
    def add_log(self, string: str, *args):
        self.items.append(" ".join([string] + list(args)))
    
    def draw(self, title: str, p_open: pygui.Bool):
        pygui.set_next_window_size((520, 600), pygui.COND_FIRST_USE_EVER)
        if not pygui.begin(title, p_open):
            pygui.end()
            return
        
        # As a specific feature guaranteed by the library, after calling Begin() the last Item represent the title bar.
        # So e.g. IsItemHovered() will return true when hovering the title bar.
        # Here we create a context menu only available from the title bar.
        if pygui.begin_popup_context_item():
            if pygui.menu_item("Close Console"):
                p_open.value = False
            pygui.end_popup()
        
        pygui.text_wrapped(
            "This example implements a console with basic coloring, completion (TAB key) and history (Up/Down keys). A more elaborate "
            "implementation may want to store entries along with extra data such as timestamp, emitter, etc.")
        pygui.text_wrapped("Enter 'HELP' for help.")

        if pygui.small_button("Add Debug Text"):
            self.add_log("{} some text".format(len(self.items)))
            self.add_log("some more text")
            self.add_log("display very important message here!")
        
        pygui.same_line()
        if pygui.small_button("Add Debug Error"):
            self.add_log("[error] something went wrong")
        pygui.same_line()
        if pygui.small_button("Clear"):
            self.clear_log()
        pygui.same_line()
        copy_to_clipboard = pygui.small_button("Copy")

        pygui.separator()

        # Options menu
        if pygui.begin_popup("Options"):
            pygui.checkbox("Auto-scroll", self.auto_scroll)
            pygui.end_popup()

        # Options, Filter
        if pygui.button("Options"):
            pygui.open_popup("Options")
        pygui.same_line()
        self.imgui_filter.draw('Filter ("incl,-excl") ("error")', 180)
        pygui.separator()

        # Reserve enough left-over height for 1 separator + 1 input text
        footer_height_to_reserve = pygui.get_style().item_spacing[1] + pygui.get_frame_height_with_spacing()
        if pygui.begin_child("ScrollingRegion", (0, -footer_height_to_reserve), False, pygui.WINDOW_FLAGS_HORIZONTAL_SCROLLBAR):
            if pygui.begin_popup_context_window():
                if pygui.selectable("Clear"):
                    self.clear_log()
                pygui.end_popup()
            
            # Display every line as a separate entry so we can change their color or add custom widgets.
            # If you only want raw text you can use ImGui::TextUnformatted(log.begin(), log.end());
            # NB- if you have thousands of entries this approach may be too inefficient and may require user-side clipping
            # to only process visible items. The clipper will automatically measure the height of your first item and then
            # "seek" to display only items in the visible area.
            # To use the clipper we can replace your standard loop:
            #      for (int i = 0; i < Items.Size; i++)
            #   With:
            #      ImGuiListClipper clipper;
            #      clipper.Begin(Items.Size);
            #      while (clipper.Step())
            #         for (int i = clipper.DisplayStart; i < clipper.DisplayEnd; i++)
            # - That your items are evenly spaced (same height)
            # - That you have cheap random access to your elements (you can access them given their index,
            #   without processing all the ones before)
            # You cannot this code as-is if a filter is active because it breaks the 'cheap random-access' property.
            # We would need random-access on the post-filtered list.
            # A typical application wanting coarse clipping and filtering may want to pre-compute an array of indices
            # or offsets of items that passed the filtering test, recomputing this array when user changes the filter,
            # and appending newly elements as they are inserted. This is left as a task to the user until we can manage
            # to improve this example code!
            # If your items are of variable height:
            # - Split them into same height items would be simpler and facilitate random-seeking into your list.
            # - Consider using manual call to IsRectVisible() and skipping extraneous decoration from your items.
            pygui.push_style_var(pygui.STYLE_VAR_ITEM_SPACING, (4, 1)) # Tighten spacing
            if copy_to_clipboard:
                pygui.log_to_clipboard()
            
            for item in self.items:
                if not self.imgui_filter.pass_filter(item):
                    continue

                # Normally you would store more information in your item than just a string.
                # (e.g. make Items[] an array of structure, store color/type etc.)
                color = (0, 0, 0, 0)
                has_color = False
                if "[error]" in item:
                    color = (1, 0.4, 0.4, 1)
                    has_color = True
                elif "#" in item:
                    color = (1, 0.8, 0.6, 1)
                    has_color = True
                if has_color:
                    pygui.push_style_color(pygui.COL_TEXT, color)
                pygui.text_unformatted(item)
                if has_color:
                    pygui.pop_style_color()
            
            if copy_to_clipboard:
                pygui.log_finish()
            
           # Keep up at the bottom of the scroll region if we were already at the bottom at the beginning of the frame.
           # Using a scrollbar or mouse-wheel will take away from the bottom edge.
            if self.scroll_to_bottom or (self.auto_scroll and pygui.get_scroll_y() >= pygui.get_scroll_max_y()):
                pygui.set_scroll_here_y(1)
            self.scroll_to_bottom.value = False

            pygui.pop_style_var()
        pygui.end_child()
        pygui.separator()

        # Command-line
        reclaim_focus = False
        input_text_flags = \
            pygui.INPUT_TEXT_FLAGS_ENTER_RETURNS_TRUE | \
            pygui.INPUT_TEXT_FLAGS_ESCAPE_CLEARS_ALL | \
            pygui.INPUT_TEXT_FLAGS_CALLBACK_COMPLETION | \
            pygui.INPUT_TEXT_FLAGS_CALLBACK_HISTORY
        
        if pygui.input_text("Input", self.input_buf, input_text_flags, self.text_edit_callback):
            if len(self.input_buf.value.strip()) > 0:
                self.exec_command(self.input_buf.value)
            self.input_buf.value = ""
            reclaim_focus = True

        # Auto-focus on window apparition
        pygui.set_item_default_focus()
        if reclaim_focus:
            pygui.set_keyboard_focus_here(-1) # Auto focus previous widget

        pygui.end()

    def exec_command(self, command_line: str):
        self.add_log("# {}\n".format(command_line))

        # Insert into history. First find match and delete it so it can be pushed to the back.
        # This isn't trying to be smart or optimal.
        self.history_pos = -1
        for i in reversed(range(len(self.history))):
            if self.history[i] == command_line:
                self.history.pop(i)
                break
        self.history.append(command_line)
        
        if command_line.startswith("CLEAR"):
            self.clear_log()
        elif command_line.startswith("HELP"):
            self.add_log("Commands:")
            for command in self.commands:
                self.add_log(f"- {command}")
        elif command_line.startswith("HISTORY"):
            first = len(self.history) - 10
            for i in range(max(first, 0), len(self.history)):
                self.add_log("{} {}\n".format(i, self.history[i]))
        else:
            self.add_log("Unknown command: {}".format(command_line))
        
        self.scroll_to_bottom.value = True
    
    def text_edit_callback(self, data: pygui.ImGuiInputTextCallbackData, user_data) -> int:
        if data.event_flag == pygui.INPUT_TEXT_FLAGS_CALLBACK_COMPLETION:
            # Example of TEXT COMPLETION
            # Locate beginning of current word
            word_end = data.cursor_pos
            word_start = data.cursor_pos

            while (word_start > 0):
                c = data.buf[word_start - 1]
                if c == ' ' or c == '\t' or c == ',' or c == ';':
                    break
                word_start -= 1
            word = data.buf[word_start:word_end]
        
            candidates = [command for command in self.commands if command.startswith(word.upper())]
            if len(candidates) == 0:
                self.add_log('No match for "{}"!\n'.format(word))
            elif len(candidates) == 1:
                data.delete_chars(word_start, word_end - word_start)
                data.insert_chars(data.cursor_pos, candidates[0] + " ")
            
            else:
                # Multiple matches. Complete as much as we can..
                # So inputing "C"+Tab will complete to "CL" then display "CLEAR" and "CLASSIFY" as matches.
                match_len = word_end - word_start
                while True:
                    all_candidates_matches = True
                    for i, candidate in enumerate(candidates):
                        if i == 0:
                            c = candidate[match_len].upper()
                            continue
                        
                        if c != candidate[match_len].upper():
                            all_candidates_matches = False
                            break

                    if not all_candidates_matches:
                        break
                    match_len += 1

                if match_len > 0:
                    data.delete_chars(word_start, word_end - word_start)
                    data.insert_chars(data.cursor_pos, candidates[0][:match_len])

                # List matches
                self.add_log("Possible matches:\n")
                for candidate in candidates:
                    self.add_log("- {}\n".format(candidate))
            
        elif data.event_flag == pygui.INPUT_TEXT_FLAGS_CALLBACK_HISTORY:
            # Example of HISTORY
            prev_history_pos = self.history_pos
            if data.event_key == pygui.KEY_UP_ARROW:
                if self.history_pos == -1:
                    self.history_pos = len(self.history) - 1
                elif self.history_pos > 0:
                    self.history_pos -= 1
            elif data.event_key == pygui.KEY_DOWN_ARROW:
                if self.history_pos != -1:
                    self.history_pos += 1
                    if self.history_pos >= len(self.history):
                       self.history_pos = -1

            # A better implementation would preserve the data on the current input line along with cursor position.
            if prev_history_pos != self.history_pos:
                history_str = self.history[self.history_pos] if self.history_pos >= 0 else ""
                data.delete_chars(0, data.buf_text_len)
                data.insert_chars(0, history_str)
        return 0


class ExampleAppDocuments:
    class MyDocument:
        def __init__(self, name: str, open_=True, color=(1, 1, 1, 1)):
            self.name = name
            self.open_ = pygui.Bool(open_)
            self.open_prev = pygui.Bool(open_)
            self.color = pygui.Vec4(*color)
            self.dirty = False
            self.want_close = False
        
        def do_open(self):
            self.open_.value = True
        
        def do_queue_close(self):
            self.want_close = True
        
        def do_force_close(self):
            self.open_.value = False
            self.dirty = False
        
        def do_save(self):
            self.dirty = False
        
        def display_contents(self):
            pygui.push_id(self)
            pygui.text(f'Document "{self.name}"')
            pygui.push_style_color(pygui.COL_TEXT, self.color.tuple())
            pygui.text_wrapped("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.")
            pygui.pop_style_color()
            if pygui.button("Modify", (100, 0)):
                self.dirty = True
            pygui.same_line()
            if pygui.button("Save", (100, 0)):
                self.do_save()
            pygui.color_edit3("color", self.color)  # Useful to test drag and drop and hold-dragged-to-open-tab behavior.
            pygui.pop_id()

        def display_context_menu(self):
            if not pygui.begin_popup_context_item():
                return

            buf = f"Save {self.name}"
            if pygui.menu_item(buf, "CTRL+S", False, self.open_.value):
                self.do_save()
            if pygui.menu_item("Close", "CTRL+W", False, self.open_.value):
                self.do_queue_close()
            pygui.end_popup()

    def __init__(self):
        self.documents = []
        self.documents.append(ExampleAppDocuments.MyDocument("Lettuce",             True,  (0.4, 0.8, 0.4, 1.0)))
        self.documents.append(ExampleAppDocuments.MyDocument("Eggplant",            True,  (0.8, 0.5, 1.0, 1.0)))
        self.documents.append(ExampleAppDocuments.MyDocument("Carrot",              True,  (1.0, 0.8, 0.5, 1.0)))
        self.documents.append(ExampleAppDocuments.MyDocument("Tomato",              False, (1.0, 0.3, 0.4, 1.0)))
        self.documents.append(ExampleAppDocuments.MyDocument("A Rather Long Title", False))
        self.documents.append(ExampleAppDocuments.MyDocument("Some Document",       False))

    def notify_of_document_closed_elsewhere(self):
        # [Optional] Notify the system of Tabs/Windows closure that happened outside the regular tab interface.
        # If a tab has been closed programmatically (aka closed from another source such as the Checkbox() in the demo,
        # as opposed to clicking on the regular tab closing button) and stops being submitted, it will take a frame for
        # the tab bar to notice its absence. During this frame there will be a gap in the tab bar, and if the tab that has
        # disappeared was the selected one, the tab bar will report no selected tab during the frame. This will effectively
        # give the impression of a flicker for one frame.
        # We call SetTabItemClosed() to manually notify the Tab Bar or Docking system of removed tabs to avoid this glitch.
        # Note that this completely optional, and only affect tab bars with the ImGuiTabBarFlags_Reorderable flag.
        for doc in self.documents:
            doc: ExampleAppDocuments.MyDocument
            if not doc.open_ and doc.open_prev:
                pygui.set_tab_item_closed(doc.name)
            doc.open_prev.value = doc.open_.value
    
    class Target(Enum):
        NONE = 0
        TAB = 1                  # Create documents as local tab into a local tab bar
        DOCKSPACE_AND_WINDOW = 2 # Create documents as regular windows, and create an embedded dockspace
    
    opt_target = pygui.Int(Target.TAB.value)
    opt_reorderable = pygui.Bool(True)
    opt_fitting_flags = pygui.TAB_BAR_FLAGS_FITTING_POLICY_DEFAULT
    close_queue = []

    def show_example_app_documents(self, p_open: pygui.Bool):
        # When (opt_target == Target_DockSpaceAndWindow) there is the possibily that one of our child Document window (e.g. "Eggplant")
        # that we emit gets docked into the same spot as the parent window ("Example: Documents").
        # This would create a problematic pt_target = pygui.Int(Target.TAB) loop because selecting the "Eggplant" tab would make the "Example: Documents" tab
        # not visible, which in turn would stop submitting the "Eggplant" window.
        # We avoid this problem by submitting our documents window even if our parent window is not currently visible.
        # Another solution may be to make the "Example: Documents" window use the ImGuiWindowFlags_NoDocking.
        window_contents_visible = pygui.begin("Example: Pygui Documents", p_open, pygui.WINDOW_FLAGS_MENU_BAR)
        if not window_contents_visible and ExampleAppDocuments.opt_target.value != ExampleAppDocuments.Target.DOCKSPACE_AND_WINDOW:
            pygui.end()
            return

        if pygui.begin_menu_bar():
            if pygui.begin_menu("File"):
                open_count = 0
                for doc_n in range(len(self.documents)):
                    open_count += 1 if self.documents[doc_n].open_ else 0
                
                if pygui.begin_menu("Open", open_count < len(self.documents)):
                    for doc in self.documents:
                        doc: ExampleAppDocuments.MyDocument
                        if not doc.open_:
                            if pygui.menu_item(doc.name):
                                doc.do_open()
                    pygui.end_menu()
                if pygui.menu_item("Close All Documents", None, False, open_count > 0):
                    for doc in self.documents:
                        doc.do_queue_close()
                if pygui.menu_item("Exit", "Ctrl+F4") and p_open:
                    p_open.value = False
                pygui.end_menu()
            pygui.end_menu_bar()
        
        # [Debug] List documents with one checkbox for each
        for doc_n, doc in enumerate(self.documents):
            if doc_n > 0:
                pygui.same_line()
            pygui.push_id(doc)
            if pygui.checkbox(doc.name, doc.open_):
                if not doc.open_:
                    doc.do_force_close()
            pygui.pop_id()
        pygui.push_item_width(pygui.get_font_size() * 12)
        pygui.combo("Output", ExampleAppDocuments.opt_target, ["None", "TabBar+Tabs", "DockSpace+Window"])
        pygui.pop_item_width()
        redock_all = False
        if ExampleAppDocuments.opt_target.value == ExampleAppDocuments.Target.TAB.value:
            pygui.same_line()
            pygui.checkbox("Reorderable Tabs", ExampleAppDocuments.opt_reorderable)
        if ExampleAppDocuments.opt_target.value == ExampleAppDocuments.Target.DOCKSPACE_AND_WINDOW.value:
            pygui.same_line()
            redock_all = pygui.button("Redock all")
        
        pygui.separator()

        # About the ImGuiWindowFlags_UnsavedDocument / ImGuiTabItemFlags_UnsavedDocument flags.
        # They have multiple effects:
        # - Display a dot next to the title.
        # - Tab is selected when clicking the X close button.
        # - Closure is not assumed (will wait for user to stop submitting the tab).
        #   Otherwise closure is assumed when pressing the X, so if you keep submitting the tab may reappear at end of tab bar.
        #   We need to assume closure by default otherwise waiting for "lack of submission" on the next frame would leave an empty
        #   hole for one-frame, both in the tab-bar and in tab-contents when closing a tab/window.
        #   The rarely used SetTabItemClosed() function is a way to notify of programmatic closure to avoid the one-frame hole.

        # Tabs
        if ExampleAppDocuments.opt_target.value == ExampleAppDocuments.Target.TAB.value:
            tab_bar_flags = ExampleAppDocuments.opt_fitting_flags | (pygui.TAB_BAR_FLAGS_REORDERABLE if ExampleAppDocuments.opt_reorderable else 0)
            if pygui.begin_tab_bar("##tabs", tab_bar_flags):
                if ExampleAppDocuments.opt_reorderable:
                    self.notify_of_document_closed_elsewhere()
                
                # [DEBUG] Stress tests
                # if ((ImGui::GetFrameCount() % 30) == 0) docs[1].Open ^= 1;            // [DEBUG] Automatically show/hide a tab. Test various interactions e.g. dragging with this on.
                # if (ImGui::GetIO().KeyCtrl) ImGui::SetTabItemSelected(docs[1].Name);  // [DEBUG] Test SetTabItemSelected(), probably not very useful as-is anyway..

                # Submit Tabs
                for doc in self.documents:
                    if not doc.open_:
                        continue

                    tab_flags = (pygui.TAB_ITEM_FLAGS_UNSAVED_DOCUMENT if doc.dirty else 0)
                    visible = pygui.begin_tab_item(doc.name, doc.open_, tab_flags)
                    
                    # Cancel attempt to close when unsaved add to save queue so we can display a popup.
                    if not doc.open_ and doc.dirty:
                        doc.open_.value = True
                        doc.do_queue_close()
                    
                    doc.display_context_menu()
                    if visible:
                        doc.display_contents()
                        pygui.end_tab_item()
                
                pygui.end_tab_bar()
        elif ExampleAppDocuments.opt_target.value == ExampleAppDocuments.Target.DOCKSPACE_AND_WINDOW.value:
            if pygui.get_io().config_flags & pygui.CONFIG_FLAGS_DOCKING_ENABLE:
                self.notify_of_document_closed_elsewhere()

                # Create a DockSpace node where any window can be docked
                dockspace_id = pygui.get_id("MyPyguiDockSpace")
                pygui.dock_space(dockspace_id)

                # Create Windows
                for doc in self.documents:
                    if not doc.open_:
                        continue

                    pygui.set_next_window_dock_id(dockspace_id, pygui.COND_ALWAYS if redock_all else pygui.COND_FIRST_USE_EVER)
                    window_flags = pygui.WINDOW_FLAGS_UNSAVED_DOCUMENT if doc.dirty else 0
                    # pygui note: Adding the ##pygui suffix gives the window some
                    # uniqueness so that having the imgui_demo version open at the
                    # same time doesn't produce unpredictable behaviour.
                    visible = pygui.begin(doc.name + "##pygui", doc.open_, window_flags)

                    # Cancel attempt to close when unsaved add to save queue so we can display a popup.
                    if not doc.open_ and doc.dirty:
                        doc.open_.value = True
                        doc.do_queue_close()
                    
                    doc.display_context_menu()
                    if visible:
                        doc.display_contents()

                    pygui.end()
            else:
                show_docking_disabled_message()
        
        # Early out other contents
        if not window_contents_visible:
            pygui.end()
            return
    
        # Update closing queue
        if len(ExampleAppDocuments.close_queue) == 0:
            # Close queue is locked once we started a popup
            for doc in self.documents:
                if doc.want_close:
                    doc.want_close = False
                    ExampleAppDocuments.close_queue.append(doc)
        
        # Display closing confirmation UI
        if len(ExampleAppDocuments.close_queue) > 0:
            closed_queue_unsaved_documents = 0
            for n in range(len(ExampleAppDocuments.close_queue)):
                if ExampleAppDocuments.close_queue[n].dirty:
                    closed_queue_unsaved_documents += 1
                
            if closed_queue_unsaved_documents == 0:
                # Close documents when all are unsaved
                for n in range(len(ExampleAppDocuments.close_queue)):
                    ExampleAppDocuments.close_queue[n].do_force_close()
                ExampleAppDocuments.close_queue.clear()
            else:
                if not pygui.is_popup_open("Save?"):
                    pygui.open_popup("Save?")
                if pygui.begin_popup_modal("Save?", None, pygui.WINDOW_FLAGS_ALWAYS_AUTO_RESIZE):
                    pygui.text("Save change to the following items?")
                    item_height = pygui.get_text_line_height_with_spacing()
                    if pygui.begin_child_frame(pygui.get_id("pygui_frame"), (-pygui.FLT_MIN, 6.25 * item_height)):
                        for n in range(len(ExampleAppDocuments.close_queue)):
                            if ExampleAppDocuments.close_queue[n].dirty:
                                pygui.text(ExampleAppDocuments.close_queue[n].name)
                        pygui.end_child_frame()
                    button_size = (pygui.get_font_size() * 7, 0)
                    if pygui.button("Yes", button_size):
                        for n in range(len(ExampleAppDocuments.close_queue)):
                            if ExampleAppDocuments.close_queue[n].dirty:
                                ExampleAppDocuments.close_queue[n].do_save()
                            ExampleAppDocuments.close_queue[n].do_force_close()
                        ExampleAppDocuments.close_queue.clear()
                        pygui.close_current_popup()
                    pygui.same_line()
                    if pygui.button("No", button_size):
                        for n in range(len(ExampleAppDocuments.close_queue)):
                            ExampleAppDocuments.close_queue[n].do_force_close()
                        ExampleAppDocuments.close_queue.clear()
                        pygui.close_current_popup()
                    pygui.same_line()
                    if pygui.button("Cancel", button_size):
                        ExampleAppDocuments.close_queue.clear()
                        pygui.close_current_popup()
                    pygui.end_popup()
        pygui.end()


class demo:
    example_app_console = ExampleAppConsole()
    example_app_documents = ExampleAppDocuments()

    show_app_console = pygui.Bool(False)
    show_app_documents = pygui.Bool(False)
    show_custom_rendering = pygui.Bool(False)
    show_font_demo = pygui.Bool(False)

    show_about_window = pygui.Bool(False)
    show_debug_log_window = pygui.Bool(False)
    show_font_selector = pygui.Bool(False)
    show_metrics_window = pygui.Bool(False)
    show_stack_tool_window = pygui.Bool(False)
    show_style_editor = pygui.Bool(False)
    show_style_selector = pygui.Bool(False)
    show_user_guide = pygui.Bool(False)


def pygui_demo_window():
    pygui.begin("Pygui Demo Window", None, pygui.WINDOW_FLAGS_MENU_BAR)
    show_menu_bar()

    if demo.show_app_console:
        demo.example_app_console.draw("Example: Pygui Console", demo.show_app_console)
    if demo.show_app_documents:
        demo.example_app_documents.show_example_app_documents(demo.show_app_documents)
    if demo.show_custom_rendering:
        show_app_custom_rendering(demo.show_custom_rendering)
    if demo.show_font_demo:
        show_fonts_demo()
    
    if demo.show_about_window:
        pygui.show_about_window(demo.show_about_window)
    if demo.show_debug_log_window:
        pygui.show_debug_log_window(demo.show_debug_log_window)
    if demo.show_font_selector:
        if pygui.begin("Font Selector", demo.show_font_selector):
            pygui.show_font_selector("Font")
        pygui.end()
    if demo.show_metrics_window:
        pygui.show_metrics_window(demo.show_metrics_window)
    if demo.show_stack_tool_window:
        pygui.show_stack_tool_window(demo.show_stack_tool_window)
    if demo.show_style_editor:
        if pygui.begin("Style Editor", demo.show_style_editor):
            pygui.show_style_editor()
        pygui.end()
    if demo.show_style_selector:
        if pygui.begin("Style Selector", demo.show_style_selector):
            pygui.show_style_selector("Style")
        pygui.end()
    if demo.show_user_guide:
        if pygui.begin("User Guide", demo.show_user_guide):
            pygui.show_user_guide()
        pygui.end()

    show_demo_widgets()
    show_demo_window_layout()
    show_demo_tables()
    show_random_extras()
    show_crash_test()
    pygui.end()


class widget:
    _singleton_instance = None

    @staticmethod
    def instance() -> widget:
        if widget._singleton_instance is None:
            widget._singleton_instance = widget()
        return widget._singleton_instance
    
    def __init__(self):
        self.widgets_image = Image.open("pygui/img/code.png")
        self.widgets_image_texture = pygui.load_image(self.widgets_image)

    general_clicked = 0
    general_check = pygui.Bool(True)
    general_e = pygui.Int()
    general_counter = 0
    inputs_str0 = pygui.String("Hello, World!", 128)
    inputs_str1 = pygui.String(buffer_size=128)
    inputs_i0 = pygui.Int(123)
    inputs_f0 = pygui.Float(0.001)
    inputs_d0 = pygui.Double(999999.00000001)
    inputs_f1 = pygui.Float(1.e10)
    inputs_vec4a = [
        pygui.Float(0.1),
        pygui.Float(0.2),
        pygui.Float(0.3),
        pygui.Float(0.44),
    ]
    drag_i1 = pygui.Int(50)
    drag_i2 = pygui.Int(42)
    drag_f1 = pygui.Float(1)
    drag_f2 = pygui.Float(0.0067)
    sliders_i1 = pygui.Int()
    sliders_f1 = pygui.Float(0.123)
    sliders_f2 = pygui.Float()
    sliders_angle = pygui.Float()
    sliders_elem = pygui.Int()
    picker_col1 = pygui.Vec4(1, 0, 0.2, 1)
    picker_col2 = pygui.Vec4(0.4, 0.7, 0, 0.5)
    combo_item_current = pygui.Int()
    list_item_current = pygui.Int()
    tree_base_flags = pygui.Int(
        pygui.TREE_NODE_FLAGS_OPEN_ON_ARROW | \
        pygui.TREE_NODE_FLAGS_OPEN_ON_DOUBLE_CLICK | \
        pygui.TREE_NODE_FLAGS_SPAN_AVAIL_WIDTH)
    tree_align_label_with_current_x_position = pygui.Bool(False)
    tree_test_drag_and_drop = pygui.Bool(False)
    tree_selection_mask = pygui.Int(1 << 2)
    header_closable_group = pygui.Bool(True)
    text_wrap_width = pygui.Float(200)
    text_utf8_buf = pygui.String("日本語", 64)
    combo_flags = pygui.Int()
    combo_item_current_idx = pygui.Int()
    combo_item_current_2 = pygui.Int()
    combo_item_current_3 = pygui.Int()
    combo_item_current_4 = pygui.Int()
    image_use_text_color_for_tint = pygui.Bool(False)
    image_pressed_count = 0
    list_box_item_current_idx = 0
    select_selection = [
        pygui.Bool(False),
        pygui.Bool(True),
        pygui.Bool(False),
        pygui.Bool(False),
        pygui.Bool(False),
    ]
    select_selected = -1
    select_single_state_selected = -1
    select_multi_state_selection = [
        pygui.Bool(False),
        pygui.Bool(False),
        pygui.Bool(False),
        pygui.Bool(False),
        pygui.Bool(False),
    ]
    select_render_selected = [
        pygui.Bool(False),
        pygui.Bool(False),
        pygui.Bool(False),
    ]
    select_column_selected = [pygui.Bool(False) for _ in range(10)]
    select_grid_selected = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]
    select_allign_selected = [
        pygui.Bool(True),
        pygui.Bool(False),
        pygui.Bool(True),
        pygui.Bool(False),
        pygui.Bool(True),
        pygui.Bool(False),
        pygui.Bool(True),
        pygui.Bool(False),
        pygui.Bool(True),
    ]
    tab_active_tabs = []
    tab_next_tab_id = 0
    tab_show_leading_button = pygui.Bool(True)
    tab_show_trailing_button = pygui.Bool(True)
    tab_tab_bar_flags = pygui.Int(
        pygui.TAB_BAR_FLAGS_AUTO_SELECT_NEW_TABS | \
        pygui.TAB_BAR_FLAGS_REORDERABLE | \
        pygui.TAB_BAR_FLAGS_FITTING_POLICY_RESIZE_DOWN)
    plotting_animate = pygui.Bool(True)
    plotting_arr = [
        0.6, 0.1, 1.0, 0.5, 0.92, 0.1, 0.2
    ]
    plotting_values = [0] * 90
    plotting_values_offset = 0
    plotting_refresh_time = 0
    plotting_phase = 0
    plotting_func_type = pygui.Int()
    plotting_display_count = pygui.Int(70)
    plotting_progress = 0
    plotting_progress_dir = 1
    colour_color = pygui.Vec4(114 / 255, 144 / 255, 154 / 255, 200 / 255)
    colour_flags = pygui.Int()
    colour_alpha_preview = pygui.Bool(True)
    colour_alpha_half_preview = pygui.Bool(False)
    colour_drag_and_drop = pygui.Bool(True)
    colour_options_menu = pygui.Bool(True)
    colour_hdr = pygui.Bool(False)
    colour_saved_palette_init = pygui.Bool(True)
    colour_saved_palette = [pygui.Vec4.zero() for _ in range(32)]
    colour_backup_color = pygui.Vec4.zero()
    colour_no_border = pygui.Bool(False)
    colour_alpha = pygui.Bool(True)
    colour_alpha_bar = pygui.Bool(True)
    colour_side_preview = pygui.Bool(True)
    colour_ref_color = pygui.Bool(False)
    colour_ref_color_v = pygui.Vec4(1, 0, 1, 0.5)
    colour_display_mode = pygui.Int(False)
    colour_picker_mode = pygui.Int(False)
    colour_color_hsv = pygui.Vec4(0.23, 1, 1, 1)
    data_drag_clamp = pygui.Bool(False)
    data_s8_v = pygui.Int(127)
    data_u8_v = pygui.Int(255)
    data_s16_v = pygui.Int(32767)
    data_u16_v = pygui.Int(65535)
    data_s32_v = pygui.Long(-1)
    data_u32_v = pygui.Long(-1)
    data_s64_v = pygui.Long(-1)
    data_u64_v = pygui.Long(-1)
    data_f32_v = pygui.Float(0.123)
    data_f64_v = pygui.Double(90000.01234567890123456789)
    data_inputs_step = pygui.Bool(True)
    data_long_n = [
        pygui.Long(10000000),
        pygui.Long(20000000),
    ]
    data_float_n = [
        pygui.Float(0.1),
        pygui.Float(0.2),
        pygui.Float(0.3),
        pygui.Float(0.4),
    ]
    data_double_n = [
        pygui.Double(0.00001),
        pygui.Double(0.00002),
        pygui.Double(0.00003),
        pygui.Double(0.00004),
    ]
    multi_vec4f = pygui.Vec4(0.10, 0.2, 0.3, 0.44)
    multi_vec4i = pygui.Vec4(1, 5, 100, 255)
    tab_tab_bar_flags = pygui.Int(pygui.TAB_BAR_FLAGS_REORDERABLE)
    tab_opened = [pygui.Bool(True) for _ in range(4)]
    vert_int_value = pygui.Int()
    vert_values = [
        pygui.Float(),
        pygui.Float(0.6),
        pygui.Float(0.35),
        pygui.Float(0.9),
        pygui.Float(0.7),
        pygui.Float(0.2),
        pygui.Float(),
    ]
    vert_values2 = [
        pygui.Float(0.2),
        pygui.Float(0.8),
        pygui.Float(0.4),
        pygui.Float(0.25),
    ]


def show_demo_widgets():
    if not pygui.collapsing_header("Widgets"):
        return
    
    if pygui.tree_node("Basic"):
        pygui.separator_text("General")

        if pygui.button("Button"):
            widget.general_clicked += 1
        
        if widget.general_clicked & 1:
            pygui.same_line()
            pygui.text("Thanks for clicking me!")
        
        pygui.checkbox("checkbox", widget.general_check)

        pygui.radio_button_int_ptr("radio a", widget.general_e, 0)
        pygui.same_line()
        pygui.radio_button_int_ptr("radio b", widget.general_e, 1)
        pygui.same_line()
        pygui.radio_button_int_ptr("radio c", widget.general_e, 2)
        
        # Color buttons, demonstrate using PushID() to add unique identifier in the ID stack, and changing style.
        for i in range(6):
            if i > 0:
                pygui.same_line()
            
            pygui.push_id(i)
            pygui.push_style_color(pygui.COL_BUTTON,         pygui.color_convert_hsv_to_rgb(i / 7, 0.6, 0.6))
            pygui.push_style_color(pygui.COL_BUTTON_HOVERED, pygui.color_convert_hsv_to_rgb(i / 7, 0.7, 0.7))
            pygui.push_style_color(pygui.COL_BUTTON_ACTIVE,  pygui.color_convert_hsv_to_rgb(i / 7, 0.8, 0.8))
            pygui.button("Click")
            pygui.pop_style_color(3)
            pygui.pop_id()
        
        # Use AlignTextToFramePadding() to align text baseline to the baseline of framed widgets elements
        # (otherwise a Text+SameLine+Button sequence will have the text a little too high by default!)
        # See 'Demo->Layout->Text Baseline Alignment' for details.
        pygui.align_text_to_frame_padding()
        pygui.text("Hold to repeat:")
        pygui.same_line()

        spacing: float = pygui.get_style().item_inner_spacing[0]
        pygui.push_button_repeat(True)
        if pygui.arrow_button("##left", pygui.DIR_LEFT):
            widget.general_counter -= 1
        pygui.same_line(0, spacing)
        if pygui.arrow_button("##right", pygui.DIR_RIGHT):
            widget.general_counter += 1
        pygui.pop_button_repeat()
        pygui.same_line()
        pygui.text(str(widget.general_counter))

        # Tooltips

        pygui.text("Tooltips:")
        pygui.same_line()
        pygui.small_button("Button")
        if pygui.is_item_hovered():
            pygui.set_tooltip("I am a tooltip")
        
        pygui.same_line()
        pygui.small_button("Fancy")
        if pygui.is_item_hovered() and pygui.begin_tooltip():
            pygui.text("I am a fancy tooltip")
            arr = [0.6, 0.1, 1.0, 0.5, 0.92, 0.1, 0.2]
            pygui.plot_lines("Curve", arr)
            pygui.text("Sin(time) = {}".format(math.sin(time.time())))
            pygui.end_tooltip()
        
        pygui.same_line()
        pygui.small_button("Delayed")
        if pygui.is_item_hovered(pygui.HOVERED_FLAGS_DELAY_NORMAL):
            pygui.set_tooltip("I am a tooltip with a delay")
        
        pygui.same_line()
        help_marker("Tooltip are created by using the IsItemHovered() function over any kind of item.")

        pygui.label_text("label", "Value")

        pygui.separator_text("Inputs")

        pygui.input_text("input text", widget.inputs_str0)
        pygui.same_line()
        help_marker("USER:\n"
            "Hold SHIFT or use mouse to select text.\n"
            "CTRL+Left/Right to word jump.\n"
            "CTRL+A or Double-Click to select all.\n"
            "CTRL+X,CTRL+C,CTRL+V clipboard.\n"
            "CTRL+Z,CTRL+Y undo/redo.\n"
            "ESCAPE to revert.\n\n"
            "PROGRAMMER:\n"
            "You can use the ImGuiInputTextFlags_CallbackResize facility if you need to wire InputText() "
            "to a dynamic string type. See misc/cpp/imgui_stdlib.h for an example (this is not demonstrated "
            "in imgui_demo.cpp)."
        )

        pygui.input_text_with_hint("input text (w/ hint)", "enter text here", widget.inputs_str1)
        pygui.input_int("input int", widget.inputs_i0)
        pygui.input_float("input float", widget.inputs_f0, 0.01, 1.0, "%.3f")
        pygui.input_double("input double", widget.inputs_d0, 0.01, 1.0, "%.8f")
        pygui.input_float("input scientific", widget.inputs_f1, 0, 0, "%e")
        pygui.input_float2("input float2", widget.inputs_vec4a)
        pygui.input_float3("input float3", widget.inputs_vec4a)
        pygui.input_float4("input float4", widget.inputs_vec4a)

        pygui.separator_text("Drags")

        pygui.drag_int("drag int", widget.drag_i1, 1)
        pygui.same_line()
        help_marker(
            "Click and drag to edit value.\n"
            "Hold SHIFT/ALT for faster/slower edit.\n"
            "Double-click or CTRL+click to input value."
        )
        pygui.drag_int("drag int 0..100", widget.drag_i2, 1, 0, 100, "%d%%", pygui.SLIDER_FLAGS_ALWAYS_CLAMP)
        pygui.drag_float("drag float", widget.drag_f1, 0.005)
        pygui.drag_float("drag small float", widget.drag_f2, 0.0001, 0, 0, "%.06f ns")

        pygui.separator_text("Sliders")

        pygui.slider_int("slider int", widget.sliders_i1, -1, 3)
        pygui.same_line()
        help_marker("CTRL+click to input value.")
        pygui.slider_float("slider float", widget.sliders_f1, 0, 1, "ratio = %.3f")
        pygui.slider_float("slider float (log)", widget.sliders_f2, -10, 10, "%.4f", pygui.SLIDER_FLAGS_LOGARITHMIC)
        pygui.slider_angle("slider angle", widget.sliders_angle)

        # Using the format string to display a name instead of an integer.
        # Here we completely omit '%d' from the format string, so it'll only display a name.
        # This technique can also be used with DragInt().
        elements = ["Fire", "Earth", "Air", "Water"]
        elem_name = elements[widget.sliders_elem.value] if 0 <= widget.sliders_elem.value < len(elements) else "Unknown"
        pygui.slider_int("slider enum", widget.sliders_elem, 0, len(elements) - 1, elem_name)
        pygui.same_line()
        help_marker("Using the format string parameter to display a name instead of the underlying integer.")
        
        pygui.separator_text("Selectors/Pickers")

        pygui.color_edit3("color 1", widget.picker_col1)
        pygui.same_line()
        help_marker(
            "Click on the color square to open a color picker.\n"
            "Click and hold to use drag and drop.\n"
            "Right-click on the color square to show options.\n"
            "CTRL+click on individual component to input value.\n"
        )
        pygui.color_edit4("color 2", widget.picker_col2)

        # Using the _simplified_ one-liner Combo() api here
        # See "Combo" section for examples of how to use the more flexible BeginCombo()/EndCombo() api.
        # I dunno man, it's pretty clean here in python...
        # I added some extra unicode characters to test that they copy correctly.
        items = ["AAAA", "BBBB", "CCCC", "DDDD", "EEEE", "FFFF", "GGGG", "HHHH", "IIIIIII", "JJJJ", "KKKKKKK", "😀😁😂"]
        pygui.combo("combo", widget.combo_item_current, items)
        pygui.same_line()
        help_marker("Using the simplified one-liner Combo API here.\nRefer to the \"Combo\" section below for an explanation of how to use the more flexible and general BeginCombo/EndCombo API.")
        
        items_list = ["Apple", "Banana", "Cherry", "Kiwi", "Mango", "Orange", "Pineapple", "Strawberry", "Watermelon", "😀😁😂"]
        pygui.list_box("listbox", widget.list_item_current, items_list, 4)
        pygui.same_line()
        help_marker(
            "Using the simplified one-liner ListBox API here.\nRefer to the \"List boxes\" section below for an explanation of how to use the more flexible and general BeginListBox/EndListBox API."
        )

        pygui.tree_pop()
    
    if pygui.tree_node("Trees"):
        if pygui.tree_node("Basic trees"):
            for i in range(5):
                if i == 0:
                    pygui.set_next_item_open(True, pygui.COND_ONCE)
                
                if pygui.tree_node("Child {}".format(i)):
                    pygui.text("blah blah")
                    pygui.same_line()
                    if pygui.small_button("button"):
                        pass
                    pygui.tree_pop()
            pygui.tree_pop()

        if pygui.tree_node("Advanced, with Selectable nodes"):
            help_marker(
                "This is a more typical looking tree with selectable nodes.\n"
                "Click to select, CTRL+Click to toggle, click on arrows or double-click to open."
            )
            pygui.checkbox_flags("ImGuiTreeNodeFlags_OpenOnArrow",       widget.tree_base_flags, pygui.TREE_NODE_FLAGS_OPEN_ON_ARROW)
            pygui.checkbox_flags("ImGuiTreeNodeFlags_OpenOnDoubleClick", widget.tree_base_flags, pygui.TREE_NODE_FLAGS_OPEN_ON_DOUBLE_CLICK)
            pygui.checkbox_flags("ImGuiTreeNodeFlags_SpanAvailWidth",    widget.tree_base_flags, pygui.TREE_NODE_FLAGS_SPAN_AVAIL_WIDTH)
            pygui.same_line()
            help_marker("Extend hit area to all available width instead of allowing more items to be laid out after the node.")
            pygui.checkbox_flags("ImGuiTreeNodeFlags_SpanFullWidth",     widget.tree_base_flags, pygui.TREE_NODE_FLAGS_SPAN_FULL_WIDTH)
            pygui.checkbox("Align label with current X position", widget.tree_align_label_with_current_x_position)
            pygui.checkbox("Test tree node as drag source", widget.tree_test_drag_and_drop)
            pygui.text("Hello!")
            if widget.tree_align_label_with_current_x_position:
                pygui.unindent(pygui.get_tree_node_to_label_spacing())
            
            # 'selection_mask' is dumb representation of what may be user-side selection state.
            #  You may retain selection state inside or outside your objects in whatever format you see fit.
            # 'node_clicked' is temporary storage of what node we have clicked to process selection at the end
            #  of the loop. May be a pointer to your own node type, etc.
            node_clicked = -1
            for i in range(6):
                node_flags = widget.tree_base_flags.value
                is_selected = (widget.tree_selection_mask.value & (1 << i)) != 0
                if is_selected:
                    node_flags |= pygui.TREE_NODE_FLAGS_SELECTED
                if i < 3:
                    # Items 0..2 are Tree Node
                    node_open = pygui.tree_node(f"Selectable Node {i}", node_flags)
                    if pygui.is_item_clicked() and not pygui.is_item_toggled_open():
                        node_clicked = i
                    if widget.tree_test_drag_and_drop and pygui.begin_drag_drop_source():
                        pygui.set_drag_drop_payload("_TREENODE", None, 0)
                        pygui.text("This is a drag and drop source")
                        pygui.end_drag_drop_source()
                    if node_open:
                        pygui.bullet_text("Blah blah\nBlah Blah")
                        pygui.tree_pop()
                else:
                    # Items 3..5 are Tree Leaves
                    # The only reason we use TreeNode at all is to allow selection of the leaf. Otherwise we can
                    # use BulletText() or advance the cursor by GetTreeNodeToLabelSpacing() and call Text().
                    node_flags |= pygui.TREE_NODE_FLAGS_LEAF | pygui.TREE_NODE_FLAGS_NO_TREE_PUSH_ON_OPEN # ImGuiTreeNodeFlags_Bullet
                    pygui.tree_node(f"Selectable Leaf {i}", node_flags)
                    if pygui.is_item_clicked() and not pygui.is_item_toggled_open():
                        node_clicked = i
                    if widget.tree_test_drag_and_drop and pygui.begin_drag_drop_source():
                        pygui.set_drag_drop_payload("_TREENODE", None, 0)
                        pygui.text("This is a drag and drop source")
                        pygui.end_drag_drop_source()
            
            if node_clicked != -1:
                # Update selection state
                # (process outside of tree loop to avoid visual inconsistencies during the clicking frame)
                if pygui.get_io().key_ctrl:
                    widget.tree_selection_mask.value ^= (1 << node_clicked)              # CTRL+click to toggle
                else: #elif not (static.widgets_tree_selection_mask & (1 << node_clicked)) # Depending on selection behavior you want, may want to preserve selection when clicking on item that is part of the selection
                    widget.tree_selection_mask.value = (1 << node_clicked)               # Click to single-select

            if widget.tree_align_label_with_current_x_position:
                pygui.indent(pygui.get_tree_node_to_label_spacing())
            pygui.tree_pop()
        pygui.tree_pop()
    
    if pygui.tree_node("Collapsing Headers"):
        pygui.checkbox("Show 2nd header", widget.header_closable_group)
        if pygui.collapsing_header("Header", pygui.TREE_NODE_FLAGS_NONE):
            pygui.text("IsItemHovered: {}".format(pygui.is_item_hovered()))
            for i in range(5):
                pygui.text(f"Some content {i}")
        
        if pygui.collapsing_header_bool_ptr("Header with a close button", widget.header_closable_group):
            pygui.text("IsItemHovered: {}".format(pygui.is_item_hovered()))
            for i in range(5):
                pygui.text(f"more content {i}")
        pygui.tree_pop()
    
    if pygui.tree_node("Bullets"):
        pygui.bullet_text("Bullet point 1")
        pygui.bullet_text("Bullet point 2\nOn multiple lines")
        if pygui.tree_node("Tree node"):
            pygui.bullet_text("Another bullet point")
            pygui.tree_pop()
        
        pygui.bullet()
        pygui.text("Bullet point 3 (two calls)")
        pygui.bullet()
        pygui.small_button("Button")
        pygui.tree_pop()

    if pygui.tree_node("Text"):
        if pygui.tree_node("Colorful text"):
            pygui.text_colored((1, 0, 1, 1), "Pink")
            pygui.text_colored((1, 1, 0, 1), "Yellow")
            pygui.text_disabled("Disabled")
            pygui.same_line()
            help_marker("The TextDisabled color is stored in ImGuiStyle.")
            pygui.tree_pop()
        
        if pygui.tree_node("Word Wrapping"):
            pygui.text_wrapped(
                "This text should automatically wrap on the edge of the window. The current implementation "
                "for text wrapping follows simple rules suitable for English and possibly other languages.")
            pygui.spacing()

            pygui.slider_float("Wrap width", widget.text_wrap_width, -20, 600, "%.0f")

            draw_list = pygui.get_window_draw_list()
            for n in range(2):
                pygui.text(f"Test paragraph {n}")
                pos = pygui.get_cursor_screen_pos()
                marker_min = (pos[0] + widget.text_wrap_width.value, pos[1])
                marker_max = (pos[0] + widget.text_wrap_width.value + 10, pos[1] + pygui.get_text_line_height())
                pygui.push_text_wrap_pos(pygui.get_cursor_pos()[0] + widget.text_wrap_width.value)
                if n == 0:
                    pygui.text("The lazy dog is a good dog. This paragraph should fit within {} pixels. Testing a 1 character word. The quick brown fox jumps over the lazy dog.".format(
                        widget.text_wrap_width.value
                    ))
                else:
                    pygui.text("aaaaaaaa bbbbbbbb, c cccccccc,dddddddd. d eeeeeeee   ffffffff. gggggggg!hhhhhhhh")
                
                draw_list.add_rect(pygui.get_item_rect_min(), pygui.get_item_rect_max(), pygui.IM_COL32(255, 255, 0, 255))
                draw_list.add_rect_filled(marker_min, marker_max, pygui.IM_COL32(255, 0, 255, 255))
                pygui.pop_text_wrap_pos()
            pygui.tree_pop()

        if pygui.tree_node("UTF-8 Text"):
            # UTF-8 test with Japanese characters
            # (Needs a suitable font? Try "Google Noto" or "Arial Unicode". See docs/FONTS.md for details.)
            # - From C++11 you can use the u8"my text" syntax to encode literal strings as UTF-8
            # - For earlier compiler, you may be able to encode your sources as UTF-8 (e.g. in Visual Studio, you
            #   can save your source files as 'UTF-8 without signature').
            # - FOR THIS DEMO FILE ONLY, BECAUSE WE WANT TO SUPPORT OLD COMPILERS, WE ARE *NOT* INCLUDING RAW UTF-8
            #   CHARACTERS IN THIS SOURCE FILE. Instead we are encoding a few strings with hexadecimal constants.
            #   Don't do this in your application! Please use u8"text in any language" in your application!
            # Note that characters values are preserved even by InputText() if the font cannot be displayed,
            # so you can safely copy & paste garbled characters into another application.
            pygui.text_wrapped(
                "CJK text will only appear if the font was loaded with the appropriate CJK character ranges. "
                "Call io.Fonts->AddFontFromFileTTF() manually to load extra character ranges. "
                "Read docs/FONTS.md for details.")
            # Normally we would use u8"blah blah" with the proper characters directly in the string.
            pygui.text("Hiragana: かきくけこ (kakikukeko)")
            pygui.text("Kanjis: 日本語 (nihongo)")
            pygui.input_text("UTF-8 input", widget.text_utf8_buf)
            pygui.tree_pop()
        pygui.tree_pop()

    if pygui.tree_node("Images"):
        if pygui.tree_node("Custom Pygui Image"):
            pygui.image(
                widget.instance().widgets_image_texture,
                (widget.instance().widgets_image.width / 2,
                widget.instance().widgets_image.height / 2))
            pygui.tree_pop()
        
        if pygui.tree_node("ImGui Demo"):
            io = pygui.get_io()
            pygui.text_wrapped(
                "Below we are displaying the font texture (which is the only texture we have access to in this demo). "
                "Use the 'ImTextureID' type as storage to pass pointers or identifier to your own texture data. "
                "Hover the texture for a zoomed view!")
            
            my_tex_id: int = io.fonts.tex_id
            my_tex_w = io.fonts.tex_width
            my_tex_h = io.fonts.tex_height

            pygui.checkbox("Use Text Color for Tint", widget.image_use_text_color_for_tint)
            pygui.text("{}x{}".format(my_tex_w, my_tex_h))
            pos = pygui.get_cursor_screen_pos()
            uv_min = (0, 0) # Top-left
            uv_max = (1, 1) # Lower-right
            if widget.image_use_text_color_for_tint:
                tint_col = pygui.get_style_color_vec4(pygui.COL_TEXT)
            else:
                tint_col = (1, 1, 1, 1)
            border_col = pygui.get_style_color_vec4(pygui.COL_BORDER)
            pygui.image(my_tex_id, (my_tex_w, my_tex_h), uv_min, uv_max, tint_col, border_col)

            if pygui.is_item_hovered() and pygui.begin_tooltip():
                region_sz = 32
                region_x = io.mouse_pos[0] - pos[0] - region_sz * 0.5
                region_y = io.mouse_pos[1] - pos[1] - region_sz * 0.5
                zoom = 4
                if region_x < 0:
                    region_x = 0
                elif region_x > my_tex_w - region_sz:
                    region_x = my_tex_w - region_sz
                
                if region_y < 0:
                    region_y = 0
                elif region_y > my_tex_h - region_sz:
                    region_y = my_tex_h - region_sz
                
                pygui.text("Min: ({:.2f}, {:.2f})".format(region_x, region_y))
                pygui.text("Max: ({:.2f}, {:.2f})".format(region_x + region_sz, region_y + region_sz))
                uv0 = (region_x) / my_tex_w, (region_y) / my_tex_h
                uv1 = (region_x + region_sz) / my_tex_w, (region_y + region_sz) / my_tex_h
                pygui.image(my_tex_id, (region_sz * zoom, region_sz * zoom), uv0, uv1, tint_col, border_col)
                pygui.end_tooltip()
            
            pygui.text_wrapped("And now some textured buttons..")
            for i in range(8):
                # UV coordinates are often (0.0f, 0.0f) and (1.0f, 1.0f) to display an entire textures.
                # Here are trying to display only a 32x32 pixels area of the texture, hence the UV computation.
                # Read about UV coordinates here: https://github.com/ocornut/imgui/wiki/Image-Loading-and-Displaying-Examples
                pygui.push_id(i)
                if i > 0:
                    pygui.push_style_var(pygui.STYLE_VAR_FRAME_PADDING, (i - 1, i - 1))
                size = (32, 32)
                uv0 = (0, 0)
                uv1 = (32 / my_tex_w, 32 / my_tex_h)
                bg_col = (0, 0, 0, 1)
                tint_col = (1, 1, 1, 1)
                if pygui.image_button("", my_tex_id, size, uv0, uv1, bg_col, tint_col):
                    widget.image_pressed_count += 1
                if i > 0:
                    pygui.pop_style_var()
                pygui.pop_id()
                pygui.same_line()
            
            pygui.new_line()
            pygui.text("Pressed {} times.".format(widget.image_pressed_count))
            pygui.tree_pop()

        pygui.tree_pop()
    
    if pygui.tree_node("Combo"):
        # Combo Boxes are also called "Dropdown" in other systems
        # Expose flags as checkbox for the demo
        pygui.checkbox_flags("ImGuiComboFlags_PopupAlignLeft", widget.combo_flags, pygui.COMBO_FLAGS_POPUP_ALIGN_LEFT)
        pygui.same_line()
        help_marker("Only makes a difference if the popup is larger than the combo")
        if pygui.checkbox_flags("ImGuiComboFlags_NoArrowButton", widget.combo_flags, pygui.COMBO_FLAGS_NO_ARROW_BUTTON):
            widget.combo_flags.value &= ~pygui.COMBO_FLAGS_NO_PREVIEW
        if pygui.checkbox_flags("ImGuiComboFlags_NoPreview", widget.combo_flags, pygui.COMBO_FLAGS_NO_PREVIEW):
            widget.combo_flags.value &= ~pygui.COMBO_FLAGS_NO_ARROW_BUTTON
        
        # Using the generic BeginCombo() API, you have full control over how to display the combo contents.
        # (your selection data could be an index, a pointer to the object, an id for the object, a flag intrusively
        # stored in the object itself, etc.)
        items = ["AAAA", "BBBB", "CCCC", "DDDD", "EEEE", "FFFF", "GGGG", "HHHH", "IIII", "JJJJ", "KKKK", "LLLLLLL", "MMMM", "OOOOOOO"]
        combo_preview_value = items[widget.combo_item_current_idx.value]
        if pygui.begin_combo("combo 1", combo_preview_value, widget.combo_flags.value):
            for n in range(len(items)):
                is_selected = widget.combo_item_current_idx.value == n
                if pygui.selectable(items[n], is_selected):
                    widget.combo_item_current_idx.value = n
                
                # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                if is_selected:
                    pygui.set_item_default_focus()
            
            pygui.end_combo()
        
        # Simplified one-liner Combo() API, using values packed in a single constant string
        # This is a convenience for when the selection set is small and known at compile-time.
        # Pygui note: Obviously this doesn't really make sense in pygui. Just use a list.
        pygui.combo("combo 2 (one-liner)", widget.combo_item_current_2, ["aaaa", "bbbb", "cccc", "dddd", "eeee"])

        # Simplified one-liner Combo() using an array of const char*
        # This is not very useful (may obsolete): prefer using BeginCombo()/EndCombo() for full control.
        # If the selection isn't within 0..count, Combo won't display a preview
        pygui.combo("combo 3 (array)", widget.combo_item_current_3, items)

        # Simplified one-liner Combo() using an accessor function
        def item_getter(data, n: int, out_str: pygui.String) -> bool:
            out_str.value = data[n]
            return True
        pygui.combo_callback("combo 4 (function)", widget.combo_item_current_4, item_getter, items, len(items))
        pygui.tree_pop()

    if pygui.tree_node("List boxes"):
        # Using the generic BeginListBox() API, you have full control over how to display the combo contents.
        # (your selection data could be an index, a pointer to the object, an id for the object, a flag intrusively
        # stored in the object itself, etc.)
        items = ["AAAA", "BBBB", "CCCC", "DDDD", "EEEE", "FFFF", "GGGG", "HHHH", "IIII", "JJJJ", "KKKK", "LLLLLLL", "MMMM", "OOOOOOO"]
        if pygui.begin_list_box("listbox 1"):
            for n in range(len(items)):
                is_selected = widget.list_box_item_current_idx == n
                if pygui.selectable(items[n], is_selected):
                    widget.list_box_item_current_idx = n
                
                # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                if is_selected:
                    pygui.set_item_default_focus()
                
            pygui.end_list_box()

        pygui.text("Full-width:")
        if pygui.begin_list_box("##listbox 2", (-pygui.FLT_MIN, 5 * pygui.get_text_line_height_with_spacing())):
            for n in range(len(items)):
                is_selected = widget.list_box_item_current_idx == n
                if pygui.selectable(items[n], is_selected):
                    widget.list_box_item_current_idx = n
                
                # Set the initial focus when opening the combo (scrolling + keyboard navigation focus)
                if is_selected:
                    pygui.set_item_default_focus()
            pygui.end_list_box()
        
        pygui.tree_pop()
    
    if pygui.tree_node("Selectables"):
        if pygui.tree_node("Basic"):
            pygui.selectable_bool_ptr("1. I am selectable", widget.select_selection[0])
            pygui.selectable_bool_ptr("2. I am selectable", widget.select_selection[1])
            pygui.text("(I am not selectable)")
            pygui.selectable_bool_ptr("4. I am selectable", widget.select_selection[3])
            if pygui.selectable("5. I am double clickable", widget.select_selection[4], pygui.SELECTABLE_FLAGS_ALLOW_DOUBLE_CLICK):
                if pygui.is_mouse_double_clicked(pygui.MOUSE_BUTTON_LEFT):
                    widget.select_selection[4].value = not widget.select_selection[4].value
            pygui.tree_pop()
        
        if pygui.tree_node("Selection State: Single Selection"):
            for n in range(5):
                if pygui.selectable(f"Object {n}", widget.select_single_state_selected == n):
                    widget.select_single_state_selected = n
            pygui.tree_pop()

        if pygui.tree_node("Selection State: Multiple Selection"):
            help_marker("Hold CTRL and click to select multiple items.")
            for n in range(5):
                if pygui.selectable(f"Object {n}", widget.select_multi_state_selection[n]):
                    if not pygui.get_io().key_ctrl:
                        widget.select_multi_state_selection = [pygui.Bool(False) for _ in range(len(widget.select_multi_state_selection))]
                    widget.select_multi_state_selection[n].value = not widget.select_multi_state_selection[n].value
            pygui.tree_pop()
        
        if pygui.tree_node("Rendering more text into the same line"):
            pygui.selectable_bool_ptr("main.c", widget.select_render_selected[0])
            pygui.same_line(300)
            pygui.text(" 2,345 bytes")

            pygui.selectable_bool_ptr("Hello.cpp", widget.select_render_selected[1])
            pygui.same_line(300)
            pygui.text("12,245 bytes")
            
            pygui.selectable_bool_ptr("Hello.h", widget.select_render_selected[2])
            pygui.same_line(300)
            pygui.text(" 2,345 bytes")
            pygui.tree_pop()
        
        if pygui.tree_node("In columns"):
            if pygui.begin_table("split1", 3, pygui.TABLE_FLAGS_RESIZABLE | pygui.TABLE_FLAGS_NO_SAVED_SETTINGS | pygui.TABLE_FLAGS_BORDERS):
                for i in range(10):
                    pygui.table_next_column()
                    pygui.selectable_bool_ptr(f"Item {i}", widget.select_column_selected[i])
                pygui.end_table()
            pygui.spacing()
            if pygui.begin_table("split2", 3, pygui.TABLE_FLAGS_RESIZABLE | pygui.TABLE_FLAGS_NO_SAVED_SETTINGS | pygui.TABLE_FLAGS_BORDERS):
                for i in range(10):
                    pygui.table_next_row()
                    pygui.table_next_column()
                    pygui.selectable_bool_ptr(f"Item {i}", widget.select_column_selected[i], pygui.SELECTABLE_FLAGS_SPAN_ALL_COLUMNS)
                    pygui.table_next_column()
                    pygui.text("Some other contents")
                    pygui.table_next_column()
                    pygui.text("123456")
                pygui.end_table()
            pygui.tree_pop()
        
        if pygui.tree_node("Grid"):
            # Add in a bit of silly fun...
            current_time = pygui.get_time()
            winning_state = not any(0 in inner for inner in widget.select_grid_selected)
            if winning_state:
                pygui.push_style_var(
                    pygui.STYLE_VAR_SELECTABLE_TEXT_ALIGN,
                    (0.5 + 0.5 * math.cos(current_time * 2), 0.5 + 0.5 * math.sin(current_time * 3))
                )
            for y in range(4):
                for x in range(4):
                    if x > 0:
                        pygui.same_line()
                    pygui.push_id(y * 4 + x)
                    if pygui.selectable("Sailor", bool(widget.select_grid_selected[y][x]), 0, (50, 50)):
                        widget.select_grid_selected[y][x] ^= 1
                        if x > 0:
                            widget.select_grid_selected[y][x - 1] ^= 1
                        if x < 3:
                            widget.select_grid_selected[y][x + 1] ^= 1
                        if y > 0:
                            widget.select_grid_selected[y - 1][x] ^= 1
                        if y < 3:
                            widget.select_grid_selected[y + 1][x] ^= 1
                    pygui.pop_id()
                
            if winning_state:
                pygui.pop_style_var()
            pygui.tree_pop()

        if pygui.tree_node("Alignment"):
            help_marker(
                "By default, Selectables uses style.SelectableTextAlign but it can be overridden on a per-item "
                "basis using PushStyleVar(). You'll probably want to always keep your default situation to "
                "left-align otherwise it becomes difficult to layout multiple items on a same line")
            for y in range(3):
                for x in range(3):
                    alignment = (x / 2, y / 2)
                    if x > 0:
                        pygui.same_line()
                    pygui.push_style_var(pygui.STYLE_VAR_SELECTABLE_TEXT_ALIGN, alignment)
                    pygui.selectable_bool_ptr(
                        "({:.1f}, {:.1f})".format(alignment[0], alignment[1]),
                        widget.select_allign_selected[3 * y + x],
                        pygui.SELECTABLE_FLAGS_NONE,
                        (80, 80)
                    )
                    pygui.pop_style_var()
            pygui.tree_pop()
        pygui.tree_pop()

    if pygui.tree_node("Tabs"):
        if pygui.tree_node("Basic"):
            tab_bar_flags = pygui.TAB_BAR_FLAGS_NONE
            if pygui.begin_tab_bar("MyTabBar", tab_bar_flags):
                if pygui.begin_tab_item("Avocado"):
                    pygui.text("This is the Avocado tab!\nblah blah blah blah blah")
                    pygui.end_tab_item()
                if pygui.begin_tab_item("Broccoli"):
                    pygui.text("This is the Broccoli tab!\nblah blah blah blah blah")
                    pygui.end_tab_item()
                if pygui.begin_tab_item("Cucumber"):
                    pygui.text("This is the Cucumber tab!\nblah blah blah blah blah")
                    pygui.end_tab_item()
                pygui.end_tab_bar()
            pygui.separator()
            pygui.tree_pop()
        
        if pygui.tree_node("Advanced & Close Button"):
            pygui.checkbox_flags("ImGuiTabBarFlags_Reorderable", widget.tab_tab_bar_flags, pygui.TAB_BAR_FLAGS_REORDERABLE)
            pygui.checkbox_flags("ImGuiTabBarFlags_AutoSelectNewTabs", widget.tab_tab_bar_flags, pygui.TAB_BAR_FLAGS_AUTO_SELECT_NEW_TABS)
            pygui.checkbox_flags("ImGuiTabBarFlags_TabListPopupButton", widget.tab_tab_bar_flags, pygui.TAB_BAR_FLAGS_TAB_LIST_POPUP_BUTTON)
            pygui.checkbox_flags("ImGuiTabBarFlags_NoCloseWithMiddleMouseButton", widget.tab_tab_bar_flags, pygui.TAB_BAR_FLAGS_NO_CLOSE_WITH_MIDDLE_MOUSE_BUTTON)
            if widget.tab_tab_bar_flags.value & pygui.TAB_BAR_FLAGS_FITTING_POLICY_MASK == 0:
                widget.tab_tab_bar_flags.value |= pygui.TAB_BAR_FLAGS_FITTING_POLICY_DEFAULT
            if pygui.checkbox_flags("ImGuiTabBarFlags_FittingPolicyResizeDown", widget.tab_tab_bar_flags, pygui.TAB_BAR_FLAGS_FITTING_POLICY_RESIZE_DOWN):
                widget.tab_tab_bar_flags.value &= ~(pygui.TAB_BAR_FLAGS_FITTING_POLICY_MASK ^ pygui.TAB_BAR_FLAGS_FITTING_POLICY_RESIZE_DOWN)
            if pygui.checkbox_flags("ImGuiTabBarFlags_FittingPolicyScroll", widget.tab_tab_bar_flags, pygui.TAB_BAR_FLAGS_FITTING_POLICY_SCROLL):
                widget.tab_tab_bar_flags.value &= ~(pygui.TAB_BAR_FLAGS_FITTING_POLICY_MASK ^ pygui.TAB_BAR_FLAGS_FITTING_POLICY_SCROLL)

            # Tab Bar
            names = ["Artichoke", "Beetroot", "Celery", "Daikon"]
            for n in range(len(widget.tab_opened)):
                if n > 0:
                    pygui.same_line()
                pygui.checkbox(names[n], widget.tab_opened[n])

            # Passing a bool* to BeginTabItem() is similar to passing one to Begin():
            # the underlying bool will be set to false when the tab is closed.
            if pygui.begin_tab_bar("MyTabBar", widget.tab_tab_bar_flags.value):
                for n in range(len(widget.tab_opened)):
                    if widget.tab_opened[n] and pygui.begin_tab_item(names[n], widget.tab_opened[n], pygui.TAB_BAR_FLAGS_NONE):
                        pygui.text("This is the {} tab!".format(names[n]))
                        if n & 1:
                            pygui.text("I am an odd tab.")
                        pygui.end_tab_item()
                pygui.end_tab_bar()
            pygui.separator()
            pygui.tree_pop()

        if pygui.tree_node("TabItemButton & Leading/Trailing flags"):
            if widget.tab_next_tab_id == 0: # Initialize with some default tabs
                for i in range(3):
                    widget.tab_active_tabs.append(widget.tab_next_tab_id)
                    widget.tab_next_tab_id += 1
            
            # TabItemButton() and Leading/Trailing flags are distinct features which we will demo together.
            # (It is possible to submit regular tabs with Leading/Trailing flags, or TabItemButton tabs without Leading/Trailing flags...
            # but they tend to make more sense together)
            pygui.checkbox("Show Leading TabItemButton()", widget.tab_show_leading_button)
            pygui.checkbox("Show Trailing TabItemButton()", widget.tab_show_trailing_button)
            
            # Expose some other flags which are useful to showcase how they interact with Leading/Trailing tabs
            pygui.checkbox_flags("ImGuiTabBarFlags_TabListPopupButton", widget.tab_tab_bar_flags, pygui.TAB_BAR_FLAGS_TAB_LIST_POPUP_BUTTON)
            if pygui.checkbox_flags("ImGuiTabBarFlags_FittingPolicyResizeDown", widget.tab_tab_bar_flags, pygui.TAB_BAR_FLAGS_FITTING_POLICY_RESIZE_DOWN):
                widget.tab_tab_bar_flags.value &= ~(pygui.TAB_BAR_FLAGS_FITTING_POLICY_MASK ^ pygui.TAB_BAR_FLAGS_FITTING_POLICY_RESIZE_DOWN)
            if pygui.checkbox_flags("ImGuiTabBarFlags_FittingPolicyScroll", widget.tab_tab_bar_flags, pygui.TAB_BAR_FLAGS_FITTING_POLICY_SCROLL):
                widget.tab_tab_bar_flags.value &= ~(pygui.TAB_BAR_FLAGS_FITTING_POLICY_MASK ^ pygui.TAB_BAR_FLAGS_FITTING_POLICY_SCROLL)

            if pygui.begin_tab_bar("MyTabBar", widget.tab_tab_bar_flags.value):
                # Demo a Leading TabItemButton(): click the "?" button to open a menu
                if widget.tab_show_leading_button:
                    if pygui.tab_item_button("?", pygui.TAB_ITEM_FLAGS_LEADING | pygui.TAB_BAR_FLAGS_NO_TOOLTIP):
                        pygui.open_popup("MyHelpMenu")
                if pygui.begin_popup("MyHelpMenu"):
                    pygui.selectable("Hello!")
                    pygui.end_popup()

                # Demo Trailing Tabs: click the "+" button to add a new tab (in your app you may want to use a font icon instead of the "+")
                # Note that we submit it before the regular tabs, but because of the ImGuiTabItemFlags_Trailing flag it will always appear at the end.
                if widget.tab_show_trailing_button:
                    if pygui.tab_item_button("+", pygui.TAB_ITEM_FLAGS_TRAILING | pygui.TAB_BAR_FLAGS_NO_TOOLTIP):
                        widget.tab_active_tabs.append(widget.tab_next_tab_id) # Add new tab
                        widget.tab_next_tab_id += 1
                
                # Submit our regular tabs
                n = 0
                while n < len(widget.tab_active_tabs):
                    open_ = pygui.Bool(True)
                    name = f"{widget.tab_active_tabs[n]:04d}"
                    if pygui.begin_tab_item(name, open_, pygui.TAB_ITEM_FLAGS_NONE):
                        pygui.text(f"This is the {name} tab!")
                        pygui.end_tab_item()
                    
                    if not open_:
                        widget.tab_active_tabs.pop(n)
                    else:
                        n += 1
                
                pygui.end_tab_bar()
            pygui.separator()
            pygui.tree_pop()
        pygui.tree_pop()

    if pygui.tree_node("Plotting"):
        pygui.checkbox("Animate", widget.plotting_animate)

        # Plot as lines and plot as histogram
        pygui.plot_lines("Frame Times", widget.plotting_arr)
        pygui.plot_histogram("Histogram", widget.plotting_arr, 0, None, 0, 1, (0, 80))

        # Fill an array of contiguous float values to plot
        # Tip: If your float aren't contiguous but part of a structure, you can pass a pointer to your first float
        # and the sizeof() of your structure in the "stride" parameter.
        if not widget.plotting_animate or widget.plotting_refresh_time == 0:
            widget.plotting_refresh_time = time.time()
        
        while widget.plotting_refresh_time < time.time():
            widget.plotting_values[widget.plotting_values_offset] = math.cos(
                widget.plotting_phase
            )
            widget.plotting_values_offset = (widget.plotting_values_offset + 1) % len(widget.plotting_values)
            widget.plotting_phase += 0.1 * widget.plotting_values_offset
            widget.plotting_refresh_time += 1 / 60

        average = 0
        for n in range(len(widget.plotting_values)):
            average += widget.plotting_values[n]
        average /= len(widget.plotting_values)
        pygui.plot_lines(
            "Lines",
            widget.plotting_values,
            widget.plotting_values_offset,
            "avg {:.6f}".format(average),
            -1,
            1,
            (0, 80)
        )

        # This section has been modified to use pythonic functions and methods
        # rather than the values_getter moethod in the demo.
        pygui.separator_text("Functions")
        pygui.set_next_item_width(pygui.get_font_size() * 8)
        pygui.combo("func", widget.plotting_func_type, ["Sin", "Saw"])
        pygui.same_line()
        pygui.slider_int("Sample count", widget.plotting_display_count, 1, 400)

        def saw(value: int):
            return 1 if value & 1 == 0 else -1

        if widget.plotting_func_type.value == 0:
            values = [math.sin(i / 10) for i in range(widget.plotting_display_count.value)]
        else:
            values = [saw(i) for i in range(widget.plotting_display_count.value)]
        
        pygui.plot_lines("Lines", values, 0, None, -1, 1, (0, 80))
        pygui.plot_histogram("Histogram", values, 0, None, -1, 1, (0, 80))
        pygui.separator()

        if widget.plotting_animate:
            widget.plotting_progress += widget.plotting_progress_dir * 0.4 * pygui.get_io().delta_time
            if widget.plotting_progress >= 1.1:
                widget.plotting_progress = 1.1
                widget.plotting_progress_dir *= -1
            if widget.plotting_progress <= -0.1:
                widget.plotting_progress = -0.1
                widget.plotting_progress_dir *= -1

        # Typically we would use ImVec2(-1.0f,0.0f) or ImVec2(-FLT_MIN,0.0f) to use all available width,
        # or ImVec2(width,0.0f) for a specified width. ImVec2(0.0f,0.0f) uses ItemWidth.
        pygui.progress_bar(widget.plotting_progress, (0, 0))
        pygui.same_line(0, pygui.get_style().item_inner_spacing[0])
        pygui.text("Progress Bar")
        
        progress_saturated = pygui.IM_CLAMP(widget.plotting_progress, 0, 1)
        pygui.progress_bar(widget.plotting_progress, (0, 0), "{}/{}".format(
            int(progress_saturated * 1753), 1753
        ))
        pygui.tree_pop()

    if pygui.tree_node("Color/Picker Widgets"):
        pygui.separator_text("Options")
        pygui.checkbox_flags("With Alpha Preview", widget.colour_flags, pygui.COLOR_EDIT_FLAGS_ALPHA_PREVIEW)
        pygui.checkbox_flags("With Half Alpha Preview", widget.colour_flags, pygui.COLOR_EDIT_FLAGS_ALPHA_PREVIEW_HALF)
        pygui.checkbox_flags("No Drag and Drop", widget.colour_flags, pygui.COLOR_EDIT_FLAGS_NO_DRAG_DROP)
        pygui.checkbox_flags("No Options Menu", widget.colour_flags, pygui.COLOR_EDIT_FLAGS_NO_OPTIONS)
        pygui.same_line()
        help_marker("Right-click on the individual color widget to show options.")
        pygui.checkbox_flags("With HDR", widget.colour_flags, pygui.COLOR_EDIT_FLAGS_HDR)
        pygui.same_line()
        help_marker("Currently all this does is to lift the 0..1 limits on dragging widgets.")
        misc_flags = widget.colour_flags.value
        
        pygui.separator_text("Inline color editor")
        pygui.text("Color widget:")
        pygui.same_line()
        help_marker(
            "Click on the color square to open a color picker.\n"
            "CTRL+click on individual component to input value.\n")
        pygui.color_edit3("MyColor##1", widget.colour_color, misc_flags)

        pygui.text("Color widget HSV with Alpha:")
        pygui.color_edit4("MyColor##2", widget.colour_color, pygui.COLOR_EDIT_FLAGS_DISPLAY_HSV | misc_flags)

        pygui.text("Color widget with Float Display:")
        pygui.color_edit4("MyColor##2f", widget.colour_color, pygui.COLOR_EDIT_FLAGS_FLOAT | misc_flags)
        
        pygui.text("Color button with Picker:")
        pygui.same_line()
        help_marker(
            "With the ImGuiColorEditFlags_NoInputs flag you can hide all the slider/text inputs.\n"
            "With the ImGuiColorEditFlags_NoLabel flag you can pass a non-empty label which will only "
            "be used for the tooltip and picker popup.")
        pygui.color_edit4("MyColor##3", widget.colour_color, pygui.COLOR_EDIT_FLAGS_NO_INPUTS | pygui.COLOR_EDIT_FLAGS_NO_LABEL | misc_flags)

        pygui.text("Color button with Custom Picker Popup:")

        # Generate a default palette. The palette will persist and can be edited.
        if widget.colour_saved_palette_init:
            for n in range(len(widget.colour_saved_palette)):
                widget.colour_saved_palette[n] = pygui.Vec4(*pygui.color_convert_hsv_to_rgb(
                    n / 31,
                    0.8,
                    0.8
                ))
                widget.colour_saved_palette[n].w = 1 # Alpha
            widget.colour_saved_palette_init.value = False
        
        open_popup = pygui.color_button("MyColor##3b", widget.colour_color.tuple(), misc_flags)
        pygui.same_line(0, pygui.get_style().item_inner_spacing[0])
        open_popup = open_popup or pygui.button("Palette")
        if open_popup:
            pygui.open_popup("mypicker")
            widget.colour_backup_color = widget.colour_color.copy()
        if pygui.begin_popup("mypicker"):
            pygui.text("MY CUSTOM COLOR PICKER WITH AN AMAZING PALETTE!")
            pygui.separator()
            pygui.color_picker4("##picker", widget.colour_color, misc_flags | pygui.COLOR_EDIT_FLAGS_NO_SIDE_PREVIEW | pygui.COLOR_EDIT_FLAGS_NO_SMALL_PREVIEW)
            pygui.same_line()

            pygui.begin_group()
            pygui.text("Current")
            pygui.color_button("##current", widget.colour_color.tuple(), pygui.COLOR_EDIT_FLAGS_NO_PICKER | pygui.COLOR_EDIT_FLAGS_ALPHA_PREVIEW_HALF, (60, 40))
            pygui.text("Previous")
            if pygui.color_button("##previous", widget.colour_backup_color.tuple(), pygui.COLOR_EDIT_FLAGS_NO_PICKER | pygui.COLOR_EDIT_FLAGS_ALPHA_PREVIEW_HALF, (60, 40)):
                widget.colour_color = widget.colour_backup_color.copy()
            pygui.separator()
            pygui.text("Palette")
            for n in range(len(widget.colour_saved_palette)):
                pygui.push_id(n)
                if n % 8 != 0:
                    pygui.same_line(0, pygui.get_style().item_spacing[0])
                
                palette_button_flags = \
                    pygui.COLOR_EDIT_FLAGS_NO_ALPHA | \
                    pygui.COLOR_EDIT_FLAGS_NO_PICKER | \
                    pygui.COLOR_EDIT_FLAGS_NO_TOOLTIP
                if pygui.color_button("##palette", widget.colour_saved_palette[n].tuple(), palette_button_flags, (20, 20)):
                    preserved_alpha = widget.colour_color.w
                    widget.colour_color = widget.colour_saved_palette[n].copy()
                    widget.colour_color.w = preserved_alpha

                # Allow user to drop colors into each palette entry. Note that ColorButton() is already a
                # drag source by default, unless specifying the ImGuiColorEditFlags_NoDragDrop flag.
                # Pygui note. In the pyx file the accept drap drop payload for
                # the color 3f and 4f types will return Vec4 containing the
                # color that is being dragged.
                if pygui.begin_drag_drop_target():
                    payload: pygui.ImGuiPayload = pygui.accept_drag_drop_payload(pygui.PAYLOAD_TYPE_COLOR_3F)
                    if payload is not None:
                        preserved_alpha = widget.colour_saved_palette[n].w
                        vec4: pygui.Vec4 = payload.data
                        widget.colour_saved_palette[n] = vec4.copy()
                        widget.colour_saved_palette[n].w = preserved_alpha
                    
                    payload = pygui.accept_drag_drop_payload(pygui.PAYLOAD_TYPE_COLOR_4F)
                    if payload is not None:
                        preserved_alpha = widget.colour_saved_palette[n].w
                        vec4: pygui.Vec4 = payload.data
                        widget.colour_saved_palette[n] = vec4.copy()
                        widget.colour_saved_palette[n].w = preserved_alpha
                    pygui.end_drag_drop_target()
                
                pygui.pop_id()
            pygui.end_group()
            pygui.end_popup()

        pygui.text("Color button only:")
        pygui.checkbox("ImGuiColorEditFlags_NoBorder", widget.colour_no_border)
        pygui.color_button(
            "MyColor##3c",
            widget.colour_color.tuple(),
            misc_flags | (pygui.COLOR_EDIT_FLAGS_NO_BORDER if widget.colour_no_border else 0),
            (80, 80))
        
        pygui.separator_text("Color picker")
        pygui.checkbox("With Alpha", widget.colour_alpha)
        pygui.checkbox("With Alpha Bar", widget.colour_alpha_bar)
        pygui.checkbox("With Side Preview Bar", widget.colour_side_preview)
        if widget.colour_side_preview:
            pygui.same_line()
            pygui.checkbox("With Ref Color", widget.colour_ref_color)
            if widget.colour_ref_color:
                pygui.same_line()
                pygui.color_edit4("##RefColor", widget.colour_ref_color_v, pygui.COLOR_EDIT_FLAGS_NO_INPUTS | misc_flags)
        pygui.combo("Display Mode", widget.colour_display_mode, ["Auto/Current", "None", "RGB Only", "HSV Only", "Hex Only"])
        pygui.same_line()
        help_marker(
            "ColorEdit defaults to displaying RGB inputs if you don't specify a display mode, "
            "but the user can change it with a right-click on those inputs.\n\nColorPicker defaults to displaying RGB+HSV+Hex "
            "if you don't specify a display mode.\n\nYou can change the defaults using SetColorEditOptions().")
        pygui.same_line()
        help_marker("When not specified explicitly (Auto/Current mode), user can right-click the picker to change mode.")
        flags = misc_flags
        if not widget.colour_alpha: # This is by default if you call ColorPicker3() instead of ColorPicker4()
            flags |= pygui.COLOR_EDIT_FLAGS_NO_ALPHA
        if widget.colour_alpha_bar:
            flags |= pygui.COLOR_EDIT_FLAGS_ALPHA_BAR
        if not widget.colour_side_preview:
            flags |= pygui.COLOR_EDIT_FLAGS_NO_SIDE_PREVIEW
        if widget.colour_picker_mode.value == 1:
            flags |= pygui.COLOR_EDIT_FLAGS_PICKER_HUE_BAR
        if widget.colour_picker_mode.value == 2:
            flags |= pygui.COLOR_EDIT_FLAGS_PICKER_HUE_WHEEL
        if widget.colour_display_mode.value == 1:
            flags |= pygui.COLOR_EDIT_FLAGS_NO_INPUTS # Disable all RGB/HSV/Hex displays
        if widget.colour_display_mode.value == 2:
            flags |= pygui.COLOR_EDIT_FLAGS_DISPLAY_RGB # Override display mode
        if widget.colour_display_mode.value == 3:
            flags |= pygui.COLOR_EDIT_FLAGS_DISPLAY_HSV
        if widget.colour_display_mode.value == 4:
            flags |= pygui.COLOR_EDIT_FLAGS_DISPLAY_HEX

        pygui.color_picker4("MyColor##4", widget.colour_color, flags, widget.colour_ref_color_v if widget.colour_ref_color else None)

        pygui.text("Set defaults in code:")
        pygui.same_line()
        help_marker("SetColorEditOptions() is designed to allow you to set boot-time default.\n"
            "We don't have Push/Pop functions because you can force options on a per-widget basis if needed,"
            "and the user can change non-forced ones with the options menu.\nWe don't have a getter to avoid"
            "encouraging you to persistently save values that aren't forward-compatible.")
        if pygui.button("Default: Uint8 + HSV + Hue Bar"):
            pygui.set_color_edit_options(pygui.COLOR_EDIT_FLAGS_UINT8 | pygui.COLOR_EDIT_FLAGS_DISPLAY_HSV | pygui.COLOR_EDIT_FLAGS_PICKER_HUE_BAR)
        if pygui.button("Default: Float + HDR + Hue Wheel"):
            pygui.set_color_edit_options(pygui.COLOR_EDIT_FLAGS_FLOAT | pygui.COLOR_EDIT_FLAGS_HDR | pygui.COLOR_EDIT_FLAGS_PICKER_HUE_WHEEL)

        # Always both a small version of both types of pickers (to make it more visible in the demo to people who are skimming quickly through it)
        pygui.text("Both types:")
        w = (pygui.get_content_region_avail()[0] - pygui.get_style().item_spacing[1]) * 0.4
        pygui.set_next_item_width(w)
        pygui.color_picker3("##MyColor##5", widget.colour_color, pygui.COLOR_EDIT_FLAGS_PICKER_HUE_BAR | pygui.COLOR_EDIT_FLAGS_NO_SIDE_PREVIEW | pygui.COLOR_EDIT_FLAGS_NO_INPUTS | pygui.COLOR_EDIT_FLAGS_NO_ALPHA)
        pygui.same_line()
        pygui.set_next_item_width(w)
        pygui.color_picker3("##MyColor##6", widget.colour_color, pygui.COLOR_EDIT_FLAGS_PICKER_HUE_WHEEL | pygui.COLOR_EDIT_FLAGS_NO_SIDE_PREVIEW | pygui.COLOR_EDIT_FLAGS_NO_INPUTS | pygui.COLOR_EDIT_FLAGS_NO_ALPHA)

        # HSV encoded support (to avoid RGB<>HSV round trips and singularities when S==0 or V==0)
        pygui.spacing()
        pygui.text("HSV encoded colors")
        pygui.same_line()
        help_marker(
            "By default, colors are given to ColorEdit and ColorPicker in RGB, but ImGuiColorEditFlags_InputHSV"
            "allows you to store colors as HSV and pass them to ColorEdit and ColorPicker as HSV. This comes with the"
            "added benefit that you can manipulate hue values with the picker even when saturation or value are zero.")
        pygui.text("Color widget with InputHSV:")
        pygui.color_edit4("HSV shown as RGB##1", widget.colour_color_hsv, pygui.COLOR_EDIT_FLAGS_DISPLAY_RGB | pygui.COLOR_EDIT_FLAGS_INPUT_HSV | pygui.COLOR_EDIT_FLAGS_FLOAT)
        pygui.color_edit4("HSV shown as HSV##1", widget.colour_color_hsv, pygui.COLOR_EDIT_FLAGS_DISPLAY_HSV | pygui.COLOR_EDIT_FLAGS_INPUT_HSV | pygui.COLOR_EDIT_FLAGS_FLOAT)
        drag_floats = [pygui.Float(v) for v in widget.colour_color_hsv.tuple()]
        pygui.drag_float4("Raw HSV values", drag_floats, 0.01, 0, 1)
        widget.colour_color_hsv = pygui.Vec4(*(f.value for f in drag_floats))

        pygui.tree_pop()

    if pygui.tree_node("Data Types"):
        IM_PRId64 = "I64d"
        IM_PRIu64 = "I64u"
        s8_zero  = 0;  s8_one  = 1;  s8_fifty  = 50;  s8_min  = -128;               s8_max = 127
        u8_zero  = 0;  u8_one  = 1;  u8_fifty  = 50;  u8_min  = 0;                  u8_max = 255
        s16_zero = 0;  s16_one = 1;  s16_fifty = 50;  s16_min = -32768;             s16_max = 32767
        u16_zero = 0;  u16_one = 1;  u16_fifty = 50;  u16_min = 0;                  u16_max = 65535
        s32_zero = 0;  s32_one = 1;  s32_fifty = 50;  s32_min = pygui.INT_MIN//2;   s32_max = pygui.INT_MAX//2;    s32_hi_a = pygui.INT_MAX//2 - 100;    s32_hi_b = pygui.INT_MAX//2
        u32_zero = 0;  u32_one = 1;  u32_fifty = 50;  u32_min = 0;                  u32_max = pygui.UINT_MAX//2;   u32_hi_a = pygui.UINT_MAX//2 - 100;   u32_hi_b = pygui.UINT_MAX//2
        s64_zero = 0;  s64_one = 1;  s64_fifty = 50;  s64_min = pygui.LLONG_MIN//2; s64_max = pygui.LLONG_MAX//2;  s64_hi_a = pygui.LLONG_MAX//2 - 100;  s64_hi_b = pygui.LLONG_MAX//2
        u64_zero = 0;  u64_one = 1;  u64_fifty = 50;  u64_min = 0;                  u64_max = pygui.ULLONG_MAX//2; u64_hi_a = pygui.ULLONG_MAX//2 - 100; u64_hi_b = pygui.ULLONG_MAX//2
        f32_zero = 0;  f32_one = 1;  f32_lo_a = -10000000000;      f32_hi_a = +10000000000
        f64_zero = 0;  f64_one = 1;  f64_lo_a = -1000000000000000; f64_hi_a = +1000000000000000

        pygui.separator_text("Drags")
        pygui.checkbox("Clamp integers to 0..50", widget.data_drag_clamp)
        drag_clamp = widget.data_drag_clamp.value

        if pygui.tree_node("drag_scalar"):
            pygui.drag_scalar("drag s8",         pygui.DATA_TYPE_S8,     widget.data_s8_v,  1,       s8_zero  if drag_clamp else None, s8_fifty  if drag_clamp else None)
            pygui.drag_scalar("drag u8",         pygui.DATA_TYPE_U8,     widget.data_u8_v,  1,       u8_zero  if drag_clamp else None, u8_fifty  if drag_clamp else None, "%u ms")
            pygui.drag_scalar("drag s16",        pygui.DATA_TYPE_S16,    widget.data_s16_v, 1 << 8,  s16_zero if drag_clamp else None, s16_fifty if drag_clamp else None)
            pygui.drag_scalar("drag u16",        pygui.DATA_TYPE_U16,    widget.data_u16_v, 1 << 8,  u16_zero if drag_clamp else None, u16_fifty if drag_clamp else None, "%u ms")
            pygui.drag_scalar("drag s32",        pygui.DATA_TYPE_S32,    widget.data_s32_v, 1 << 24, s32_zero if drag_clamp else None, s32_fifty if drag_clamp else None)
            pygui.drag_scalar("drag s32 hex",    pygui.DATA_TYPE_S32,    widget.data_s32_v, 1 << 24, s32_zero if drag_clamp else None, s32_fifty if drag_clamp else None, "0x%08X")
            pygui.drag_scalar("drag u32",        pygui.DATA_TYPE_U32,    widget.data_u32_v, 1 << 24, u32_zero if drag_clamp else None, u32_fifty if drag_clamp else None, "%u ms")
            pygui.drag_scalar("drag s64",        pygui.DATA_TYPE_S64,    widget.data_s64_v, 1 << 56, s64_zero if drag_clamp else None, s64_fifty if drag_clamp else None)
            pygui.drag_scalar("drag u64",        pygui.DATA_TYPE_U64,    widget.data_u64_v, 1 << 56, u64_zero if drag_clamp else None, u64_fifty if drag_clamp else None)
            pygui.drag_scalar("drag float",      pygui.DATA_TYPE_FLOAT,  widget.data_f32_v, 0.005,   f32_zero, f32_one, "%f")
            pygui.drag_scalar("drag float log",  pygui.DATA_TYPE_FLOAT,  widget.data_f32_v, 0.005,   f32_zero, f32_one, "%f", pygui.SLIDER_FLAGS_LOGARITHMIC)
            pygui.drag_scalar("drag double",     pygui.DATA_TYPE_DOUBLE, widget.data_f64_v, 0.0005,  f64_zero, None,    "%.10f grams")
            pygui.drag_scalar("drag double log", pygui.DATA_TYPE_DOUBLE, widget.data_f64_v, 0.0005,  f64_zero, f64_one, "0 < %.10f < 1", pygui.SLIDER_FLAGS_LOGARITHMIC)
            pygui.tree_pop()

        if pygui.tree_node("slider_scalar"):
            pygui.slider_scalar("slider s8 full",       pygui.DATA_TYPE_S8,     widget.data_s8_v,  s8_min,   s8_max,   "%d")
            pygui.slider_scalar("slider u8 full",       pygui.DATA_TYPE_U8,     widget.data_u8_v,  u8_min,   u8_max,   "%u")
            pygui.slider_scalar("slider s16 full",      pygui.DATA_TYPE_S16,    widget.data_s16_v, s16_min,  s16_max,  "%d")
            pygui.slider_scalar("slider u16 full",      pygui.DATA_TYPE_U16,    widget.data_u16_v, u16_min,  u16_max,  "%u")
            pygui.slider_scalar("slider s32 low",       pygui.DATA_TYPE_S32,    widget.data_s32_v, s32_zero, s32_fifty,"%d")
            pygui.slider_scalar("slider s32 high",      pygui.DATA_TYPE_S32,    widget.data_s32_v, s32_hi_a, s32_hi_b, "%d")
            pygui.slider_scalar("slider s32 full",      pygui.DATA_TYPE_S32,    widget.data_s32_v, s32_min,  s32_max,  "%d")
            pygui.slider_scalar("slider s32 hex",       pygui.DATA_TYPE_S32,    widget.data_s32_v, s32_zero, s32_fifty, "0x%04X")
            pygui.slider_scalar("slider u32 low",       pygui.DATA_TYPE_U32,    widget.data_u32_v, u32_zero, u32_fifty,"%u")
            pygui.slider_scalar("slider u32 high",      pygui.DATA_TYPE_U32,    widget.data_u32_v, u32_hi_a, u32_hi_b, "%u")
            pygui.slider_scalar("slider u32 full",      pygui.DATA_TYPE_U32,    widget.data_u32_v, u32_min,  u32_max,  "%u")
            pygui.slider_scalar("slider s64 low",       pygui.DATA_TYPE_S64,    widget.data_s64_v, s64_zero, s64_fifty,"%" + IM_PRId64)
            pygui.slider_scalar("slider s64 high",      pygui.DATA_TYPE_S64,    widget.data_s64_v, s64_hi_a, s64_hi_b, "%" + IM_PRId64)
            pygui.slider_scalar("slider s64 full",      pygui.DATA_TYPE_S64,    widget.data_s64_v, s64_min,  s64_max,  "%" + IM_PRId64)
            pygui.slider_scalar("slider u64 low",       pygui.DATA_TYPE_U64,    widget.data_u64_v, u64_zero, u64_fifty,"%" + IM_PRIu64 + " ms")
            pygui.slider_scalar("slider u64 high",      pygui.DATA_TYPE_U64,    widget.data_u64_v, u64_hi_a, u64_hi_b, "%" + IM_PRIu64 + " ms")
            pygui.slider_scalar("slider u64 full",      pygui.DATA_TYPE_U64,    widget.data_u64_v, u64_min,  u64_max,  "%" + IM_PRIu64 + " ms")
            pygui.slider_scalar("slider float low",     pygui.DATA_TYPE_FLOAT,  widget.data_f32_v, f32_zero, f32_one)
            pygui.slider_scalar("slider float low log", pygui.DATA_TYPE_FLOAT,  widget.data_f32_v, f32_zero, f32_one,  "%.10f", pygui.SLIDER_FLAGS_LOGARITHMIC)
            pygui.slider_scalar("slider float high",    pygui.DATA_TYPE_FLOAT,  widget.data_f32_v, f32_lo_a, f32_hi_a, "%e")
            pygui.slider_scalar("slider double low",    pygui.DATA_TYPE_DOUBLE, widget.data_f64_v, f64_zero, f64_one,  "%.10f grams")
            pygui.slider_scalar("slider double low log",pygui.DATA_TYPE_DOUBLE, widget.data_f64_v, f64_zero, f64_one,  "%.10f", pygui.SLIDER_FLAGS_LOGARITHMIC)
            pygui.slider_scalar("slider double high",   pygui.DATA_TYPE_DOUBLE, widget.data_f64_v, f64_lo_a, f64_hi_a, "%e grams")
            pygui.tree_pop()

        if pygui.tree_node("slider_scalar reverse"):
            pygui.slider_scalar("slider s8 reverse",    pygui.DATA_TYPE_S8,   widget.data_s8_v,  s8_max,    s8_min,   "%d")
            pygui.slider_scalar("slider u8 reverse",    pygui.DATA_TYPE_U8,   widget.data_u8_v,  u8_max,    u8_min,   "%u")
            pygui.slider_scalar("slider s32 reverse",   pygui.DATA_TYPE_S32,  widget.data_s32_v, s32_fifty, s32_zero, "%d")
            pygui.slider_scalar("slider u32 reverse",   pygui.DATA_TYPE_U32,  widget.data_u32_v, u32_fifty, u32_zero, "%u")
            pygui.slider_scalar("slider s64 reverse",   pygui.DATA_TYPE_S64,  widget.data_s64_v, s64_fifty, s64_zero, "%" + IM_PRId64)
            pygui.slider_scalar("slider u64 reverse",   pygui.DATA_TYPE_U64,  widget.data_u64_v, u64_fifty, u64_zero, "%" + IM_PRIu64 + " ms")
            pygui.tree_pop()

        if pygui.tree_node("input_scalar"):
            pygui.checkbox("Show step buttons", widget.data_inputs_step)
            pygui.input_scalar("input s8",      pygui.DATA_TYPE_S8,     widget.data_s8_v,  s8_one  if widget.data_inputs_step else None, None, "%d")
            pygui.input_scalar("input u8",      pygui.DATA_TYPE_U8,     widget.data_u8_v,  u8_one  if widget.data_inputs_step else None, None, "%u")
            pygui.input_scalar("input s16",     pygui.DATA_TYPE_S16,    widget.data_s16_v, s16_one if widget.data_inputs_step else None, None, "%d")
            pygui.input_scalar("input u16",     pygui.DATA_TYPE_U16,    widget.data_u16_v, u16_one if widget.data_inputs_step else None, None, "%u")
            pygui.input_scalar("input s32",     pygui.DATA_TYPE_S32,    widget.data_s32_v, s32_one if widget.data_inputs_step else None, None, "%d")
            pygui.input_scalar("input s32 hex", pygui.DATA_TYPE_S32,    widget.data_s32_v, s32_one if widget.data_inputs_step else None, None, "%04X")
            pygui.input_scalar("input u32",     pygui.DATA_TYPE_U32,    widget.data_u32_v, u32_one if widget.data_inputs_step else None, None, "%u")
            pygui.input_scalar("input u32 hex", pygui.DATA_TYPE_U32,    widget.data_u32_v, u32_one if widget.data_inputs_step else None, None, "%08X")
            pygui.input_scalar("input s64",     pygui.DATA_TYPE_S64,    widget.data_s64_v, s64_one if widget.data_inputs_step else None)
            pygui.input_scalar("input u64",     pygui.DATA_TYPE_U64,    widget.data_u64_v, u64_one if widget.data_inputs_step else None)
            pygui.input_scalar("input float",   pygui.DATA_TYPE_FLOAT,  widget.data_f32_v, f32_one if widget.data_inputs_step else None)
            pygui.input_scalar("input double",  pygui.DATA_TYPE_DOUBLE, widget.data_f64_v, f64_one if widget.data_inputs_step else None)
            pygui.tree_pop()

        # The _n versions. These are annoying.
        if pygui.tree_node("drag_scalar_n"):
            help_marker(
                "This example demonstrates the importance of selecting the correct data type.\n"
                " 4 * 1 byte (s8/u8)   chars  == 1 * 4 byte int.\n"
                " 2 * 2 byte (s16/u16) shorts == 1 * 4 byte int.\n"
                " 2 * 4 byte (s16/u16) ints   == 1 * 8 byte long.\n"
                " So if you want to edit an integer then you should select S32 as the type. Otherwise, this actually makes"
                " a neat way to edit the bits of an integer")
            pygui.drag_scalar_n("drag_n s8",      pygui.DATA_TYPE_S8,     widget.data_long_n, 16)
            pygui.drag_scalar_n("drag_n u8",      pygui.DATA_TYPE_U8,     widget.data_long_n, 16)
            pygui.drag_scalar_n("drag_n s16",     pygui.DATA_TYPE_S16,    widget.data_long_n, 8)
            pygui.drag_scalar_n("drag_n u16",     pygui.DATA_TYPE_U16,    widget.data_long_n, 8)
            pygui.drag_scalar_n("drag_n s32",     pygui.DATA_TYPE_S32,    widget.data_long_n, 4)
            pygui.drag_scalar_n("drag_n s32 hex", pygui.DATA_TYPE_S32,    widget.data_long_n, 4)
            pygui.drag_scalar_n("drag_n u32",     pygui.DATA_TYPE_U32,    widget.data_long_n, 4, 1 << 22)
            pygui.drag_scalar_n("drag_n u32 hex", pygui.DATA_TYPE_U32,    widget.data_long_n, 4, 1 << 22)
            pygui.drag_scalar_n("drag_n s64",     pygui.DATA_TYPE_S64,    widget.data_long_n, 2, 1 << 54)
            pygui.drag_scalar_n("drag_n u64",     pygui.DATA_TYPE_U64,    widget.data_long_n, 2, 1 << 54)
            pygui.drag_scalar_n("drag_n float",   pygui.DATA_TYPE_FLOAT,  widget.data_float_n, 4)
            pygui.drag_scalar_n("drag_n double",  pygui.DATA_TYPE_DOUBLE, widget.data_double_n, 4)
            pygui.tree_pop()

        if pygui.tree_node("slider_scalar_n"):
            pygui.slider_scalar_n("slider_n s8",      pygui.DATA_TYPE_S8,     widget.data_long_n, 16,  s8_min,  s8_max)
            pygui.slider_scalar_n("slider_n u8",      pygui.DATA_TYPE_U8,     widget.data_long_n, 16,  u8_min,  u8_max)
            pygui.slider_scalar_n("slider_n s16",     pygui.DATA_TYPE_S16,    widget.data_long_n, 8,   s16_min, s16_max)
            pygui.slider_scalar_n("slider_n u16",     pygui.DATA_TYPE_U16,    widget.data_long_n, 8,   u16_min, u16_max)
            pygui.slider_scalar_n("slider_n s32",     pygui.DATA_TYPE_S32,    widget.data_long_n, 4,   s32_min, s32_max)
            pygui.slider_scalar_n("slider_n s32 hex", pygui.DATA_TYPE_S32,    widget.data_long_n, 4,   s32_min, s32_max)
            pygui.slider_scalar_n("slider_n u32",     pygui.DATA_TYPE_U32,    widget.data_long_n, 4,   u32_min, u32_max)
            pygui.slider_scalar_n("slider_n u32 hex", pygui.DATA_TYPE_U32,    widget.data_long_n, 4,   u32_min, u32_max)
            pygui.slider_scalar_n("slider_n s64",     pygui.DATA_TYPE_S64,    widget.data_long_n, 2,   s64_min, s64_max)
            pygui.slider_scalar_n("slider_n u64",     pygui.DATA_TYPE_U64,    widget.data_long_n, 2,   u64_min, u64_max)
            pygui.slider_scalar_n("slider_n float",   pygui.DATA_TYPE_FLOAT,  widget.data_float_n, 4,  f32_lo_a, f32_hi_a)
            pygui.slider_scalar_n("slider_n double",  pygui.DATA_TYPE_DOUBLE, widget.data_double_n, 4, f64_lo_a, f64_hi_a)
            pygui.tree_pop()

        if pygui.tree_node("input_scalar_n"):
            pygui.input_scalar_n("input_n s8",      pygui.DATA_TYPE_S8,     widget.data_long_n, 8,   1,    10) # It works with 16 but looks terrible
            pygui.input_scalar_n("input_n u8",      pygui.DATA_TYPE_U8,     widget.data_long_n, 8,   2,    20)
            pygui.input_scalar_n("input_n s16",     pygui.DATA_TYPE_S16,    widget.data_long_n, 8,   3,    30)
            pygui.input_scalar_n("input_n u16",     pygui.DATA_TYPE_U16,    widget.data_long_n, 8,   4,    40)
            pygui.input_scalar_n("input_n s32",     pygui.DATA_TYPE_S32,    widget.data_long_n, 4,   5,    50)
            pygui.input_scalar_n("input_n s32 hex", pygui.DATA_TYPE_S32,    widget.data_long_n, 4,   6,    60)
            pygui.input_scalar_n("input_n u32",     pygui.DATA_TYPE_U32,    widget.data_long_n, 4,   7,    70)
            pygui.input_scalar_n("input_n u32 hex", pygui.DATA_TYPE_U32,    widget.data_long_n, 4,   8,    80)
            pygui.input_scalar_n("input_n s64",     pygui.DATA_TYPE_S64,    widget.data_long_n, 2,   9,    90)
            pygui.input_scalar_n("input_n u64",     pygui.DATA_TYPE_U64,    widget.data_long_n, 2,   10,   100)
            pygui.input_scalar_n("input_n float",   pygui.DATA_TYPE_FLOAT,  widget.data_float_n, 4,  0.1,  1)
            pygui.input_scalar_n("input_n double",  pygui.DATA_TYPE_DOUBLE, widget.data_double_n, 4, 0.01, 0.1)
            pygui.tree_pop()

        if pygui.tree_node("vslider_scalar"):
            pygui.vslider_scalar("##vslider_scalar s8",      (80, 160), pygui.DATA_TYPE_S8,     widget.data_s8_v,  s8_min,   s8_max);   pygui.same_line()
            pygui.vslider_scalar("##vslider_scalar u8",      (80, 160), pygui.DATA_TYPE_U8,     widget.data_u8_v,  u8_min,   u8_max);   pygui.same_line()
            pygui.vslider_scalar("##vslider_scalar s16",     (80, 160), pygui.DATA_TYPE_S16,    widget.data_s16_v, s16_min,  s16_max);  pygui.same_line()
            pygui.vslider_scalar("##vslider_scalar u16",     (80, 160), pygui.DATA_TYPE_U16,    widget.data_u16_v, u16_min,  u16_max);  pygui.same_line()
            pygui.vslider_scalar("##vslider_scalar s32",     (80, 160), pygui.DATA_TYPE_S32,    widget.data_s32_v, s32_min,  s32_max)
            pygui.vslider_scalar("##vslider_scalar s32 hex", (80, 160), pygui.DATA_TYPE_S32,    widget.data_s32_v, s32_min,  s32_max);  pygui.same_line()
            pygui.vslider_scalar("##vslider_scalar u32",     (80, 160), pygui.DATA_TYPE_U32,    widget.data_u32_v, u32_min,  u32_max);  pygui.same_line()
            pygui.vslider_scalar("##vslider_scalar u32 hex", (80, 160), pygui.DATA_TYPE_U32,    widget.data_u32_v, u32_min,  u32_max);  pygui.same_line()
            pygui.vslider_scalar("##vslider_scalar s64",     (80, 160), pygui.DATA_TYPE_S64,    widget.data_s64_v, s64_min,  s64_max);  pygui.same_line()
            pygui.vslider_scalar("##vslider_scalar u64",     (80, 160), pygui.DATA_TYPE_U64,    widget.data_u64_v, u64_min,  u64_max)
            pygui.vslider_scalar("##vslider_scalar float",   (80, 160), pygui.DATA_TYPE_FLOAT,  widget.data_f32_v, f32_zero, f32_hi_a); pygui.same_line()
            pygui.vslider_scalar("##vslider_scalar double",  (80, 160), pygui.DATA_TYPE_DOUBLE, widget.data_f64_v, f64_zero, f64_hi_a)
            pygui.tree_pop()
        pygui.tree_pop()

    if pygui.tree_node("Multi-component Widgets"):
        pygui.separator_text("2-wide")
        pygui.input_float2("input float2", widget.multi_vec4f.as_floatptrs())
        pygui.drag_float2("drag float2", widget.multi_vec4f.as_floatptrs(), 0.01, 0, 1)
        pygui.slider_float2("slider float2", widget.multi_vec4f.as_floatptrs(), 0, 1)
        pygui.input_int2("input int2", widget.multi_vec4i.as_floatptrs())
        pygui.drag_int2("drag int2", widget.multi_vec4i.as_floatptrs(), 1, 0, 255)
        pygui.slider_int2("slider int2", widget.multi_vec4i.as_floatptrs(), 0, 255)

        pygui.separator_text("3-wide")
        pygui.input_float3("input float3", widget.multi_vec4f.as_floatptrs())
        pygui.drag_float3("drag float3", widget.multi_vec4f.as_floatptrs(), 0.01, 0, 1)
        pygui.slider_float3("slider float3", widget.multi_vec4f.as_floatptrs(), 0, 1)
        pygui.input_int3("input int3", widget.multi_vec4i.as_floatptrs())
        pygui.drag_int3("drag int3", widget.multi_vec4i.as_floatptrs(), 1, 0, 255)
        pygui.slider_int3("slider int3", widget.multi_vec4i.as_floatptrs(), 0, 255)

        pygui.separator_text("4-wide")
        pygui.input_float4("input float4", widget.multi_vec4f.as_floatptrs())
        pygui.drag_float4("drag float4", widget.multi_vec4f.as_floatptrs(), 0.01, 0, 1)
        pygui.slider_float4("slider float4", widget.multi_vec4f.as_floatptrs(), 0, 1)
        pygui.input_int4("input int4", widget.multi_vec4i.as_floatptrs())
        pygui.drag_int4("drag int4", widget.multi_vec4i.as_floatptrs(), 1, 0, 255)
        pygui.slider_int4("slider int4", widget.multi_vec4i.as_floatptrs(), 0, 255)

        pygui.tree_pop()

    if pygui.tree_node("Vertical Sliders"):
        spacing = 4
        pygui.push_style_var(pygui.STYLE_VAR_ITEM_SPACING, (spacing, spacing))
        pygui.vslider_int("##int", (18, 160), widget.vert_int_value, 0, 5)
        pygui.same_line()

        pygui.push_id("set1")
        for i in range(7):
            if i > 0:
                pygui.same_line()
            pygui.push_id(i)
            pygui.push_style_color(pygui.COL_FRAME_BG, pygui.color_convert_hsv_to_rgb(i / 7, 0.5, 0.5))
            pygui.push_style_color(pygui.COL_FRAME_BG_HOVERED, pygui.color_convert_hsv_to_rgb(i / 7, 0.6, 0.5))
            pygui.push_style_color(pygui.COL_FRAME_BG_ACTIVE, pygui.color_convert_hsv_to_rgb(i / 7, 0.7, 0.5))
            pygui.push_style_color(pygui.COL_SLIDER_GRAB, pygui.color_convert_hsv_to_rgb(i / 7, 0.9, 0.9))
            pygui.vslider_float("##v", (18, 160), widget.vert_values[i], 0, 1, "")
            if pygui.is_item_active() or pygui.is_item_hovered():
                pygui.set_tooltip("{:.3f}".format(widget.vert_values[i].value))
            pygui.pop_style_color(4)
            pygui.pop_id()
        pygui.pop_id()

        pygui.same_line()
        pygui.push_id("set2")
        rows = 3
        small_slider_size = (18, (160 - (rows - 1) * spacing) // rows)
        for nx in range(4):
            if nx > 0:
                pygui.same_line()
            pygui.begin_group()
            for ny in range(rows):
                pygui.push_id(nx * rows + ny)
                pygui.vslider_float("##v", small_slider_size, widget.vert_values2[nx], 0, 1, "")
                if pygui.is_item_active() or pygui.is_item_hovered():
                    pygui.set_tooltip("{:.3f}".format(widget.vert_values2[nx].value))
                pygui.pop_id()
            pygui.end_group()
        pygui.pop_id()

        pygui.same_line()
        pygui.push_id("set3")
        for i in range(4):
            if i > 0:
                pygui.same_line()
            pygui.push_id(i)
            pygui.push_style_var(pygui.STYLE_VAR_GRAB_MIN_SIZE, 40)
            pygui.vslider_float("##v", (40, 160), widget.vert_values[i], 0, 1, "%.2f\nsec")
            pygui.pop_style_var()
            pygui.pop_id()
        pygui.pop_id()
        pygui.pop_style_var()
        pygui.tree_pop()


class layout:
    track_item = pygui.Int(50)
    enable_track = pygui.Bool(True)
    enable_extra_decorations = pygui.Bool(False)
    scroll_to_off_px = pygui.Float()
    scroll_to_pos_px = pygui.Float(200)
    lines = pygui.Int(7)


def show_demo_window_layout():
    if not pygui.collapsing_header("Layout & Scrolling"):
        return
    
    if pygui.tree_node("Scrolling"):
        help_marker("Use SetScrollHereY() or SetScrollFromPosY() to scroll to a given vertical position.")
        pygui.checkbox("Decoration", layout.enable_extra_decorations)
        pygui.checkbox("Track", layout.enable_track)
        pygui.push_item_width(100)
        pygui.same_line(140)
        layout.enable_track.value |= pygui.drag_int("##item", layout.track_item, 0.25, 0, 99, "Item = %d")

        scroll_to_off = pygui.button("Scroll Offset")
        pygui.same_line(140)
        scroll_to_off |= pygui.drag_float("##off", layout.scroll_to_off_px, 1, 0, pygui.FLT_MAX, "+%.0f px")

        scroll_to_pos = pygui.button("Scroll To Pos")
        pygui.same_line(140)
        scroll_to_pos |= pygui.drag_float("##pos", layout.scroll_to_pos_px, 1, -10, pygui.FLT_MAX, "X/Y = %.0f px")
        pygui.pop_item_width()

        if scroll_to_off or scroll_to_pos:
            layout.enable_track.value = False
        
        style = pygui.get_style()
        child_w = (pygui.get_content_region_avail()[0] - 4 * style.item_spacing[0]) / 5
        if child_w < 1:
            child_w = 1
        pygui.push_id("##VerticalScrolling")
        for i in range(5):
            if i > 0:
                pygui.same_line()
            pygui.begin_group()
            names = ["Top", "25%", "Center", "75%", "Bottom"]
            pygui.text_unformatted(names[i])

            child_flags = pygui.WINDOW_FLAGS_MENU_BAR if layout.enable_extra_decorations else 0
            child_id = pygui.get_id(str(i))
            child_is_visible = pygui.begin_child(str(child_id), (child_w, 200), True, child_flags)
            if pygui.begin_menu_bar():
                pygui.text_unformatted("abc")
                pygui.end_menu_bar()
            if scroll_to_off:
                pygui.set_scroll_y(layout.scroll_to_off_px.value)
            if scroll_to_pos:
                pygui.set_scroll_from_pos_y(pygui.get_cursor_start_pos()[1] + layout.scroll_to_pos_px.value, i * 0.25)
            if child_is_visible: # Avoid calling SetScrollHereY when running with culled items
                for item in range(100):
                    if layout.enable_track and item == layout.track_item.value:
                        pygui.text_colored((1, 1, 0, 1), "Item {}".format(item))
                        pygui.set_scroll_here_y(i * 0.25) # 0.0f:top, 0.5f:center, 1.0f:bottom
                    else:
                        pygui.text("Item {}".format(item))
            scroll_y = pygui.get_scroll_y()
            scroll_max_y = pygui.get_scroll_max_y()
            pygui.end_child()
            pygui.text("{:.0f}/{:.0f}".format(scroll_y, scroll_max_y))
            pygui.end_group()
        pygui.pop_id()

        # Horizontal scroll functions
        pygui.spacing()
        help_marker(
            "Use SetScrollHereX() or SetScrollFromPosX() to scroll to a given horizontal position.\n\n"
            "Because the clipping rectangle of most window hides half worth of WindowPadding on the "
            "left/right, using SetScrollFromPosX(+1) will usually result in clipped text whereas the "
            "equivalent SetScrollFromPosY(+1) wouldn't.")
        pygui.push_id("##HorizontalScrolling")
        for i in range(5):
            child_height = pygui.get_text_line_height() + style.scrollbar_size + style.window_padding[1] * 2
            child_flags = pygui.WINDOW_FLAGS_HORIZONTAL_SCROLLBAR | (pygui.WINDOW_FLAGS_ALWAYS_VERTICAL_SCROLLBAR if layout.enable_extra_decorations else 0)
            child_id = pygui.get_id(str(i))
            child_is_visible = pygui.begin_child(str(child_id), (-100, child_height), True, child_flags)
            if scroll_to_off:
                pygui.set_scroll_x(layout.scroll_to_off_px.value)
            if scroll_to_pos:
                pygui.set_scroll_from_pos_x(pygui.get_cursor_start_pos()[0] + layout.scroll_to_pos_px.value, i * 0.25)
            if child_is_visible: # Avoid calling SetScrollHereY when running with culled items
                for item in range(100):
                    if item > 0:
                        pygui.same_line()
                    if (layout.enable_track and item == layout.track_item.value):
                        pygui.text_colored((1, 1, 0, 1), "Item {}".format(item))
                        pygui.set_scroll_here_x(i * 0.25) # 0.0f:left, 0.5f:center, 1.0f:right
                    else:
                        pygui.text("Item {}".format(item))
            scroll_x = pygui.get_scroll_x()
            scroll_max_x = pygui.get_scroll_max_x()
            pygui.end_child()
            pygui.same_line()
            names = ["Left", "25%", "Center", "75%", "Right"]
            pygui.text("{}\n{:.0f}/{:.0f}".format(names[i], scroll_x, scroll_max_x))
            pygui.spacing()
        pygui.pop_id()

        # Miscellaneous Horizontal Scrolling Demo
        help_marker(
            "Horizontal scrolling for a window is enabled via the ImGuiWindowFlags_HorizontalScrollbar flag.\n\n"
            "You may want to also explicitly specify content width by using SetNextWindowContentWidth() before Begin().")
        pygui.slider_int("Lines", layout.lines, 1, 15)
        pygui.push_style_var(pygui.STYLE_VAR_FRAME_ROUNDING, 3)
        pygui.push_style_var(pygui.STYLE_VAR_FRAME_PADDING, (2, 1))
        scrolling_child_size = (0, pygui.get_frame_height_with_spacing() * 7 + 30)
        pygui.begin_child("scrolling", scrolling_child_size, True, pygui.WINDOW_FLAGS_HORIZONTAL_SCROLLBAR)
        for line in range(layout.lines.value):
            # Display random stuff. For the sake of this trivial demo we are using basic Button() + SameLine()
            # If you want to create your own time line for a real application you may be better off manipulating
            # the cursor position yourself, aka using SetCursorPos/SetCursorScreenPos to position the widgets
            # yourself. You may also want to use the lower-level ImDrawList API.
            num_buttons = 10 + (line * 9 if line & 1 else line * 3)
            
            for n in range(num_buttons):
                if n > 0:
                    pygui.same_line()
                pygui.push_id(n + line * 1000)
                if n % 15 == 0:
                    label = "FizzBuzz"
                elif n % 3 == 0:
                    label = "Fizz"
                elif n % 5 == 0:
                    label = "Buzz"
                else:
                    label = str(n)
                hue = n * 0.05
                pygui.push_style_color(pygui.COL_BUTTON, pygui.color_convert_hsv_to_rgb(hue, 0.6, 0.6))
                pygui.push_style_color(pygui.COL_BUTTON_HOVERED, pygui.color_convert_hsv_to_rgb(hue, 0.7, 0.7))
                pygui.push_style_color(pygui.COL_BUTTON_ACTIVE, pygui.color_convert_hsv_to_rgb(hue, 0.8, 0.8))
                pygui.button(label, (40 + math.sin(line + n) * 20, 0))
                pygui.pop_style_color(3)
                pygui.pop_id()
        scroll_x = pygui.get_scroll_x()
        scroll_max_x = pygui.get_scroll_max_x()
        pygui.end_child()
        pygui.pop_style_var(2)
        scroll_x_delta = 0
        pygui.small_button("<<")
        if pygui.is_item_active():
            scroll_x_delta = -pygui.get_io().delta_time * 1000
        pygui.same_line()
        pygui.text("Scroll from code")
        pygui.same_line()
        pygui.small_button(">>")
        if pygui.is_item_active():
            scroll_x_delta = +pygui.get_io().delta_time * 1000
        pygui.same_line()
        pygui.text("{:.0f}/{:.0f}".format(scroll_x, scroll_max_x))
        if scroll_x_delta != 0:
            # Demonstrate a trick: you can use Begin to set yourself in the context of another window
            # (here we are already out of your child window)
            pygui.begin_child("scrolling")
            pygui.set_scroll_x(pygui.get_scroll_x() + scroll_x_delta)
            pygui.end_child()
        pygui.spacing()

        pygui.tree_pop()


class table:
    disable_indent = pygui.Bool(False)
    border_flags = pygui.Int(pygui.TABLE_FLAGS_BORDERS | pygui.TABLE_FLAGS_ROW_BG)
    class ContentsType(Enum):
        CT_TEXT = auto()
        CT_FILL_BUTTON = auto()
    border_display_headers = pygui.Bool(False)
    border_contents_type = pygui.Int(ContentsType.CT_TEXT.value)
    resize_flags = pygui.Int( \
        pygui.TABLE_FLAGS_SIZING_STRETCH_SAME | \
        pygui.TABLE_FLAGS_RESIZABLE | \
        pygui.TABLE_FLAGS_BORDERS_OUTER | \
        pygui.TABLE_FLAGS_BORDERS_V | \
        pygui.TABLE_FLAGS_CONTEXT_MENU_IN_BODY)
    fixed_flags = pygui.Int( \
        pygui.TABLE_FLAGS_SIZING_FIXED_FIT | \
        pygui.TABLE_FLAGS_RESIZABLE | \
        pygui.TABLE_FLAGS_BORDERS_OUTER | \
        pygui.TABLE_FLAGS_BORDERS_V | \
        pygui.TABLE_FLAGS_CONTEXT_MENU_IN_BODY)
    mixed_flags = pygui.Int( \
        pygui.TABLE_FLAGS_SIZING_FIXED_FIT | \
        pygui.TABLE_FLAGS_ROW_BG | \
        pygui.TABLE_FLAGS_BORDERS | \
        pygui.TABLE_FLAGS_RESIZABLE | \
        pygui.TABLE_FLAGS_REORDERABLE | \
        pygui.TABLE_FLAGS_HIDEABLE)
    hidable_flags = pygui.Int( \
        pygui.TABLE_FLAGS_RESIZABLE | \
        pygui.TABLE_FLAGS_REORDERABLE | \
        pygui.TABLE_FLAGS_HIDEABLE | \
        pygui.TABLE_FLAGS_BORDERS_OUTER | \
        pygui.TABLE_FLAGS_BORDERS_V)
    padding_flags = pygui.Int( \
        pygui.TABLE_FLAGS_BORDERS_V)
    padding_show_headers = pygui.Bool(False)
    padding_flags2 = pygui.Int( \
        pygui.TABLE_FLAGS_BORDERS | \
        pygui.TABLE_FLAGS_ROW_BG)
    padding_cell_padding = pygui.Vec2.zero()
    padding_show_widget_frame_bg = pygui.Bool(True)
    padding_text_bufs = [pygui.String("edit me", 16) for _ in range(3 * 15)]
    sort_items = []
    sort_flags = pygui.Int( \
       pygui.TABLE_FLAGS_RESIZABLE | \
       pygui.TABLE_FLAGS_REORDERABLE | \
       pygui.TABLE_FLAGS_HIDEABLE | \
       pygui.TABLE_FLAGS_SORTABLE | \
       pygui.TABLE_FLAGS_SORT_MULTI | \
       pygui.TABLE_FLAGS_ROW_BG | \
       pygui.TABLE_FLAGS_BORDERS_OUTER | \
       pygui.TABLE_FLAGS_BORDERS_V | \
       pygui.TABLE_FLAGS_NO_BORDERS_IN_BODY | \
       pygui.TABLE_FLAGS_SCROLL_Y)
    
    # We are passing our own identifier to TableSetupColumn() to facilitate identifying columns in the sorting code.
    # This identifier will be passed down into ImGuiTableSortSpec::ColumnUserID.
    # But it is possible to omit the user id parameter of TableSetupColumn() and just use the column index instead! (ImGuiTableSortSpec::ColumnIndex)
    # If you don't use sorting, you will generally never care about giving column an ID!
    class MyItemColumnID(Enum):
        ID = auto()
        Name = auto()
        Action = auto()
        Quantity = auto()
        Description = auto()
    
    class MyItem:
        def __init__(self, _id: int, name: str, quantity: int):
            self._id = _id
            self.name = name
            self.quantity = quantity
        
        def get_column_field(self, column: int):
            """
            If you want to use this approach for sorting, then you need to make
            sure this matches the column order that is to be used in the table.
            """
            return [
                self._id,
                self.name,
                None,
                self.quantity
            ][column]
    
    # From: https://stackoverflow.com/a/75123782
    class negated: # name changed; otherwise the same
        def __init__(self, obj):
            self.obj = obj

        def __eq__(self, other):
            return other.obj == self.obj

        def __lt__(self, other):
            return other.obj < self.obj


def show_demo_tables():
    def push_style_compact():
        style = pygui.get_style()
        pygui.push_style_var(pygui.STYLE_VAR_FRAME_PADDING, (style.frame_padding[0], style.frame_padding[1] * 0.6))
        pygui.push_style_var(pygui.STYLE_VAR_ITEM_SPACING, (style.item_spacing[0], style.item_spacing[1] * 0.6))

    def pop_style_compact():
        pygui.pop_style_var(2)

    if not pygui.collapsing_header("Tables & Columns"):
        return
    
    TEXT_BASE_WIDTH = pygui.calc_text_size("A")[0]
    TEXT_BASE_HEIGHT = pygui.get_text_line_height_with_spacing()

    pygui.push_id("Tables")

    open_action = -1
    if pygui.button("Open all"):
        open_action = 1
    pygui.same_line()
    if pygui.button("Close all"):
        open_action = 0
    pygui.same_line()

    # Options
    pygui.checkbox("Disable tree indentation", table.disable_indent)
    pygui.same_line()
    help_marker("Disable the indenting of tree nodes so demo tables can use the full window width.")
    pygui.separator()
    if table.disable_indent:
        pygui.push_style_var(pygui.STYLE_VAR_INDENT_SPACING, 0)
    
    # About Styling of tables
    # Most settings are configured on a per-table basis via the flags passed to BeginTable() and TableSetupColumns APIs.
    # There are however a few settings that a shared and part of the ImGuiStyle structure:
    #   style.CellPadding                          // Padding within each cell
    #   style.Colors[ImGuiCol_TableHeaderBg]       // Table header background
    #   style.Colors[ImGuiCol_TableBorderStrong]   // Table outer and header borders
    #   style.Colors[ImGuiCol_TableBorderLight]    // Table inner borders
    #   style.Colors[ImGuiCol_TableRowBg]          // Table row background when ImGuiTableFlags_RowBg is enabled (even rows)
    #   style.Colors[ImGuiCol_TableRowBgAlt]       // Table row background when ImGuiTableFlags_RowBg is enabled (odds rows)
    
    if open_action != -1:
        pygui.set_next_item_open(open_action != 0)
    if pygui.tree_node("Basic"):
        # Here we will showcase three different ways to output a table.
        # They are very simple variations of a same thing!

        # [Method 1] Using TableNextRow() to create a new row, and TableSetColumnIndex() to select the column.
        # In many situations, this is the most flexible and easy to use pattern.
        help_marker("Using TableNextRow() + calling TableSetColumnIndex() _before_ each cell, in a loop.")
        if pygui.begin_table("table1", 3):
            for row in range(4):
                pygui.table_next_row()
                for column in range(3):
                    pygui.table_set_column_index(column)
                    pygui.text("Row {} Column {}".format(row, column))
            pygui.end_table()
        
        # [Method 2] Using TableNextColumn() called multiple times, instead of using a for loop + TableSetColumnIndex().
        # This is generally more convenient when you have code manually submitting the contents of each column.
        help_marker("Using TableNextRow() + calling TableNextColumn() _before_ each cell, manually.")
        if pygui.begin_table("table2", 3, 0):
            for row in range(4):
                pygui.table_next_row()
                pygui.table_next_column()
                pygui.text("Row {}".format(row))
                pygui.table_next_column()
                pygui.text("Some contents")
                pygui.table_next_column()
                pygui.text("123.456")
            pygui.end_table()
        
        # [Method 3] We call TableNextColumn() _before_ each cell. We never call TableNextRow(),
        # as TableNextColumn() will automatically wrap around and create new rows as needed.
        # This is generally more convenient when your cells all contains the same type of data.
        help_marker(
            "Only using TableNextColumn(), which tends to be convenient for tables where every cell contains the same type of contents.\n"
            "This is also more similar to the old NextColumn() function of the Columns API, and provided to facilitate the Columns->Tables API transition.")
        if pygui.begin_table("table3", 3):
            for item in range(14):
                pygui.table_next_column()
                pygui.text("Item {}".format(item))
            pygui.end_table()
        pygui.tree_pop()
    
    if open_action != -1:
        pygui.set_next_item_open(open_action != 0)
    if pygui.tree_node("Borders, background"):
        push_style_compact()
        pygui.checkbox_flags("ImGuiTableFlags_RowBg", table.border_flags, pygui.TABLE_FLAGS_ROW_BG)
        pygui.checkbox_flags("ImGuiTableFlags_Borders", table.border_flags, pygui.TABLE_FLAGS_BORDERS)
        pygui.same_line()
        help_marker(
            "ImGuiTableFlags_Borders\n = ImGuiTableFlags_BordersInnerV\n | ImGuiTableFlags_BordersOuterV\n | ImGuiTableFlags_BordersInnerV\n | ImGuiTableFlags_BordersOuterH")
        pygui.indent()

        pygui.checkbox_flags("ImGuiTableFlags_BordersH", table.border_flags, pygui.TABLE_FLAGS_BORDERS_H)
        pygui.indent()
        pygui.checkbox_flags("ImGuiTableFlags_BordersOuterH", table.border_flags, pygui.TABLE_FLAGS_BORDERS_OUTER_H)
        pygui.checkbox_flags("ImGuiTableFlags_BordersInnerH", table.border_flags, pygui.TABLE_FLAGS_BORDERS_INNER_H)
        pygui.unindent()

        pygui.checkbox_flags("ImGuiTableFlags_BordersV", table.border_flags, pygui.TABLE_FLAGS_BORDERS_V)
        pygui.indent()
        pygui.checkbox_flags("ImGuiTableFlags_BordersOuterV", table.border_flags, pygui.TABLE_FLAGS_BORDERS_OUTER_V)
        pygui.checkbox_flags("ImGuiTableFlags_BordersInnerV", table.border_flags, pygui.TABLE_FLAGS_BORDERS_INNER_V)
        pygui.unindent()

        pygui.checkbox_flags("ImGuiTableFlags_BordersOuter", table.border_flags, pygui.TABLE_FLAGS_BORDERS_OUTER)
        pygui.checkbox_flags("ImGuiTableFlags_BordersInner", table.border_flags, pygui.TABLE_FLAGS_BORDERS_INNER)
        pygui.unindent()

        pygui.align_text_to_frame_padding()
        pygui.text("Cell contents:")
        pygui.same_line()
        pygui.radio_button_int_ptr("Text", table.border_contents_type, table.ContentsType.CT_TEXT.value)
        pygui.same_line()
        pygui.radio_button_int_ptr("FillButton", table.border_contents_type, table.ContentsType.CT_FILL_BUTTON.value)
        pygui.checkbox("Display headers", table.border_display_headers)
        pygui.checkbox_flags("ImGuiTableFlags_NoBordersInBody", table.border_flags, pygui.TABLE_FLAGS_NO_BORDERS_IN_BODY)
        pygui.same_line()
        help_marker("Disable vertical borders in columns Body (borders will always appear in Headers")
        pop_style_compact()

        if pygui.begin_table("table1", 3, table.border_flags.value):
            # Display headers so we can inspect their interaction with borders.
            # (Headers are not the main purpose of this section of the demo, so we are not elaborating on them too much. See other sections for details)
            if table.border_display_headers:
                pygui.table_setup_column("One")
                pygui.table_setup_column("Two")
                pygui.table_setup_column("Three")
                pygui.table_headers_row()
            
            for row in range(5):
                pygui.table_next_row()
                for column in range(3):
                    pygui.table_set_column_index(column)
                    buf_text = "Hello {},{}".format(column, row)
                    if table.border_contents_type.value == table.ContentsType.CT_TEXT.value:
                        pygui.text_unformatted(buf_text)
                    elif table.border_contents_type.value == table.ContentsType.CT_FILL_BUTTON.value:
                        pygui.button(buf_text, (-pygui.FLT_MIN, 0))
            pygui.end_table()


        pygui.tree_pop()

    if open_action != -1:
        pygui.set_next_item_open(open_action != 0)
    if pygui.tree_node("Resizable, stretch"):
        # By default, if we don't enable ScrollX the sizing policy for each column is "Stretch"
        # All columns maintain a sizing weight, and they will occupy all available width.
        
        push_style_compact()
        pygui.checkbox_flags("ImGuiTableFlags_Resizable", table.resize_flags, pygui.TABLE_FLAGS_RESIZABLE)
        pygui.checkbox_flags("ImGuiTableFlags_BordersV", table.resize_flags, pygui.TABLE_FLAGS_BORDERS_V)
        pygui.same_line()
        help_marker("Using the _Resizable flag automatically enables the _BordersInnerV flag as well, this is why the resize borders are still showing when unchecking this.")
        pop_style_compact()

        if pygui.begin_table("table1", 3, table.resize_flags.value):
            for row in range(5):
                pygui.table_next_row()
                for column in range(3):
                    pygui.table_set_column_index(column)
                    pygui.text("Hello {},{}".format(column, row))
            pygui.end_table()
        pygui.tree_pop()

    if open_action != -1:
        pygui.set_next_item_open(open_action != 0)
    if pygui.tree_node("Resizable, fixed"):
        help_marker(
            "Using _Resizable + _SizingFixedFit flags.\n"
            "Fixed-width columns generally makes more sense if you want to use horizontal scrolling.\n\n"
            "Double-click a column border to auto-fit the column to its contents.")

        push_style_compact()
        pygui.checkbox_flags("ImGuiTableFlags_NoHostExtendX", table.resize_flags, pygui.TABLE_FLAGS_NO_HOST_EXTEND_X)
        pop_style_compact()

        if pygui.begin_table("table1", 3, table.resize_flags.value):
            for row in range(5):
                pygui.table_next_row()
                for column in range(3):
                    pygui.table_set_column_index(column)
                    pygui.text("Hello {},{}".format(column, row))
            pygui.end_table()
        pygui.tree_pop()

    if open_action != -1:
        pygui.set_next_item_open(open_action != 0)
    if pygui.tree_node("Resizable, mixed"):
        help_marker(
            "Using TableSetupColumn() to alter resizing policy on a per-column basis.\n\n"
            "When combining Fixed and Stretch columns, generally you only want one, maybe two trailing columns to use _WidthStretch.")

        if pygui.begin_table("table1", 3, table.mixed_flags.value):
            pygui.table_setup_column("AAA", pygui.TABLE_COLUMN_FLAGS_WIDTH_FIXED)
            pygui.table_setup_column("BBB", pygui.TABLE_COLUMN_FLAGS_WIDTH_FIXED)
            pygui.table_setup_column("CCC", pygui.TABLE_COLUMN_FLAGS_WIDTH_STRETCH)
            pygui.table_headers_row()
            for row in range(5):
                pygui.table_next_row()
                for column in range(3):
                    pygui.table_set_column_index(column)
                    pygui.text("{} {},{}".format('Stretch' if column == 2 else 'Fixed', column , row))
            pygui.end_table()

        if pygui.begin_table("table2", 6, table.mixed_flags.value):
            pygui.table_setup_column("AAA", pygui.TABLE_COLUMN_FLAGS_WIDTH_FIXED)
            pygui.table_setup_column("BBB", pygui.TABLE_COLUMN_FLAGS_WIDTH_FIXED)
            pygui.table_setup_column("CCC", pygui.TABLE_COLUMN_FLAGS_WIDTH_FIXED | pygui.TABLE_COLUMN_FLAGS_DEFAULT_HIDE)
            pygui.table_setup_column("DDD", pygui.TABLE_COLUMN_FLAGS_WIDTH_STRETCH)
            pygui.table_setup_column("EEE", pygui.TABLE_COLUMN_FLAGS_WIDTH_STRETCH)
            pygui.table_setup_column("FFF", pygui.TABLE_COLUMN_FLAGS_WIDTH_STRETCH | pygui.TABLE_COLUMN_FLAGS_DEFAULT_HIDE)
            pygui.table_headers_row()
            for row in range(5):
                pygui.table_next_row()
                for column in range(6):
                    pygui.table_set_column_index(column)
                    pygui.text("{} {},{}".format('Stretch' if column == 2 else 'Fixed', column , row))
            pygui.end_table()
        pygui.tree_pop()

    if open_action != -1:
        pygui.set_next_item_open(open_action != 0)
    if pygui.tree_node("Reorderable, hideable, with headers"):
        push_style_compact()
        pygui.checkbox_flags("ImGuiTableFlags_Resizable", table.hidable_flags, pygui.TABLE_FLAGS_RESIZABLE)
        pygui.checkbox_flags("ImGuiTableFlags_Reorderable", table.hidable_flags, pygui.TABLE_FLAGS_REORDERABLE)
        pygui.checkbox_flags("ImGuiTableFlags_Hideable", table.hidable_flags, pygui.TABLE_FLAGS_HIDEABLE)
        pygui.checkbox_flags("ImGuiTableFlags_NoBordersInBody", table.hidable_flags, pygui.TABLE_FLAGS_NO_BORDERS_IN_BODY)
        pygui.checkbox_flags("ImGuiTableFlags_NoBordersInBodyUntilResize", table.hidable_flags, pygui.TABLE_FLAGS_NO_BORDERS_IN_BODY_UNTIL_RESIZE)
        pygui.same_line()
        help_marker("Disable vertical borders in columns Body until hovered for resize (borders will always appear in Headers)")
        pop_style_compact()

        if pygui.begin_table("table1", 3, table.hidable_flags.value):
            # Submit column names with table_setup_column() and call table_headers_row() to create a row with a header in each column.
            # (Later we will show how table_setup_column() has other uses, optional flags, sizing weight etc.)
            pygui.table_setup_column("One")
            pygui.table_setup_column("Two")
            pygui.table_setup_column("Three")
            pygui.table_headers_row()
            for row in range(6):
                pygui.table_next_row()
                for column in range(3):
                    pygui.table_set_column_index(column)
                    pygui.text("Hello {},{}".format(column, row))
            pygui.end_table()

        # Use outer_size.x == 0.0f instead of default to make the table as tight as possible (only valid when no scrolling and no stretch column)
        if pygui.begin_table("table2", 3, table.hidable_flags.value | pygui.TABLE_FLAGS_SIZING_FIXED_FIT, (0.0, 0.0)):
            pygui.table_setup_column("One")
            pygui.table_setup_column("Two")
            pygui.table_setup_column("Three")
            pygui.table_headers_row()
            for row in range(6):
                pygui.table_next_row()
                for column in range(3):
                    pygui.table_set_column_index(column)
                    pygui.text("Fixed {},{}".format(column, row))
            pygui.end_table()
        pygui.tree_pop()

    if open_action != -1:
        pygui.set_next_item_open(open_action != 0)
    if pygui.tree_node("Padding"):
        # First example: showcase use of padding flags and effect of BorderOuterV/BorderInnerV on X padding.
        # We don't expose BorderOuterH/BorderInnerH here because they have no effect on X padding.
        help_marker(
            "We often want outer padding activated when any using features which makes the edges of a column visible:\n"
            "e.g.:\n"
            "- BorderOuterV\n"
            "- any form of row selection\n"
            "Because of this, activating BorderOuterV sets the default to PadOuterX. Using PadOuterX or NoPadOuterX you can override the default.\n\n"
            "Actual padding values are using style.CellPadding.\n\n"
            "In this demo we don't show horizontal borders to emphasize how they don't affect default horizontal padding."
        )

        push_style_compact()
        pygui.checkbox_flags("ImGuiTableFlags_PadOuterX", table.padding_flags, pygui.TABLE_FLAGS_PAD_OUTER_X)
        pygui.same_line()
        help_marker("Enable outer-most padding (default if ImGuiTableFlags_BordersOuterV is set)")
        pygui.checkbox_flags("ImGuiTableFlags_NoPadOuterX", table.padding_flags, pygui.TABLE_FLAGS_NO_PAD_OUTER_X)
        pygui.same_line()
        help_marker("Disable outer-most padding (default if ImGuiTableFlags_BordersOuterV is not set)")
        pygui.checkbox_flags("ImGuiTableFlags_NoPadInnerX", table.padding_flags, pygui.TABLE_FLAGS_NO_PAD_INNER_X)
        pygui.same_line()
        help_marker("Disable inner padding between columns (double inner padding if BordersOuterV is on, single inner padding if BordersOuterV is off)")
        pygui.checkbox_flags("ImGuiTableFlags_BordersOuterV", table.padding_flags, pygui.TABLE_FLAGS_BORDERS_OUTER_V)
        pygui.checkbox_flags("ImGuiTableFlags_BordersInnerV", table.padding_flags, pygui.TABLE_FLAGS_BORDERS_INNER_V)
        pygui.checkbox("show_headers", table.padding_show_headers)
        pop_style_compact()

        if pygui.begin_table("table_padding", 3, table.padding_flags.value):
            if table.padding_show_headers:
                pygui.table_setup_column("One")
                pygui.table_setup_column("Two")
                pygui.table_setup_column("Three")
                pygui.table_headers_row()

            for row in range(5):
                pygui.table_next_row()
                for column in range(3):
                    pygui.table_next_column()
                    if row == 0:
                        pygui.text("Avail {:.2f}".format(pygui.get_content_region_avail()[0]))
                    else:
                        pygui.button("Hello {}.{}".format(column, row), (-pygui.FLT_MIN, 0))
            pygui.end_table()

        # Second example: set style.CellPadding to (0.0) or a custom value.
        # FIXME-TABLE: Vertical border effectively not displayed the same way as horizontal one...
        help_marker("Setting style.CellPadding to (0,0) or a custom value.")

        push_style_compact()
        pygui.checkbox_flags("ImGuiTableFlags_Borders", table.padding_flags2, pygui.TABLE_FLAGS_BORDERS)
        pygui.checkbox_flags("ImGuiTableFlags_BordersH", table.padding_flags2, pygui.TABLE_FLAGS_BORDERS_H)
        pygui.checkbox_flags("ImGuiTableFlags_BordersV", table.padding_flags2, pygui.TABLE_FLAGS_BORDERS_V)
        pygui.checkbox_flags("ImGuiTableFlags_BordersInner", table.padding_flags2, pygui.TABLE_FLAGS_BORDERS_INNER)
        pygui.checkbox_flags("ImGuiTableFlags_BordersOuter", table.padding_flags2, pygui.TABLE_FLAGS_BORDERS_OUTER)
        pygui.checkbox_flags("ImGuiTableFlags_RowBg", table.padding_flags2, pygui.TABLE_FLAGS_ROW_BG)
        pygui.checkbox_flags("ImGuiTableFlags_Resizable", table.padding_flags2, pygui.TABLE_FLAGS_RESIZABLE)
        pygui.checkbox("show_widget_frame_bg", table.padding_show_widget_frame_bg)
        pygui.slider_float2("CellPadding", table.padding_cell_padding.as_floatptrs(), 0, 10, "%.0f")
        pop_style_compact()

        pygui.push_style_var(pygui.STYLE_VAR_CELL_PADDING, table.padding_cell_padding.tuple())
        if pygui.begin_table("table_padding_2", 3, table.padding_flags2.value):
            if not table.padding_show_widget_frame_bg:
                pygui.push_style_color(pygui.COL_FRAME_BG, 0)
            
            for cell in range(3 * 5):
                pygui.table_next_column()
                pygui.set_next_item_width(-pygui.FLT_MIN)

                pygui.push_id(cell)
                pygui.input_text("##cell", table.padding_text_bufs[cell])
                pygui.pop_id()

            if not table.padding_show_widget_frame_bg:
                pygui.pop_style_color()
            pygui.end_table()
        
        pygui.pop_style_var()
        pygui.tree_pop()

    if open_action != -1:
        pygui.set_next_item_open(open_action != 0)
    if pygui.tree_node("Sorting"):
        template_item_names = [
            "Banana", "Apple", "Cherry", "Watermelon", "Grapefruit", "Strawberry", "Mango",
            "Kiwi", "Orange", "Pineapple", "Blueberry", "Plum", "Coconut", "Pear", "Apricot"
        ]
        if len(table.sort_items) == 0:
            for n in range(50):
                table.sort_items.append(table.MyItem(
                    n,
                    template_item_names[n % len(template_item_names)],
                    (n * n - n) % 20
                ))
        
        push_style_compact()
        pygui.checkbox_flags("ImGuiTableFlags_SortMulti", table.sort_flags, pygui.TABLE_FLAGS_SORT_MULTI)
        pygui.same_line()
        help_marker("When sorting is enabled: hold shift when clicking headers to sort on multiple column. TableGetSortSpecs() may return specs where (SpecsCount > 1).")
        pygui.checkbox_flags("ImGuiTableFlags_SortTristate", table.sort_flags, pygui.TABLE_FLAGS_SORT_TRISTATE)
        pygui.same_line()
        help_marker("When sorting is enabled: allow no sorting, disable default sorting. TableGetSortSpecs() may return specs where (SpecsCount == 0).")
        pop_style_compact()

        if pygui.begin_table("table_sorting", 4, table.sort_flags.value, (0, TEXT_BASE_HEIGHT * 15), 0):
            # Declare columns
            # We use the "user_id" parameter of TableSetupColumn() to specify a user id that will be stored in the sort specifications.
            # This is so our sort function can identify a column given our own identifier. We could also identify them based on their index!
            # Demonstrate using a mixture of flags among available sort-related flags:
            # - ImGuiTableColumnFlags_DefaultSort
            # - ImGuiTableColumnFlags_NoSort / ImGuiTableColumnFlags_NoSortAscending / ImGuiTableColumnFlags_NoSortDescending
            # - ImGuiTableColumnFlags_PreferSortAscending / ImGuiTableColumnFlags_PreferSortDescending
            pygui.table_setup_column("ID", pygui.TABLE_COLUMN_FLAGS_DEFAULT_SORT | pygui.TABLE_COLUMN_FLAGS_WIDTH_FIXED,                   0, table.MyItemColumnID.ID.value)
            pygui.table_setup_column("Name", pygui.TABLE_COLUMN_FLAGS_WIDTH_FIXED,                                                               0, table.MyItemColumnID.Name.value)
            pygui.table_setup_column("Action", pygui.TABLE_COLUMN_FLAGS_NO_SORT | pygui.TABLE_COLUMN_FLAGS_WIDTH_FIXED,                    0, table.MyItemColumnID.Action.value)
            pygui.table_setup_column("Quantity", pygui.TABLE_COLUMN_FLAGS_PREFER_SORT_DESCENDING | pygui.TABLE_COLUMN_FLAGS_WIDTH_STRETCH, 0, table.MyItemColumnID.Quantity.value)
            pygui.table_setup_scroll_freeze(0, 1) # Make row always visible
            pygui.table_headers_row()

            def custom_key(element: table.MyItem):
                sort_specs = pygui.table_get_sort_specs()
                sort_with = []
                for sort_spec in sort_specs.specs:
                    compare_obj = None
                    compare_obj = element.get_column_field(sort_spec.column_index)
                    # Or instead of using column_index you could directly check the value of
                    # column_user_id, (passed into pygui.table_setup_column()) to then add
                    # the corresponding field to the tuple. That setup is commented out below.

                    # if sort_spec.column_user_id == table.MyItemColumnID.ID.value:
                    #     compare_obj = element._id
                    # elif sort_spec.column_user_id == table.MyItemColumnID.Name.value:
                    #     compare_obj = element.name
                    # elif sort_spec.column_user_id == table.MyItemColumnID.Quantity.value:
                    #     compare_obj = element.quantity
                    # elif sort_spec.column_user_id == table.MyItemColumnID.Description.value:
                    #     compare_obj = element.name
                    
                    if sort_spec.sort_direction == pygui.SORT_DIRECTION_DESCENDING:
                        compare_obj = table.negated(compare_obj)
                    sort_with.append(compare_obj)
                # Add a default sorting method
                sort_with.append(element._id)
                return tuple(sort_with)

            # Sort our data if sort specs have been changed!
            """
            Python note: This sorting process is much easier as we can use the sort function
            to sort our list. But we still need to pass a suitable key function to ensure
            that it is sorted based on the information provided to us from ImGui. This is
            where ImGuiTableSortSpecs comes in. This class provides information about the
            sort itself. Here we use it to determine if we need to resort the list. This is
            to prevent us from needing to sort the list every frame.

            Secondly, the custom_key function above uses the information inside
            ImGuiTableSortSpecs.specs to retreive a List of ImGuiTableColumnSortSpecs. These
            contain information about the columns we are to sort on:
             - Which column?
             - Descending (def) of Ascending?
            The custom_key function returns a tuple containing the elements that will be
            used inside the sort function to compare each element.
            """
            if (sort_specs := pygui.table_get_sort_specs()):
                if sort_specs.specs_dirty:
                    table.sort_items.sort(key=custom_key)
                sort_specs.specs_dirty = False
            
            # Demonstrate using clipper for large vertical lists
            clipper = pygui.ImGuiListClipper.create()

            # This is our first example of not being able to share heap objects
            # across the dll. I need to get a pointer to a valid type that it
            # creates, not me. This requires adding a custom constructor and 
            # destructor for the ImGuiListClipper class.
            clipper.begin(len(table.sort_items))
            while clipper.step():
                for row_n in range(clipper.display_start, clipper.display_end):
                    # Display a data item
                    item: table.MyItem = table.sort_items[row_n]
                    pygui.push_id(item._id)
                    pygui.table_next_row()
                    pygui.table_next_column()
                    pygui.text("{:.4f}".format(item._id))
                    pygui.table_next_column()
                    pygui.text_unformatted(item.name)
                    pygui.table_next_column()
                    pygui.small_button("None")
                    pygui.table_next_column()
                    pygui.text("{}".format(item.quantity))
                    pygui.pop_id()
            clipper.destroy()

            pygui.end_table()
        pygui.tree_pop()

    pygui.pop_id()

    if table.disable_indent:
        pygui.pop_style_var()


class rand:
    string_test = pygui.String()
    begin_disabled = pygui.Bool(True)
    first_checkbox = pygui.Bool(False)
    second_checkbox = pygui.Bool(False)
    third_checkbox = pygui.Bool(False)
    modal_checkbox = pygui.Bool(False)
    payload_message = None
    colour = pygui.Vec4(1, 1, 0, 1)
    current_item = pygui.Int()
    current_item_list = pygui.Int()
    error_text = [(1, 0, 0, 1), ""]
    utf8_string = pygui.String("Hello")
    drag_min = pygui.Int(1)
    drag_max = pygui.Int(100)
    drag = pygui.Int(50)
    drag_float_min = pygui.Float(0.001)
    drag_float_max = pygui.Float(0.100)
    drag_float = pygui.Float(0.05)
    multiline_buffer = pygui.String()
    left_click_count = pygui.Int()
    is_activated = False
    is_deactivated = False
    edit_float = pygui.Float(5)
    is_deactivated_after_edit = False
    viewport_selection = pygui.Int(0)
    show_monitors = pygui.Bool(False)
    monitors_visible = []
    is_edited = False
    checkboxes = [pygui.Bool(False) for _ in range(10)]
    key_press_log = []
    mouse_press_log = []
    show_window = pygui.Bool(False)
    window_log = []
    input_type = pygui.Int(0)
    input_buffer = pygui.String("", 32)
    input_buffer_log = []
    input_buffer_do_always = pygui.Bool(False)
    input_flags = pygui.Int(
            pygui.INPUT_TEXT_FLAGS_CALLBACK_COMPLETION |\
            pygui.INPUT_TEXT_FLAGS_CALLBACK_HISTORY |\
            pygui.INPUT_TEXT_FLAGS_CALLBACK_CHAR_FILTER |\
            # pygui.INPUT_TEXT_FLAGS_CALLBACK_RESIZE |\
            pygui.INPUT_TEXT_FLAGS_CALLBACK_EDIT)
    tree_checkboxes = [pygui.Bool(False) for _ in range(3)]
    text_input = [pygui.String() for _ in range(3)]
    next_window_docked = pygui.Bool(True)
    next_window_dock_window_spawned = pygui.Bool(True)
    next_window_alpha = pygui.Float(1)
    next_window_collapsed = pygui.Bool(False)
    next_window_do_size = pygui.Bool(False)
    next_window_in_main_viewport = pygui.Bool(False)
    next_window_size = pygui.Vec2(500, 400)
    next_window_do_size_constraint = pygui.Bool(False)
    next_window_do_size_constraint_do_callback = pygui.Bool(False)
    callback_log = []
    next_window_size_constraint_min = pygui.Vec2(10, 10)
    next_window_size_constraint_max = pygui.Vec2(300, 300)
    next_window_content_size = pygui.Vec2(500, 400)
    next_window_scroll = pygui.Vec2(-1, -1)
    next_window_focus = pygui.Bool(False)
    next_window_spawned = pygui.Bool(True)
    frame_delta_count = 0
    df = [(i, "Entry" + str(i * 43 % 100)) for i in range(30)]
    jump_to_cache = []
    jump_to = pygui.Int(0)
    text_filter = pygui.ImGuiTextFilter.create()


def show_random_extras():
    if not pygui.collapsing_header("Random Extras"):
        return

    pygui.push_style_var(pygui.STYLE_VAR_INDENT_SPACING, 30)
    if pygui.tree_node("Info functions"):
        pygui.text("pygui.get_font_size(): {}".format(pygui.get_font_size()))
        pygui.text("pygui.get_font_tex_uv_white_pixel(): {}".format(pygui.get_font_tex_uv_white_pixel()))
        pygui.text("pygui.get_content_region_max(): {}".format(pygui.get_content_region_max()))
        pygui.text("pygui.get_cursor_pos_x(): {}".format(pygui.get_cursor_pos_x()))
        pygui.text("pygui.get_cursor_pos_y(): {}".format(pygui.get_cursor_pos_y()))
        pygui.text("pygui.get_mouse_pos(): {}".format(pygui.get_mouse_pos()))
        pygui.text("pygui.get_frame_count(): {}".format(pygui.get_frame_count()))
        left_click_count = pygui.get_mouse_clicked_count(pygui.MOUSE_BUTTON_LEFT)
        left_click_string = "pygui.get_mouse_clicked_count(pygui.MOUSE_BUTTON_LEFT): {}"
        if left_click_count == 0:
            pygui.text(left_click_string.format(rand.left_click_count.value))
        else:
            rand.left_click_count.value = left_click_count
            pygui.text(left_click_string.format(left_click_count))
        pygui.text("pygui.get_mouse_cursor(): {}".format(pygui.get_mouse_cursor()))
        pygui.text("pygui.get_window_content_region_max(): {}".format(pygui.get_window_content_region_max()))
        pygui.text("pygui.get_window_content_region_min(): {}".format(pygui.get_window_content_region_min()))
        pygui.text("pygui.get_window_dock_id(): {}".format(pygui.get_window_dock_id()))
        pygui.text("pygui.get_window_dpi_scale(): {}".format(pygui.get_window_dpi_scale()))
        pygui.text("pygui.get_window_height(): {}".format(pygui.get_window_height()))
        pygui.text("pygui.get_window_width(): {}".format(pygui.get_window_width()))
        # This function should be omitted from the cimgui API!
        # pygui.text("pygui.get_key_index(pygui.KEY_A): {}".format(pygui.get_key_index(pygui.KEY_A)))
        viewport = pygui.get_window_viewport()
        pygui.text("pygui.get_window_viewport(): {}".format(viewport))
        pygui.text("viewport.pos: {}".format(viewport.pos))
        pygui.text("pygui.is_any_item_active(): {}".format(pygui.is_any_item_active()))
        pygui.text("pygui.is_any_item_focused(): {}".format(pygui.is_any_item_focused()))
        pygui.text("pygui.is_any_item_hovered(): {}".format(pygui.is_any_item_hovered()))
        pygui.text("pygui.is_any_mouse_down(): {}".format(pygui.is_any_mouse_down()))
        pygui.tree_pop()

    if pygui.tree_node("Reading Structs"):
        def show_imfontglyph(glyph: pygui.ImFontGlyph):
            pygui.menu_item("glyph.advance_x:   {}".format(glyph.advance_x))
            pygui.menu_item("glyph.codepoint:   {}".format(glyph.codepoint))
            pygui.menu_item("glyph.colored:     {}".format(glyph.colored))
            pygui.menu_item("glyph.u0:          {}".format(glyph.u0))
            pygui.menu_item("glyph.u1:          {}".format(glyph.u1))
            pygui.menu_item("glyph.v0:          {}".format(glyph.v0))
            pygui.menu_item("glyph.v1:          {}".format(glyph.v1))
            pygui.menu_item("glyph.visible:     {}".format(glyph.visible))
            pygui.menu_item("glyph.x0:          {}".format(glyph.x0))
            pygui.menu_item("glyph.x1:          {}".format(glyph.x1))
            pygui.menu_item("glyph.y0:          {}".format(glyph.y0))
            pygui.menu_item("glyph.y1:          {}".format(glyph.y1))
        
        def show_imfontconfig(config: pygui.ImFontConfig):
            if pygui.begin_menu("config.dst_font"):
                show_imfont(config.dst_font)
                pygui.end_menu()
            pygui.menu_item("config.ellipsis_char:           {} {}".format(config.ellipsis_char, chr(config.ellipsis_char)))
            pygui.menu_item("config.font_builder_flags:      {}".format(config.font_builder_flags))
            pygui.menu_item("config.font_data_owned_by_atlas: {}".format(config.font_data_owned_by_atlas))
            pygui.menu_item("config.font_data_size:          {}".format(config.font_data_size))
            pygui.menu_item("config.font_no:                 {}".format(config.font_no))
            pygui.menu_item("config.glyph_extra_spacing:     {}".format(config.glyph_extra_spacing))
            pygui.menu_item("config.glyph_max_advance_x:     {}".format(config.glyph_max_advance_x))
            pygui.menu_item("config.glyph_min_advance_x:     {}".format(config.glyph_min_advance_x))
            pygui.menu_item("config.glyph_offset:            {}".format(config.glyph_offset))
            pygui.menu_item("config.merge_mode:              {}".format(config.merge_mode))
            pygui.menu_item("config.name:                    {}".format(config.name))
            pygui.menu_item("config.oversample_h:            {}".format(config.oversample_h))
            pygui.menu_item("config.oversample_v:            {}".format(config.oversample_v))
            pygui.menu_item("config.pixel_snap_h:            {}".format(config.pixel_snap_h))
            pygui.menu_item("config.rasterizer_multiply:     {}".format(config.rasterizer_multiply))

        def show_imfontatlas(atlas: pygui.ImFontAtlas):
            if pygui.begin_menu("atlas.config_data"):
                for i, config in enumerate(atlas.config_data):
                    if pygui.begin_menu(f"Config:  {i}"):
                        show_imfontconfig(config)
                        pygui.end_menu()
                pygui.end_menu()
            if pygui.begin_menu("atlas.custom_rects"):
                for i, rect in enumerate(atlas.custom_rects):
                    if pygui.begin_menu(f"Custom Rect:  {i}"):
                        show_imfontatlascustomrect(rect)
                        pygui.end_menu()
                pygui.end_menu()
            pygui.menu_item("atlas.flags:                   {}".format(atlas.flags))
            pygui.menu_item("atlas.font_builder_flags:      {}".format(atlas.font_builder_flags))
            pygui.menu_item("atlas.font_builder_io:         {}".format(atlas.font_builder_io))
            if pygui.begin_menu("atlas.fonts"):
                for i, font in enumerate(atlas.fonts):
                    if pygui.begin_menu(f"Font:  {i}"):
                        show_imfont(font)
                        pygui.end_menu()
                pygui.end_menu()
            pygui.menu_item("atlas.locked:                  {}".format(atlas.locked))
            pygui.menu_item("atlas.pack_id_lines:           {}".format(atlas.pack_id_lines))
            pygui.menu_item("atlas.pack_id_mouse_cursors:   {}".format(atlas.pack_id_mouse_cursors))
            pygui.menu_item("atlas.tex_desired_width:       {}".format(atlas.tex_desired_width))
            pygui.menu_item("atlas.tex_glyph_padding:       {}".format(atlas.tex_glyph_padding))
            pygui.menu_item("atlas.tex_height:              {}".format(atlas.tex_height))
            pygui.menu_item("atlas.tex_id:                  {}".format(atlas.tex_id))
            if pygui.begin_menu("atlas.tex_pixels_alpha8"):
                for i, byte in enumerate(atlas.tex_pixels_alpha8):
                    pygui.menu_item("Byte {}:  {}".format(i, byte))
                pygui.end_menu()
            if pygui.begin_menu("atlas.tex_pixels_rgba_32"):
                bytes = atlas.tex_pixels_rgba_32
                for i in range(len(bytes) // 4):
                    cur = int.from_bytes(bytes[i:i+4], "big")
                    pygui.menu_item("Byte {}:  {}".format(i, cur))
                pygui.end_menu()
            pygui.menu_item("atlas.tex_pixels_use_colors:   {}".format(atlas.tex_pixels_use_colors))
            pygui.menu_item("atlas.tex_ready:               {}".format(atlas.tex_ready))
            pygui.menu_item("atlas.tex_uv_lines:            {}".format(atlas.tex_uv_lines.tuple()))
            pygui.menu_item("atlas.tex_uv_scale:            {}".format(atlas.tex_uv_scale))
            pygui.menu_item("atlas.tex_uv_white_pixel:      {}".format(atlas.tex_uv_white_pixel))
            pygui.menu_item("atlas.tex_width:               {}".format(atlas.tex_width))

        def show_imfontatlascustomrect(rect: pygui.ImFontAtlasCustomRect):
            if rect.font is not None:
                if pygui.begin_menu("rect.font"):
                    show_imfont(rect.font)
                    pygui.end_menu()
            else:
                pygui.menu_item("rect.font:             {}".format(None))
            pygui.menu_item("rect.glyph_advance_x:  {}".format(rect.glyph_advance_x))
            pygui.menu_item("rect.glyph_id:         {}".format(rect.glyph_id))
            pygui.menu_item("rect.glyph_offset:     {}".format(rect.glyph_offset))
            pygui.menu_item("rect.height:           {}".format(rect.height))
            pygui.menu_item("rect.width:            {}".format(rect.width))
            pygui.menu_item("rect.x:                {}".format(rect.x))
            pygui.menu_item("rect.y:                {}".format(rect.y))
            pygui.menu_item("rect.is_packed():      {}".format(rect.is_packed()))

        def show_imfont(font: pygui.ImFont):
            pygui.menu_item("font.ascent:                {}".format(font.ascent))
            if pygui.begin_menu("font.config_data"):
                show_imfontconfig(font.config_data)
                pygui.end_menu()
            pygui.menu_item("font.config_data_count:     {}".format(font.config_data_count))
            if pygui.begin_menu("font.container_atlas"):
                show_imfontatlas(font.container_atlas)
                pygui.end_menu()
            pygui.menu_item("font.descent:               {}".format(font.descent))
            pygui.menu_item("font.dirty_lookup_tables:   {}".format(font.dirty_lookup_tables))
            pygui.menu_item("font.ellipsis_char:         {} {}".format(font.ellipsis_char, chr(font.ellipsis_char)))
            pygui.menu_item("font.ellipsis_char_count:   {}".format(font.ellipsis_char_count))
            pygui.menu_item("font.ellipsis_char_step:    {}".format(font.ellipsis_char_step))
            pygui.menu_item("font.ellipsis_width:        {}".format(font.ellipsis_width))
            pygui.menu_item("font.fallback_advance_x:    {}".format(font.fallback_advance_x))
            pygui.menu_item("font.fallback_char:         {} {}".format(font.fallback_char, chr(font.fallback_char)))
            if pygui.begin_menu("font.fallback_glyph"):
                show_imfontglyph(font.fallback_glyph)
                pygui.end_menu()
            pygui.menu_item("font.font_size:             {}".format(font.font_size))
            if pygui.begin_menu("font.glyphs"):
                for glyph in font.glyphs:
                    if pygui.begin_menu("Glyph {}:    {}  ".format(glyph.codepoint, chr(glyph.codepoint))):
                        show_imfontglyph(glyph)
                        pygui.end_menu()
                pygui.end_menu()
            if pygui.begin_menu("font.index_advance_x"):
                for i, flt in enumerate(font.index_advance_x):
                    # chr(0) turns into a null character which terminates the string in c.
                    # Very interesting that I can control that.
                    pygui.menu_item("For char {} '{}':  {}".format(i, chr(i) if i != 0 else "\\0", flt))
                pygui.end_menu()
            if pygui.begin_menu("font.index_lookup"):
                for i, _int in enumerate(font.index_lookup):
                    pygui.menu_item("For char {} '{}':  {}".format(i, chr(i) if i != 0 else "\\0", _int))
                pygui.end_menu()
            pygui.menu_item("font.metrics_total_surface: {}".format(font.metrics_total_surface))
            pygui.menu_item("font.scale:                 {}".format(font.scale))
        
        def show_imguiio(io: pygui.ImGuiIO):
            pygui.menu_item("io.app_accepting_events:                   {}".format(io.app_accepting_events))
            pygui.menu_item("io.app_focus_lost:                         {}".format(io.app_focus_lost))
            pygui.menu_item("io.backend_flags:                          {}".format(io.backend_flags))
            pygui.menu_item("io.backend_platform_name:                  {}".format(io.backend_platform_name))
            pygui.menu_item("io.backend_renderer_name:                  {}".format(io.backend_renderer_name))
            pygui.menu_item("io.backend_using_legacy_key_arrays:        {}".format(io.backend_using_legacy_key_arrays))
            pygui.menu_item("io.backend_using_legacy_nav_input_array:   {}".format(io.backend_using_legacy_nav_input_array))
            pygui.menu_item("io.config_debug_begin_return_value_loop:   {}".format(io.config_debug_begin_return_value_loop))
            pygui.menu_item("io.config_debug_begin_return_value_once:   {}".format(io.config_debug_begin_return_value_once))
            pygui.menu_item("io.config_docking_always_tab_bar:          {}".format(io.config_docking_always_tab_bar))
            pygui.menu_item("io.config_docking_no_split:                {}".format(io.config_docking_no_split))
            pygui.menu_item("io.config_docking_transparent_payload:     {}".format(io.config_docking_transparent_payload))
            pygui.menu_item("io.config_docking_with_shift:              {}".format(io.config_docking_with_shift))
            pygui.menu_item("io.config_drag_click_to_input_text:        {}".format(io.config_drag_click_to_input_text))
            pygui.menu_item("io.config_flags:                           {}".format(io.config_flags))
            pygui.menu_item("io.config_input_text_cursor_blink:         {}".format(io.config_input_text_cursor_blink))
            pygui.menu_item("io.config_input_text_enter_keep_active:    {}".format(io.config_input_text_enter_keep_active))
            pygui.menu_item("io.config_input_trickle_event_queue:       {}".format(io.config_input_trickle_event_queue))
            pygui.menu_item("io.config_mac_osx_behaviors:               {}".format(io.config_mac_osx_behaviors))
            pygui.menu_item("io.config_memory_compact_timer:            {}".format(io.config_memory_compact_timer))
            pygui.menu_item("io.config_viewports_no_auto_merge:         {}".format(io.config_viewports_no_auto_merge))
            pygui.menu_item("io.config_viewports_no_decoration:         {}".format(io.config_viewports_no_decoration))
            pygui.menu_item("io.config_viewports_no_default_parent:     {}".format(io.config_viewports_no_default_parent))
            pygui.menu_item("io.config_viewports_no_task_bar_icon:      {}".format(io.config_viewports_no_task_bar_icon))
            pygui.menu_item("io.config_windows_move_from_title_bar_only:{}".format(io.config_windows_move_from_title_bar_only))
            pygui.menu_item("io.config_windows_resize_from_edges:       {}".format(io.config_windows_resize_from_edges))
            pygui.menu_item("io.ctx:                                    {}".format(io.ctx.__class__))
            pygui.menu_item("io.delta_time:                             {}".format(io.delta_time))
            pygui.menu_item("io.display_framebuffer_scale:              {}".format(io.display_framebuffer_scale))
            pygui.menu_item("io.display_size:                           {}".format(io.display_size))
            pygui.menu_item("io.font_allow_user_scaling:                {}".format(io.font_allow_user_scaling))
            if io.font_default is not None:
                if pygui.begin_menu("io.font_default"):
                    show_imfont(io.font_default)
                    pygui.end_menu()
            else:
                pygui.menu_item("io.font_default:                           {}".format(None))
            pygui.menu_item("io.font_global_scale:                      {}".format(io.font_global_scale))
            if pygui.begin_menu("io.fonts"):
                show_imfontatlas(io.fonts)
                pygui.end_menu()
            pygui.menu_item("io.framerate:                              {}".format(io.framerate))
            pygui.menu_item("io.get_clipboard_text_fn:                  {}".format(io.get_clipboard_text_fn))
            pygui.menu_item("io.hover_delay_normal:                     {}".format(io.hover_delay_normal))
            pygui.menu_item("io.hover_delay_short:                      {}".format(io.hover_delay_short))
            pygui.menu_item("io.ini_filename:                           {}".format(io.ini_filename))
            pygui.menu_item("io.ini_saving_rate:                        {}".format(io.ini_saving_rate))
            pygui.menu_item("io.input_queue_characters:                 {}".format(io.input_queue_characters))
            pygui.menu_item("io.input_queue_surrogate:                  {}".format(io.input_queue_surrogate))
            pygui.menu_item("io.key_alt:                                {}".format(io.key_alt))
            pygui.menu_item("io.key_ctrl:                               {}".format(io.key_ctrl))
            pygui.menu_item("io.key_mods:                               {}".format(io.key_mods))
            pygui.menu_item("io.key_repeat_delay:                       {}".format(io.key_repeat_delay))
            pygui.menu_item("io.key_repeat_rate:                        {}".format(io.key_repeat_rate))
            pygui.menu_item("io.key_shift:                              {}".format(io.key_shift))
            pygui.menu_item("io.key_super:                              {}".format(io.key_super))
            if pygui.begin_menu("io.keys_data"):
                show_imguikeydata(io.keys_data)
                pygui.end_menu()
            pygui.menu_item("io.log_filename:                           {}".format(io.log_filename))
            pygui.menu_item("io.metrics_active_allocations:             {}".format(io.metrics_active_allocations))
            pygui.menu_item("io.metrics_active_windows:                 {}".format(io.metrics_active_windows))
            pygui.menu_item("io.metrics_render_indices:                 {}".format(io.metrics_render_indices))
            pygui.menu_item("io.metrics_render_vertices:                {}".format(io.metrics_render_vertices))
            pygui.menu_item("io.metrics_render_windows:                 {}".format(io.metrics_render_windows))
            pygui.menu_item("io.mouse_clicked:                          {}".format(io.mouse_clicked))
            pygui.menu_item("io.mouse_clicked_count:                    {}".format(io.mouse_clicked_count))
            pygui.menu_item("io.mouse_clicked_last_count:               {}".format(io.mouse_clicked_last_count))
            pygui.menu_item("io.mouse_clicked_pos:                      {}".format(io.mouse_clicked_pos))
            pygui.menu_item("io.mouse_clicked_time:                     {}".format(io.mouse_clicked_time))
            pygui.menu_item("io.mouse_delta:                            {}".format(io.mouse_delta))
            pygui.menu_item("io.mouse_double_click_max_dist:            {}".format(io.mouse_double_click_max_dist))
            pygui.menu_item("io.mouse_double_click_time:                {}".format(io.mouse_double_click_time))
            pygui.menu_item("io.mouse_double_clicked:                   {}".format(io.mouse_double_clicked))
            pygui.menu_item("io.mouse_down:                             {}".format(io.mouse_down))
            pygui.menu_item("io.mouse_down_duration:                    {}".format(io.mouse_down_duration))
            pygui.menu_item("io.mouse_down_duration_prev:               {}".format(io.mouse_down_duration_prev))
            pygui.menu_item("io.mouse_down_owned:                       {}".format(io.mouse_down_owned))
            pygui.menu_item("io.mouse_down_owned_unless_popup_close:    {}".format(io.mouse_down_owned_unless_popup_close))
            pygui.menu_item("io.mouse_drag_max_distance_abs:            {}".format(io.mouse_drag_max_distance_abs))
            pygui.menu_item("io.mouse_drag_max_distance_sqr:            {}".format(io.mouse_drag_max_distance_sqr))
            pygui.menu_item("io.mouse_drag_threshold:                   {}".format(io.mouse_drag_threshold))
            pygui.menu_item("io.mouse_draw_cursor:                      {}".format(io.mouse_draw_cursor))
            pygui.menu_item("io.mouse_hovered_viewport:                 {}".format(io.mouse_hovered_viewport))
            pygui.menu_item("io.mouse_pos:                              {}".format(io.mouse_pos))
            pygui.menu_item("io.mouse_pos_prev:                         {}".format(io.mouse_pos_prev))
            pygui.menu_item("io.mouse_released:                         {}".format(io.mouse_released))
            pygui.menu_item("io.mouse_source:                           {}".format(io.mouse_source))
            pygui.menu_item("io.mouse_wheel:                            {}".format(io.mouse_wheel))
            pygui.menu_item("io.mouse_wheel_h:                          {}".format(io.mouse_wheel_h))
            pygui.menu_item("io.mouse_wheel_request_axis_swap:          {}".format(io.mouse_wheel_request_axis_swap))
            pygui.menu_item("io.nav_active:                             {}".format(io.nav_active))
            pygui.menu_item("io.nav_visible:                            {}".format(io.nav_visible))
            pygui.menu_item("io.pen_pressure:                           {}".format(io.pen_pressure))
            pygui.menu_item("io.set_clipboard_text_fn:                  {}".format(io.set_clipboard_text_fn))
            pygui.menu_item("io.user_data:                              {}".format(io.user_data))
            pygui.menu_item("io.want_capture_keyboard:                  {}".format(io.want_capture_keyboard))
            pygui.menu_item("io.want_capture_mouse:                     {}".format(io.want_capture_mouse))
            pygui.menu_item("io.want_capture_mouse_unless_popup_close:  {}".format(io.want_capture_mouse_unless_popup_close))
            pygui.menu_item("io.want_save_ini_settings:                 {}".format(io.want_save_ini_settings))
            pygui.menu_item("io.want_set_mouse_pos:                     {}".format(io.want_set_mouse_pos))
            pygui.menu_item("io.want_text_input:                        {}".format(io.want_text_input))

        def show_imguikeydata(kd: pygui.ImGuiKeyData):
            pygui.menu_item("kd.analog_value: {}".format(kd.analog_value))
            pygui.menu_item("kd.down: {}".format(kd.down))
            pygui.menu_item("kd.down_duration: {}".format(kd.down_duration))
            pygui.menu_item("kd.down_duration_prev: {}".format(kd.down_duration_prev))

        def show_imguistyle(style: pygui.ImGuiStyle):
            pygui.menu_item("style.alpha:                           {}".format(style.alpha))
            pygui.menu_item("style.anti_aliased_fill:               {}".format(style.anti_aliased_fill))
            pygui.menu_item("style.anti_aliased_lines:              {}".format(style.anti_aliased_lines))
            pygui.menu_item("style.anti_aliased_lines_use_tex:      {}".format(style.anti_aliased_lines_use_tex))
            pygui.menu_item("style.button_text_align:               {}".format(style.button_text_align))
            pygui.menu_item("style.cell_padding:                    {}".format(style.cell_padding))
            pygui.menu_item("style.child_border_size:               {}".format(style.child_border_size))
            pygui.menu_item("style.child_rounding:                  {}".format(style.child_rounding))
            pygui.menu_item("style.circle_tessellation_max_error:   {}".format(style.circle_tessellation_max_error))
            pygui.menu_item("style.color_button_position:           {}".format(style.color_button_position))
            pygui.menu_item("style.colors:                          {}".format(style.colors))
            pygui.menu_item("style.columns_min_spacing:             {}".format(style.columns_min_spacing))
            pygui.menu_item("style.curve_tessellation_tol:          {}".format(style.curve_tessellation_tol))
            pygui.menu_item("style.disabled_alpha:                  {}".format(style.disabled_alpha))
            pygui.menu_item("style.display_safe_area_padding:       {}".format(style.display_safe_area_padding))
            pygui.menu_item("style.display_window_padding:          {}".format(style.display_window_padding))
            pygui.menu_item("style.frame_border_size:               {}".format(style.frame_border_size))
            pygui.menu_item("style.frame_padding:                   {}".format(style.frame_padding))
            pygui.menu_item("style.frame_rounding:                  {}".format(style.frame_rounding))
            pygui.menu_item("style.grab_min_size:                   {}".format(style.grab_min_size))
            pygui.menu_item("style.grab_rounding:                   {}".format(style.grab_rounding))
            pygui.menu_item("style.indent_spacing:                  {}".format(style.indent_spacing))
            pygui.menu_item("style.item_inner_spacing:              {}".format(style.item_inner_spacing))
            pygui.menu_item("style.item_spacing:                    {}".format(style.item_spacing))
            pygui.menu_item("style.log_slider_deadzone:             {}".format(style.log_slider_deadzone))
            pygui.menu_item("style.mouse_cursor_scale:              {}".format(style.mouse_cursor_scale))
            pygui.menu_item("style.popup_border_size:               {}".format(style.popup_border_size))
            pygui.menu_item("style.popup_rounding:                  {}".format(style.popup_rounding))
            pygui.menu_item("style.scrollbar_rounding:              {}".format(style.scrollbar_rounding))
            pygui.menu_item("style.scrollbar_size:                  {}".format(style.scrollbar_size))
            pygui.menu_item("style.selectable_text_align:           {}".format(style.selectable_text_align))
            pygui.menu_item("style.separator_text_align:            {}".format(style.separator_text_align))
            pygui.menu_item("style.separator_text_border_size:      {}".format(style.separator_text_border_size))
            pygui.menu_item("style.separator_text_padding:          {}".format(style.separator_text_padding))
            pygui.menu_item("style.tab_border_size:                 {}".format(style.tab_border_size))
            pygui.menu_item("style.tab_min_width_for_close_button:  {}".format(style.tab_min_width_for_close_button))
            pygui.menu_item("style.tab_rounding:                    {}".format(style.tab_rounding))
            pygui.menu_item("style.touch_extra_padding:             {}".format(style.touch_extra_padding))
            pygui.menu_item("style.window_border_size:              {}".format(style.window_border_size))
            pygui.menu_item("style.window_menu_button_position:     {}".format(style.window_menu_button_position))
            pygui.menu_item("style.window_min_size:                 {}".format(style.window_min_size))
            pygui.menu_item("style.window_padding:                  {}".format(style.window_padding))
            pygui.menu_item("style.window_rounding:                 {}".format(style.window_rounding))
            pygui.menu_item("style.window_title_align:              {}".format(style.window_title_align))

        def show_imguiviewport(vp: pygui.ImGuiViewport):
            pygui.menu_item("vp.dpi_scale:                  {}".format(vp.dpi_scale))
            pygui.menu_item("vp.draw_data:                  {}".format(vp.draw_data))
            pygui.menu_item("vp.flags:                      {}".format(vp.flags))
            pygui.menu_item("vp.id:                         {}".format(vp.id))
            pygui.menu_item("vp.parent_viewport_id:         {}".format(vp.parent_viewport_id))
            pygui.menu_item("vp.platform_request_close:     {}".format(vp.platform_request_close))
            pygui.menu_item("vp.platform_request_move:      {}".format(vp.platform_request_move))
            pygui.menu_item("vp.platform_request_resize:    {}".format(vp.platform_request_resize))
            pygui.menu_item("vp.platform_window_created:    {}".format(vp.platform_window_created))
            pygui.menu_item("vp.pos:                        {}".format(vp.pos))
            pygui.menu_item("vp.size:                       {}".format(vp.size))
            pygui.menu_item("vp.work_pos:                   {}".format(vp.work_pos))
            pygui.menu_item("vp.work_size:                  {}".format(vp.work_size))
            pygui.menu_item("vp.get_center():               {}".format(vp.get_center()))
            pygui.menu_item("vp.get_work_center():          {}".format(vp.get_work_center()))

        def show_imdrawlist(dl: pygui.ImDrawList):
            if dl.cmd_buffer is not None:
                if pygui.begin_menu("dl.cmd_buffer"):
                    for i, cmd in enumerate(dl.cmd_buffer):
                        if pygui.begin_menu("Command:  {}".format(i)):
                            show_imdrawcmd(cmd)
                            pygui.end_menu()
                    pygui.end_menu()
            else:
                pygui.menu_item("dl.cmd_buffer: {}".format(None))
            pygui.menu_item("dl.flags: {}".format(dl.flags))
            pygui.menu_item("dl.idx_buffer: {}".format(dl.idx_buffer))
            pygui.menu_item("dl.owner_name: {}".format(dl.owner_name))
            if pygui.begin_menu("dl.vtx_buffer"):
                for i, vert in enumerate(dl.vtx_buffer):
                    if pygui.begin_menu("Vertex:  {}".format(i)):
                        show_imdrawvert(vert)
                        pygui.end_menu()
                pygui.end_menu()

        def show_imdrawvert(vert: pygui.ImDrawVert):
            pygui.menu_item("vert.col: {}".format(vert.col))
            pygui.menu_item("vert.pos: {}".format(vert.pos))
            pygui.menu_item("vert.uv: {}".format(vert.uv))

        def show_imdrawcmd(cmd: pygui.ImDrawCmd):
            pygui.menu_item("cmd.clip_rect: {}".format(cmd.clip_rect))
            pygui.menu_item("cmd.elem_count: {}".format(cmd.elem_count))
            pygui.menu_item("cmd.idx_offset: {}".format(cmd.idx_offset))
            pygui.menu_item("cmd.vtx_offset: {}".format(cmd.vtx_offset))

        font = pygui.get_font()
        if pygui.begin_menu("pygui.get_font()"):
            show_imfont(font)
            pygui.end_menu()

        io = pygui.get_io()
        if pygui.begin_menu("pygui.get_io()"):
            show_imguiio(io)
            pygui.end_menu()

        style = pygui.get_style()
        if pygui.begin_menu("pygui.get_style()"):
            show_imguistyle(style)
            pygui.end_menu()
        
        vp = pygui.get_main_viewport()
        if pygui.begin_menu("pygui.get_main_viewport()"):
            show_imguiviewport(vp)
            pygui.end_menu()
        
        dl = pygui.get_window_draw_list()
        if pygui.begin_menu("pygui.get_window_draw_list()"):
            show_imdrawlist(dl)
            pygui.end_menu()
        
        if pygui.button("Add data to ImGuiIO.user_data?"):
            io.user_data = ("My custom", "data", 54)

        pygui.tree_pop()

    if pygui.tree_node("Custom drawing"):
        dl = pygui.get_window_draw_list()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_bezier_cubic(
            (cx, cy),
            (cx + 20, cy + 70),
            (cx + 50, cy - 10),
            (cx + 40, cy + 50),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0, 1, 0.8)),
            2,
            15
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_bezier_quadratic(
            (cx, cy),
            (cx + 10, cy + 80),
            (cx + 45, cy + 10),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.05, 1, 0.8)),
            2,
            15
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_circle(
            (cx + 25, cy + 25),
            25,
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.1, 1, 0.8)),
            15,
            2,
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_circle_filled(
            (cx + 25, cy + 25),
            25,
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.15, 1, 0.8)),
            15,
        )
        pygui.dummy((50, 50))

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_convex_poly_filled(
            [
                (cx + 25 + 9  * math.cos(math.radians(18)),  cy + 25 + 9  * math.sin(math.radians(18))),
                (cx + 25 + 25 * math.cos(math.radians(54)),  cy + 25 + 25 * math.sin(math.radians(54))),
                (cx + 25 + 9  * math.cos(math.radians(90)),  cy + 25 + 9  * math.sin(math.radians(90))),
                (cx + 25 + 25 * math.cos(math.radians(126)), cy + 25 + 25 * math.sin(math.radians(126))),
                (cx + 25 + 9  * math.cos(math.radians(162)), cy + 25 + 9  * math.sin(math.radians(162))),
                (cx + 25 + 25 * math.cos(math.radians(198)), cy + 25 + 25 * math.sin(math.radians(198))),
                (cx + 25 + 9  * math.cos(math.radians(234)), cy + 25 + 9  * math.sin(math.radians(234))),
                (cx + 25 + 25 * math.cos(math.radians(270)), cy + 25 + 25 * math.sin(math.radians(270))),
                (cx + 25 + 9  * math.cos(math.radians(306)), cy + 25 + 9  * math.sin(math.radians(306))),
                (cx + 25 + 25 * math.cos(math.radians(342)), cy + 25 + 25 * math.sin(math.radians(342))),
            ],
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.20, 1, 0.8)),
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        image =  widget.instance().widgets_image
        texture_id =  widget.instance().widgets_image_texture
        show_tl = (126, 30)
        show_br = (176, 80)
        uv_tl = (show_tl[0] / image.width, show_tl[1] / image.height)
        uv_br =   (show_br[0] / image.width, show_br[1] / image.height)
        dl.add_image(
            texture_id,
            (cx, cy),
            (cx + 50, cy + 50),
            uv_tl,
            uv_br
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        show_tl = (910, 277)
        show_tr = (950, 277)
        show_br = (960, 327)
        show_bl = (920, 327)
        uv_tl = (show_tl[0] / image.width, show_tl[1] / image.height)
        uv_tr = (show_tr[0] / image.width, show_tr[1] / image.height)
        uv_br = (show_br[0] / image.width, show_br[1] / image.height)
        uv_bl = (show_bl[0] / image.width, show_bl[1] / image.height)
        dl.add_image_quad(
            texture_id,
            (cx, cy),
            (cx + 40, cy),
            (cx + 50, cy + 50),
            (cx + 10, cy + 50),
            uv_tl,
            uv_tr,
            uv_br,
            uv_bl,
        )
        pygui.dummy((50, 50))
        pygui.same_line()
        
        cx, cy = pygui.get_cursor_screen_pos()
        show_tl = (155, 382)
        show_br = (205, 432)
        uv_tl = (show_tl[0] / image.width, show_tl[1] / image.height)
        uv_br = (show_br[0] / image.width, show_br[1] / image.height)
        dl.add_image_rounded(
            texture_id,
            (cx, cy),
            (cx + 50, cy + 50),
            uv_tl,
            uv_br,
            pygui.color_convert_float4_to_u32((1, 1, 1, 1)),
            10
        )
        pygui.dummy((50, 50))

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_line(
            (cx, cy),
            (cx + 50, cy + 50),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.25, 1, 0.8)),
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_ngon(
            (cx + 25, cy + 25),
            25,
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.3, 1, 0.8)),
            6,
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_ngon_filled(
            (cx + 25, cy + 25),
            25,
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.35, 1, 0.8)),
            8
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_polyline(
            [
                (cx, cy),
                (cx + 50, cy),
                (cx + 50, cy + 50),
                (cx, cy + 50),
                (cx, cy + 10),
                (cx + 40, cy + 10),
                (cx + 40, cy + 40),
                (cx + 10, cy + 40),
                (cx + 10, cy + 20),
                (cx + 30, cy + 20),
                (cx + 30, cy + 30),
                (cx + 20, cy + 30),
            ],
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.4, 1, 0.8)),
            pygui.IM_DRAW_FLAGS_NONE,
            2
        )
        pygui.dummy((50, 50))

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_quad(
            (cx + 15, cy),
            (cx + 35, cy),
            (cx + 50, cy + 50),
            (cx, cy + 50),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.45, 1, 0.8)),
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_quad_filled(
            (cx, cy),
            (cx + 50, cy),
            (cx + 35, cy + 50),
            (cx + 15, cy + 50),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.50, 1, 0.8)),
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_rect(
            (cx, cy),
            (cx + 50, cy + 50),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.55, 1, 0.8)),
            0,
            pygui.IM_DRAW_FLAGS_NONE,
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_rect_filled(
            (cx, cy),
            (cx + 50, cy + 50),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.60, 1, 0.8)),
            0,
            pygui.IM_DRAW_FLAGS_NONE,
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        rand.frame_delta_count += pygui.get_io().delta_time / 10
        dl.add_rect_filled_multi_color(
            (cx, cy),
            (cx + 50, cy + 50),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb((rand.frame_delta_count + 0.65) % 1, 1, 0.8)),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb((rand.frame_delta_count + 0.75) % 1, 1, 0.8)),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb((rand.frame_delta_count + 0.85) % 1, 1, 0.8)),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb((rand.frame_delta_count + 0.95) % 1, 1, 0.8)),
        )
        pygui.dummy((50, 50))

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_text(
            (cx, cy),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.70, 0.4, 0.8)),
            "Hello\nWorld"
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        # TODO: Include custom Font example.
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_triangle(
            (cx, cy),
            (cx + 50, cy + 25),
            (cx, cy + 50),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.80, 1, 0.8)),
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.add_triangle_filled(
            (cx, cy),
            (cx + 50, cy + 25),
            (cx, cy + 50),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.85, 1, 0.8))
        )
        pygui.dummy((50, 50))

        cx, cy = pygui.get_cursor_screen_pos()
        dl.path_arc_to(
            (cx + 25, cy + 25),
            25,
            math.radians(270),
            math.radians(((270 + rand.frame_delta_count * 400) % 360) + 270),
        )
        dl.path_stroke(
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.90, 1, 0.8)),
            0,
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.path_arc_to_fast(
            (cx + 25, cy + 25),
            25,
            9,
            (9 + int(rand.frame_delta_count * 20)) % 12 + 9,
        )
        dl.path_stroke(
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.95, 1, 0.8)),
            0,
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        # Creates a "point" that the bezier curve can start from
        dl.path_line_to((cx, cy))
        dl.path_bezier_cubic_curve_to(
            (cx + 20, cy + 70),
            (cx + 50, cy - 10),
            (cx + 40, cy + 50),
        )
        dl.path_stroke(
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(1, 1, 0.8)),
            0,
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.path_line_to((cx, cy))
        dl.path_bezier_quadratic_curve_to(
            (cx + 10, cy + 80),
            (cx + 45, cy + 10),
        )
        dl.path_stroke(
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.05, 1, 0.8)),
            0,
            2
        )
        pygui.dummy((50, 50))

        cx, cy = pygui.get_cursor_screen_pos()
        # Creates a "point" that the bezier curve can start from
        dl.path_line_to((cx, cy + 25))
        dl.path_line_to((cx, cy))
        dl.path_clear()
        dl.path_line_to((cx + 25, cy))
        dl.path_line_to((cx + 50, cy))
        dl.path_line_to((cx + 50, cy + 50))
        dl.path_line_to((cx, cy + 50))
        dl.path_line_to((cx, cy + 25))
        dl.path_line_to((cx + 25, cy + 25))
        dl.path_line_to((cx + 25, cy))
        dl.path_stroke(
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.10, 1, 0.8)),
            0,
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.path_line_to_merge_duplicate((cx, cy))
        dl.path_line_to_merge_duplicate((cx, cy))
        dl.path_line_to_merge_duplicate((cx, cy))
        dl.path_line_to_merge_duplicate((cx, cy))
        dl.path_line_to_merge_duplicate((cx + 50, cy))
        dl.path_line_to_merge_duplicate((cx + 50, cy + 50))
        dl.path_line_to_merge_duplicate((cx + 25, cy + 50))
        dl.path_line_to_merge_duplicate((cx + 25, cy + 25))
        dl.path_line_to_merge_duplicate((cx, cy + 25))
        dl.path_line_to_merge_duplicate((cx, cy))
        dl.path_stroke(
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.15, 1, 0.8)),
            0,
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.path_line_to((cx, cy))
        dl.path_line_to((cx + 50, cy))
        dl.path_line_to((cx + 50, cy + 25))
        dl.path_line_to((cx + 25, cy + 25))
        dl.path_line_to((cx + 25, cy + 50))
        dl.path_line_to((cx, cy + 50))
        dl.path_line_to((cx, cy))
        dl.path_stroke(
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.2, 1, 0.8)),
            0,
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        dl.path_line_to((cx, cy))
        dl.path_line_to((cx + 25, cy))
        dl.path_line_to((cx + 50, cy + 25))
        dl.path_line_to((cx + 50, cy + 50))
        dl.path_line_to((cx + 25, cy + 50))
        dl.path_line_to((cx, cy + 25))
        dl.path_fill_convex(
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.25, 1, 0.8)),
        )
        pygui.dummy((50, 50))

        cx, cy = pygui.get_cursor_screen_pos()
        dl.path_rect((cx + 25, cy), (cx + 50, cy + 50))
        dl.path_line_to((cx, cy + 25))
        dl.path_line_to((cx + 25, cy))
        dl.path_stroke(
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.30, 1, 0.8)),
            0,
            2
        )
        pygui.dummy((50, 50))
        pygui.same_line()

        cx, cy = pygui.get_cursor_screen_pos()
        rand.frame_delta_count
        fonts = pygui.get_io().fonts.fonts
        font_index = math.floor(rand.frame_delta_count * 10) % len(fonts)
        selected_font = fonts[font_index]
        dl.add_text_imfont(
            selected_font,
            13,
            (cx, cy),
            pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(0.35, 1, 0.8)),
            f"Hello\nworld\nfont: {font_index}"
        )
        pygui.dummy((50, 50))

        pygui.tree_pop()
    
    if pygui.tree_node("String() testing"):
        pygui.input_text("String test", rand.string_test)
        pygui.text("Length: {} Value: '{}'".format(
            rand.string_test.buffer_size, rand.string_test.value
        ))
        if pygui.button("Set text to constant"):
            rand.string_test.value = "Hello"
        pygui.tree_pop()

    if pygui.tree_node("pygui.accept_drag_drop_payload()"):
        pygui.text("These buttons are drag_drop sources")
        pygui.button("Hello world")
        data = ("First button", "Hello World", 1, 2, 3)
        if pygui.begin_drag_drop_source():
            pygui.set_drag_drop_payload("Custom", data)
            pygui.text(str(data))
            pygui.end_drag_drop_source()
        
        pygui.button("Foo bar")
        data = ("Second button", "Foo bar", 2)
        if pygui.begin_drag_drop_source():
            pygui.set_drag_drop_payload("Custom", data)
            pygui.text(str(data))
            pygui.end_drag_drop_source()
        
        pygui.text("Drop Here: {}".format(rand.payload_message))
        if pygui.begin_drag_drop_target():
            payload = pygui.accept_drag_drop_payload("Custom")
            if payload is not None:
                rand.payload_message = payload.data
            pygui.end_drag_drop_target()
        
        current_payload = pygui.get_drag_drop_payload()
        pygui.text("Current payload: {}".format(current_payload))
        pygui.text("Current payload.data: {}".format(current_payload.data if current_payload is not None else "..."))
        pygui.text("payload.data_frame_count: {}".format(current_payload.data_frame_count if current_payload is not None else "..."))
        pygui.text("payload.data_size:        {}".format(current_payload.data_size        if current_payload is not None else "..."))
        pygui.text("payload.data_type:        {}".format(current_payload.data_type        if current_payload is not None else "..."))
        pygui.text("payload.delivery:         {}".format(current_payload.delivery         if current_payload is not None else "..."))
        pygui.text("payload.preview:          {}".format(current_payload.preview          if current_payload is not None else "..."))
        pygui.text("payload.source_id:        {}".format(current_payload.source_id        if current_payload is not None else "..."))
        pygui.text("payload.source_parent_id: {}".format(current_payload.source_parent_id if current_payload is not None else "..."))
        pygui.tree_pop()

    if pygui.tree_node("pygui.begin_child_frame()"):
        new_id = pygui.get_id("begin_child_frame()")
        item_height = pygui.get_text_line_height_with_spacing()
        if pygui.begin_child_frame(new_id, (-pygui.FLT_MIN, item_height * 5 + 5)):
            for n in range(5):
                pygui.text("My Item {}".format(n))
            pygui.end_child_frame()
        pygui.tree_pop()

    if pygui.tree_node("pygui.begin_child_id()"):
        new_id = pygui.get_id("begin_child_id()")
        pygui.begin_child_id(new_id, (0, 260), True)
        if pygui.begin_table("split", 2, pygui.TABLE_FLAGS_RESIZABLE | pygui.TABLE_FLAGS_NO_SAVED_SETTINGS):
            for i in range(30):
                pygui.table_next_column()
                pygui.button("{:3f}".format(i), (-pygui.FLT_MIN, 0))
            pygui.end_table()
        pygui.end_child()
        pygui.tree_pop()

    if pygui.tree_node("pygui.begin_disabled()"):
        pygui.checkbox("Begin Disabled", rand.begin_disabled)
        pygui.begin_disabled(rand.begin_disabled.value)
        pygui.checkbox("First checkbox", rand.first_checkbox)
        pygui.checkbox("Second checkbox", rand.second_checkbox)
        pygui.end_disabled()
        pygui.checkbox("Ignore disabled checkbox", rand.third_checkbox)
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.begin_main_menu_bar()"):
        if pygui.begin_main_menu_bar():
            if pygui.begin_menu("File"):
                pygui.menu_item("Hello world")
                pygui.end_menu()
            
            if pygui.begin_menu("Test"):
                pygui.menu_item("Content1")
                pygui.menu_item("Content2")
                pygui.menu_item("Content3")
                pygui.end_menu()
            
            if pygui.begin_menu("About"):
                pygui.menu_item("About me etc...")
                pygui.end_menu()
            pygui.end_main_menu_bar()
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.begin_popup_context_void()"):
        pygui.text_wrapped(
            "Popup only appears when you right click on the main window."
            " This will make the usual ImGui menu appear."
        )
        if pygui.begin_popup_context_void(None, pygui.POPUP_FLAGS_MOUSE_BUTTON_RIGHT):
            show_menu_file()
            pygui.end_popup()
        pygui.tree_pop()

    if pygui.tree_node("pygui.begin_popup_modal()"):
        pygui.text_wrapped("Modal windows are like popups but the user cannot close them by clicking outside.")
        if pygui.button("Open Modal"):
            pygui.open_popup("Modal?")

        # Always center this window when appearing
        center = pygui.get_main_viewport().get_center()
        pygui.set_next_window_pos(center, pygui.COND_APPEARING, (0.5, 0.5))

        if pygui.begin_popup_modal("Modal?", None, pygui.WINDOW_FLAGS_ALWAYS_AUTO_RESIZE):
            pygui.text("This opens a modal popup")
            pygui.separator()
            mouse_pos_on_popup = pygui.get_mouse_pos_on_opening_current_popup()
            pygui.text("pygui.get_mouse_pos_on_opening_current_popup(): {}".format(
                mouse_pos_on_popup
            ))

            pygui.push_style_var(pygui.STYLE_VAR_FRAME_PADDING, (0, 0))
            pygui.checkbox("This is a checkbox", rand.modal_checkbox)
            pygui.pop_style_var()

            if pygui.button("OK", (120, 0)):
                pygui.close_current_popup()
            pygui.set_item_default_focus()
            pygui.same_line()
            if pygui.button("Cancel", (120, 0)):
                pygui.close_current_popup()
            pygui.end_popup()
        pygui.text("pygui.is_popup_open(): {}".format(pygui.is_popup_open("Modal?")))
        pygui.tree_pop()

    if pygui.tree_node("pygui.combo_callback()"):
        def combo_callback_function(data, index: int, out: pygui.String) -> bool:
            out.value = data[index]
            return True
        data = ["Apples", "Oranges", "Mango", "Passionfruit", "Strawberry"]
        
        pygui.text("pygui.combo_callback")
        pygui.combo_callback(
            "My Combo", rand.current_item,
            combo_callback_function, data, len(data))
        pygui.new_line()
        pygui.new_line()
        pygui.text("pygui.list_box_callback")
        pygui.list_box_callback(
            "My List Box", rand.current_item_list,
            combo_callback_function, data, len(data))
        pygui.tree_pop()

    if pygui.tree_node("pygui.color_convert_float4_to_u32()"):
        draw_list = pygui.get_window_draw_list()

        pygui.color_edit4("Edit rgb", rand.colour)
        pygui.color_edit4("Edit hsv", rand.colour, pygui.COLOR_EDIT_FLAGS_DISPLAY_HSV)
        float_to_u32 = pygui.color_convert_float4_to_u32(rand.colour.tuple())
        float_to_u32_macro = pygui.IM_COL32(*[c * 255 for c in rand.colour.tuple()])
        pygui.text("color_convert_float4_to_u32: {}".format(float_to_u32))
        pygui.text("IM_COL32:                    {}".format(float_to_u32_macro))

        gradient_size = (pygui.calc_item_width(), pygui.get_frame_height())

        pygui.separator()
        pygui.text("color_convert_u32_to_float4()")
        u32_to_float4 = pygui.color_convert_u32_to_float4(float_to_u32)
        pygui.text(str(u32_to_float4))
        p0 = pygui.get_cursor_screen_pos()
        p1 = (p0[0] + gradient_size[0], p0[1] + gradient_size[1])
        draw_list.add_rect_filled(p0, p1, pygui.color_convert_float4_to_u32(u32_to_float4))
        pygui.invisible_button("##gradient1", gradient_size)

        pygui.separator()
        pygui.text("color_convert_rgb_to_hsv()")
        rgb_to_hsv = pygui.color_convert_rgb_to_hsv(*u32_to_float4)
        pygui.text(str(rgb_to_hsv))
        p0 = pygui.get_cursor_screen_pos()
        p1 = (p0[0] + gradient_size[0], p0[1] + gradient_size[1])
        draw_list.add_rect_filled(p0, p1, pygui.color_convert_float4_to_u32(pygui.color_convert_hsv_to_rgb(*rgb_to_hsv)))
        pygui.invisible_button("##gradient2", gradient_size)
        
        pygui.tree_pop()

    if pygui.tree_node("pygui.debug_check_version_and_data_layout()"):
        pygui.text_wrapped(
            "If pressing this alerts ImGui then the sizes of the structs in"
            " cython is different to ImGui. This *might* not be an issue.")
        try:
            if pygui.button("Call pygui.debug_check_version_and_data_layout()"):
                pygui.debug_check_version_and_data_layout()
                rand.error_text = [(0, 1, 0, 1), "Passed"]
        except pygui.ImGuiError as e:
            rand.error_text = [(1, 0, 0, 1), str(e)]
        
        if rand.error_text[1] != "":
            pygui.push_style_color(pygui.COL_TEXT, rand.error_text[0])
            pygui.text_wrapped(rand.error_text[1])
            pygui.pop_style_color()

        if rand.error_text[1] != "":
            if pygui.button("Clear"):
                rand.error_text[1] = ""

        pygui.tree_pop()
    
    if pygui.tree_node("pygui.debug_text_encoding()"):
        pygui.debug_text_encoding("Demo String")
        pygui.text("Emojis")
        pygui.debug_text_encoding("😀😁😂")
        pygui.text("utf-8 characters")
        pygui.debug_text_encoding("こんにちは")
        pygui.input_text("Custom", rand.utf8_string)
        pygui.debug_text_encoding(rand.utf8_string.value)
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.dock_space()"):
        pygui.text_wrapped(
            "This will spawn a window that can be docked inside this dockspace."
            " This is because the dockspace is created *before* creating the"
            " window."
        )
        dockspace_id = pygui.get_id("My Dockspace")
        pygui.dock_space(dockspace_id, (500, 500))
        pygui.begin("Dock me in the dockspace")
        pygui.show_user_guide()
        pygui.end()
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.dock_space_over_viewport()"):
        dockspace_id = pygui.get_id("My ViewportDockspace")
        viewport = pygui.get_main_viewport()
        pygui.dock_space_over_viewport(viewport, pygui.DOCK_NODE_FLAGS_NO_RESIZE)
        pygui.begin("Dock me in the viewport")
        pygui.show_user_guide()
        pygui.end()
        pygui.tree_pop()

    if pygui.tree_node("pygui.drag_int_range2()"):
        pygui.drag_int_range2("My drag_int2", rand.drag_min, rand.drag_max, 1, -500, 500)
        pygui.drag_int("drag_int", rand.drag, 1, rand.drag_min.value, rand.drag_max.value)
        pygui.drag_float_range2("My drag_float2", rand.drag_float_min, rand.drag_float_max, 0.001, -1, 1)
        pygui.drag_float("drag_float", rand.drag_float, 0.001, rand.drag_float_min.value, rand.drag_float_max.value)
        pygui.tree_pop()

    if pygui.tree_node("pygui.get_clipboard_text()"):
        clipboard_text = pygui.get_clipboard_text()
        pygui.text("Current clipboard below")
        pygui.separator()
        pygui.text_wrapped(clipboard_text)
        pygui.separator()
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.ImDrawListSplitter"):
        pygui.text_wrapped(
            "The left column is channel 0. The right is channel 1. You can see"
            " from this example that the right will always draw on top even"
            " though every second draw call is the right.")
        draw_list = pygui.get_window_draw_list()
        splitter = pygui.ImDrawListSplitter.create()
        splitter.split(draw_list, 2)

        pygui.separator()
        cs = pygui.get_cursor_screen_pos()
        splitter.set_current_channel(draw_list, 0)
        size = 60
        gap = 40
        for i in range(5):
            splitter.set_current_channel(draw_list, 0)
            draw_list.add_rect_filled(
                (cs[0],        cs[1] + i * gap),
                (cs[0] + size, cs[1] + i * gap + size),
                pygui.get_color_u32_im_vec4(pygui.color_convert_hsv_to_rgb(0.1 * i, 1, 0.8))
            )
            splitter.set_current_channel(draw_list, 1)
            draw_list.add_rect(
                (cs[0] + size/2,        cs[1] + i * gap + size/3),
                (cs[0] + size/2 + size, cs[1] + i * gap + size + size/3),
                pygui.get_color_u32_im_vec4(pygui.color_convert_hsv_to_rgb((0.5 + 0.1 * i), 1, 0.8)),
                20, 0, 8
            )
        splitter.merge(draw_list)
        splitter.destroy()
        pygui.dummy((10, size * 4))
        pygui.separator()
        pygui.tree_pop()

    if pygui.tree_node("pygui.ImGuiInputTextCallbackData"):
        help_marker(
            "Press Up/Down/Tab/k to test the callbacks."
            "\nDown will use the existing buffer size. See the demo."
            "\nChar 'k' is ignored by CALLBACK_CHAR_FILTER"
            "\nUp/Down does not work with multiline input")
        # ImGuiInputTextFlags_CallbackCompletion # Callback on pressing tab (for completion handling)
        # ImGuiInputTextFlags_CallbackHistory    # Callback on pressing up/down arrows (for history handling)
        # ImGuiInputTextFlags_CallbackAlways     # Callback on each iteration. user code may query cursor position, modify text buffer.
        # ImGuiInputTextFlags_CallbackCharFilter # Callback on character inputs to replace or discard them. modify 'eventchar' to replace or discard, or return 1 in callback to discard.
        # ImGuiInputTextFlags_CallbackResize     # Callback on buffer capacity changes request (beyond 'buf_size' parameter value), allowing the string to grow. notify when the string wants to be resized (for string types which hold a cache of their size). you will be provided a new bufsize in the callback and need to honor it. (see misc/cpp/imgui_stdlib.h for an example of using this)
        # ImGuiInputTextFlags_CallbackEdit       # Callback on any edit (note that inputtext() already returns true on edit, the callback is useful mainly to manipulate the underlying buffer while focus is active)
        pygui.checkbox_flags("pygui.INPUT_TEXT_FLAGS_CALLBACK_ALWAYS", rand.input_flags, pygui.INPUT_TEXT_FLAGS_CALLBACK_ALWAYS)

        rand.input_buffer_log
        def master_callback(callback_data: pygui.ImGuiInputTextCallbackData, user_data) -> int:
            callbacks = {
                pygui.INPUT_TEXT_FLAGS_CALLBACK_COMPLETION: input_text_completion_callback,
                pygui.INPUT_TEXT_FLAGS_CALLBACK_HISTORY: input_text_history_callback,
                pygui.INPUT_TEXT_FLAGS_CALLBACK_CHAR_FILTER: input_text_char_filter_callback,
                pygui.INPUT_TEXT_FLAGS_CALLBACK_RESIZE: input_text_char_resize_callback,
                pygui.INPUT_TEXT_FLAGS_CALLBACK_EDIT: input_text_char_edit_callback,
                pygui.INPUT_TEXT_FLAGS_CALLBACK_ALWAYS: input_text_always_callback,
            }
            ret = callbacks[callback_data.event_flag](callback_data, user_data)
            return 0 if ret is None else ret

        def input_text_completion_callback(cb: pygui.ImGuiInputTextCallbackData, log):
            log.append("pygui.INPUT_TEXT_FLAGS_CALLBACK_COMPLETION")
            log.append("\tcb.ctx: {}".format(cb.ctx))
            log.append("\tcb.cursor_pos: {}".format(cb.cursor_pos))
            log.append("\tcb.buf_size: {}".format(cb.buf_size))
            log.append("\tcb.buf_text_len: {}".format(cb.buf_text_len))
            log.append("\tcb.selection_start: {}".format(cb.selection_start))
            log.append("\tcb.selection_end: {}".format(cb.selection_end))
            log.append("\tcb.flags: {}".format(cb.flags))
            log.append("\tlen(cb.user_data): {}".format(len(cb.user_data)))
            log.append("\tlen(log): {}".format(len(log)))
            log.append("\tcb.has_selection(): {}".format(cb.has_selection()))
            cb.delete_chars(0, cb.buf_text_len)
            cb.insert_chars(0, "Auto-completed")

        def input_text_history_callback(cb: pygui.ImGuiInputTextCallbackData, log):
            log.append("pygui.INPUT_TEXT_FLAGS_CALLBACK_HISTORY")
            # Must use the data to manipulate the string as some funky internal
            # operation must be taking place. You can't just straight up modify
            # the pygui.String() like in most circumstances.
            if cb.event_key == pygui.KEY_UP_ARROW:
                cb.delete_chars(0, cb.buf_text_len)
                cb.insert_chars(0, "Up arrow")
            elif cb.event_key == pygui.KEY_DOWN_ARROW:
                # This will use the existing buffer.
                cb.buf = "Down arrow"[:cb.buf_text_len]
                cb.buf_dirty = True
        
        def input_text_char_filter_callback(cb: pygui.ImGuiInputTextCallbackData, log):
            log.append("pygui.INPUT_TEXT_FLAGS_CALLBACK_CHAR_FILTER")
            if cb.event_char == ord("k"):
                return 1
            
            if cb.event_char == ord("-"):
                cb.clear_selection()
            
            if cb.event_char == ord("="):
                cb.select_all()
            
            return 0
        
        def input_text_char_resize_callback(cb: pygui.ImGuiInputTextCallbackData, log):
            log.append("pygui.INPUT_TEXT_FLAGS_CALLBACK_RESIZE: {}".format(cb.buf_text_len))
            # TODO: Have not been able to get resizing to work.
            # rand.input_buffer.buffer_size = cb.buf_text_len + 1
            # cb.buf = rand.input_buffer.value
        
        def input_text_char_edit_callback(cb: pygui.ImGuiInputTextCallbackData, log):
            log.append("pygui.INPUT_TEXT_FLAGS_CALLBACK_EDIT")
    
        def input_text_always_callback(cb: pygui.ImGuiInputTextCallbackData, log):
            log.append("pygui.INPUT_TEXT_FLAGS_CALLBACK_ALWAYS")

        input_types = ["input_text", "input_text_multiline", "input_text_with_hint"]
        pygui.list_box("Input box type", rand.input_type, input_types, 3)
        selected_type = input_types[rand.input_type.value]
        if selected_type == "input_text":
            pygui.input_text(
                "My text",
                rand.input_buffer,
                rand.input_flags.value,
                master_callback,
                rand.input_buffer_log)
        elif selected_type == "input_text_multiline":
            pygui.input_text_multiline(
                "My text",
                rand.input_buffer,
                (400, 200),
                rand.input_flags.value & ~pygui.INPUT_TEXT_FLAGS_CALLBACK_HISTORY,
                master_callback,
                rand.input_buffer_log)
        else:
             pygui.input_text_with_hint(
                "My text",
                "Hint!",
                rand.input_buffer,
                rand.input_flags.value,
                master_callback,
                rand.input_buffer_log)

        pygui.text_wrapped("Input: {}".format(rand.input_buffer.value))
        pygui.text_wrapped("Buffer Size: {}".format(rand.input_buffer.buffer_size))

        pygui.text("Events: {}".format(len(rand.input_buffer_log)))
        if pygui.begin_child("Callback log", (400, pygui.get_text_line_height_with_spacing() * 10), True):
            for i, event in enumerate(rand.input_buffer_log):
                pygui.text("{}: {}".format(i, event))
            pygui.set_scroll_here_y(1)
        pygui.end_child()
        if pygui.button("Clear log"):
            rand.input_buffer_log = []

        pygui.tree_pop()

    if pygui.tree_node("pygui.ImGuiListClipper"):
        pygui.text("Normal Clipper")
        flags = pygui.TABLE_FLAGS_BORDERS_OUTER | \
                pygui.TABLE_FLAGS_BORDERS_INNER | \
                pygui.TABLE_FLAGS_SCROLL_Y
        if pygui.begin_table("NormalClipper", 4, flags, (0, pygui.get_text_line_height_with_spacing() * 10), 0):
            pygui.table_setup_column("ID")
            pygui.table_setup_column("Name")
            pygui.table_setup_column("DisplayStart")
            pygui.table_setup_column("DisplayEnd")
            pygui.table_setup_scroll_freeze(0, 1) # Make row always visible
            pygui.table_headers_row()

            clipper = pygui.ImGuiListClipper.create()
            clipper.begin(len(rand.df))

            # pygui.text("clipper.ctx: {}".format(clipper.ctx))

            while clipper.step():
                exit_early = False
                for i in range(clipper.display_start, clipper.display_end):
                    # Display a data item
                    _id, entry_name = rand.df[i]
                    pygui.push_id(_id)
                    # pygui.table_next_row()
                    pygui.table_next_column()
                    pygui.text(str(_id))
                    pygui.table_next_column()
                    pygui.text(entry_name)
                    pygui.table_next_column()
                    pygui.text(str(clipper.display_start))
                    pygui.table_next_column()
                    pygui.text(str(clipper.display_end))
                    pygui.pop_id()
                
                    if _id == 25:
                        exit_early = True
                        break
                
                if exit_early:
                    # Lets us leave early but note that the call to clipper.begin
                    # is still defining the size of the table, so it looks weird
                    # to exit early unless you anticipate it.
                    clipper.end()
                    break
            clipper.destroy()
            pygui.end_table()

        pygui.text("Forced Display Range Clipper")
        scroll_to = pygui.slider_int("Jump to", rand.jump_to, 0, len(rand.df) - 1, "%d", pygui.SLIDER_FLAGS_ALWAYS_CLAMP)
        steps_showing = []
        if pygui.begin_table("RangedClipper", 4, flags, (0, pygui.get_text_line_height_with_spacing() * 10), 0):
            pygui.table_setup_column("ID")
            pygui.table_setup_column("Name")
            pygui.table_setup_column("DisplayStart")
            pygui.table_setup_column("DisplayEnd")
            pygui.table_setup_scroll_freeze(0, 1) # Make row always visible
            pygui.table_headers_row()

            clipper = pygui.ImGuiListClipper.create()
            clipper.begin(len(rand.df))

            if scroll_to:
                clipper.include_range_by_indices(
                    rand.jump_to.value, rand.jump_to.value + 1)

            while clipper.step():
                steps_showing.append((clipper.display_start, clipper.display_end))
                for i in range(clipper.display_start, clipper.display_end):
                    # Display a data item
                    _id, entry_name = rand.df[i]
                    pygui.push_id(_id)
                    # pygui.table_next_row()
                    pygui.table_next_column()
                    pygui.text(str(_id))
                    pygui.table_next_column()
                    pygui.text(entry_name)
                    pygui.table_next_column()
                    pygui.text(str(clipper.display_start))
                    pygui.table_next_column()
                    pygui.text(str(clipper.display_end))
                    pygui.pop_id()

                    if scroll_to and i == rand.jump_to.value:
                        pygui.set_scroll_here_y(0.5)
                
            
            clipper.destroy()
            pygui.end_table()
        if scroll_to:
            rand.jump_to_cache = steps_showing
        pygui.text("1. Update on the frame you move the slider")
        pygui.text("2. Update every frame")
        if pygui.begin_child("Steps Showing", (140, pygui.get_text_line_height_with_spacing() * 4), True):
            for step in rand.jump_to_cache:
                pygui.text("Showing {} -> {}".format(*step))
        pygui.end_child()
        pygui.same_line()
        if pygui.begin_child("Steps Showing Live", (140, pygui.get_text_line_height_with_spacing() * 4), True):
            for step in steps_showing:
                pygui.text("Showing {} -> {}".format(*step))
        pygui.end_child()
        pygui.tree_pop()

    if pygui.tree_node("pygui.ImGuiTextFilter"):
        items = [
            "Hello World",
            "pygui says 'Hello'",
            "What can be filtered...",
            "Using an ImGuiTextFilter?",
            "What about this statement",
            "Mango Apple Passionfruit",
        ]
        rand.text_filter.draw()
        pygui.text("filter.is_active(): {}".format(rand.text_filter.is_active()))
        if pygui.begin_child("Filtered items", (200, pygui.get_text_line_height_with_spacing() * 7), True):
            for item in items:
                if not rand.text_filter.pass_filter(item):
                    continue

                pygui.text(item)
        pygui.end_child()   
        pygui.tree_pop()

    if pygui.tree_node("pygui.ImGuiPlaformIO"):
        platform_io = pygui.get_platform_io()
        pygui.list_box("##Select viewport", rand.viewport_selection, [f"Viewport({hash(v)})" for v in platform_io.viewports])
        viewport = platform_io.viewports[rand.viewport_selection.value % len(platform_io.viewports)]

        margin = 5
        pygui.get_foreground_draw_list(viewport).add_rect(
            (viewport.pos[0] + margin, viewport.pos[1] + margin),
            (viewport.pos[0] + viewport.size[0] - margin, viewport.pos[1] + viewport.size[1] - margin),
            pygui.color_convert_float4_to_u32((0, 1, 0, 1)),
            0, 0, 2
        )

        if pygui.checkbox("Show Monitors", rand.show_monitors):
            rand.monitors_visible = [pygui.Bool(True) for _ in range(len(platform_io.monitors))]

        if rand.show_monitors:
            for i, monitor in enumerate(platform_io.monitors):
                if not rand.monitors_visible[i]:
                    continue

                pygui.push_id(i)
                pygui.set_next_window_pos(
                    (monitor.main_pos[0] + 1, monitor.main_pos[1] + 1)
                )
                pygui.set_next_window_size(
                    (monitor.main_pos[0] + monitor.main_size[0] - 1, monitor.main_pos[1] + monitor.main_size[1] - 1)
                )
                pygui.push_style_var(pygui.STYLE_VAR_WINDOW_ROUNDING, 0)
                if pygui.begin(f"Monitor: {i}", rand.monitors_visible[i], pygui.WINDOW_FLAGS_NO_DECORATION | pygui.WINDOW_FLAGS_NO_RESIZE):
                    pygui.text(f"Monitor: {i}")
                    pygui.get_window_draw_list().add_rect(
                        (monitor.work_pos[0], monitor.work_pos[1]),
                        (monitor.work_pos[0] + monitor.work_size[0], monitor.work_pos[1] + monitor.work_size[1]),
                        pygui.color_convert_float4_to_u32((1, 1, 0, 1)),
                        0, 0, 2
                    )
                    pygui.text("monitor.dpi_scale: {}".format(monitor.dpi_scale))
                    pygui.text("monitor.main_pos: {}".format(monitor.main_pos))
                    pygui.text("monitor.main_size: {}".format(monitor.main_size))
                    pygui.text("monitor.work_pos: {}".format(monitor.work_pos))
                    pygui.text("monitor.work_size: {}".format(monitor.work_size))
                    if pygui.button("Close"):
                        rand.monitors_visible[i].value = False
                pygui.end()
                pygui.pop_style_var()
                pygui.pop_id()
        pygui.tree_pop()

    if pygui.tree_node("pygui.input_text_multiline()"):
        def callback_function(callback_data, user_data):
            print("Hello", user_data)
        
        pygui.input_text_multiline(
            "My text", rand.multiline_buffer, (-pygui.FLT_MIN, 100),
            pygui.INPUT_TEXT_FLAGS_CALLBACK_EDIT, callback_function, "My data")
        if pygui.button("Copy to clipboard"):
            pygui.set_clipboard_text(rand.multiline_buffer.value)
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.is_item_activated()"):
        pygui.button("is_item_activated")
        if pygui.is_item_activated() or rand.is_activated:
            rand.is_activated = True
            pygui.same_line()
            pygui.text("Is Activated!")
            pygui.same_line()
            if pygui.button("Reset"):
                rand.is_activated = False
        pygui.button("is_item_deactivated")
        if pygui.is_item_deactivated() or rand.is_deactivated:
            rand.is_deactivated = True
            pygui.same_line()
            pygui.text("Is Deactivated!")
            pygui.same_line()
            if pygui.button("Reset"):
                rand.is_deactivated = False
        pygui.set_next_item_width(200)
        pygui.drag_float("is_item_deactivated_after_edit", rand.edit_float, 0.01)
        if pygui.is_item_deactivated_after_edit() or rand.is_deactivated_after_edit:
            rand.is_deactivated_after_edit = True
            pygui.same_line()
            pygui.text("Is Deactivated after edit!")
            pygui.same_line()
            if pygui.button("Reset"):
                rand.is_deactivated_after_edit = False
        
        pygui.set_next_item_width(200)
        pygui.drag_float("is_item_edited", rand.edit_float, 0.01)
        if pygui.is_item_edited() or rand.is_edited:
            rand.is_edited = True
            pygui.same_line()
            pygui.text("Is Edited!")
            pygui.same_line()
            if pygui.button("Reset"):
                rand.is_edited = False
        
        focused = -1
        for i, bool_ptr in enumerate(rand.checkboxes):
            if i > 0:
                pygui.same_line()
            pygui.push_style_color(pygui.COL_CHECK_MARK, pygui.color_convert_hsv_to_rgb(i / 10, 0.6, 0.6))
            pygui.checkbox(f"##{i}", bool_ptr)
            pygui.pop_style_color()
            if pygui.is_item_focused():
                focused = i
        pygui.text("is_item_focused: {}".format(focused if focused != -1 else "None"))
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.is_item_visible()"):
        visible = None
        rect_visible_from_cursor = None
        rect_visible = None
        if pygui.begin_child("My child", (500, pygui.get_text_line_height_with_spacing() * 6), True):
            pygui.text("Some")
            pygui.text("Lines")
            pygui.text("Inside")
            pygui.text("The")
            pygui.text("Child")
            pygui.text("So")
            pygui.text("That")
            pygui.text("The")
            pygui.text("Scroll")
            pygui.text("Appears")
            pygui.text_colored((0, 1, 0, 1), "Am I visible?")
            visible = pygui.is_item_visible()
            pygui.text("More")
            pygui.text("Text")
            rect_visible_from_cursor = pygui.is_rect_visible_by_size((10, 10))
            cursor_screen_pos = pygui.get_cursor_screen_pos()
            draw_list = pygui.get_window_draw_list()
            draw_list.add_rect_filled(
                cursor_screen_pos,
                (cursor_screen_pos[0] + 10, cursor_screen_pos[1] + 10),
                pygui.color_convert_float4_to_u32((0, 1, 0, 1))
            )
            pygui.dummy((10, pygui.get_text_line_height()))
            pygui.text("Rect above for is_rect_visible_by_size")
            pygui.text("Rect of this be seen?")
            rect_min = pygui.get_item_rect_min()
            rect_max = pygui.get_item_rect_max()
            draw_list.add_rect(rect_min, rect_max, pygui.color_convert_float4_to_u32((0, 1, 0, 1)))
            rect_visible = pygui.is_rect_visible(pygui.get_item_rect_min(), pygui.get_item_rect_max())
        pygui.end_child()
        pygui.text("is_item_visible: {}".format(visible))
        pygui.text("is_rect_visible_by_size: {}".format(rect_visible_from_cursor))
        pygui.text("is_rect_visible: {}".format(rect_visible))
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.is_key_pressed(pygui.KEY_A)"):
        pygui.text("Log for pygui.KEY_A and pygui.KEY_B (for repeat rate)")
        if pygui.is_key_pressed(pygui.KEY_A):
            rand.key_press_log.append("pygui.is_key_pressed(pygui.KEY_A)")
        if pygui.is_key_down(pygui.KEY_A):
            rand.key_press_log.append("pygui.is_key_down(pygui.KEY_A)")
        if pygui.is_key_released(pygui.KEY_A):
            rand.key_press_log.append("pygui.is_key_released(pygui.KEY_A)")
        key_press_amount = pygui.get_key_pressed_amount(pygui.KEY_B, 1, 0.2)
        if key_press_amount > 0:
            rand.key_press_log.append("pygui.get_key_pressed_amount(): {} @ {}".format(
                key_press_amount,
                pygui.get_frame_count()
            ))

        if pygui.begin_child("##Log for keys", (400, pygui.get_text_line_height_with_spacing() * 10), True):
            for event in rand.key_press_log:
                pygui.text(event)
        pygui.end_child()
        if pygui.button("Clear ##log"):
            rand.key_press_log.clear()
        pygui.tree_pop()

    if pygui.tree_node("pygui.is_mouse_hovering_rect()"):
        pygui.button("My button")
        rect_min = pygui.get_item_rect_min()
        rect_max = pygui.get_item_rect_max()
        pygui.text("Item id above: {}".format(pygui.get_item_id()))
        pygui.text("pygui.is_mouse_hovering_rect(): {}".format(pygui.is_mouse_hovering_rect(rect_min, rect_max)))
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.is_mouse_pos_valid()"):
        pygui.text("pygui.get_mouse_pos(): {}".format(pygui.get_mouse_pos()))
        pygui.text("pygui.is_mouse_pos_valid(): {}".format(pygui.is_mouse_pos_valid()))
        pygui.text("pygui.is_mouse_pos_valid((-100, 100)): {}".format(pygui.is_mouse_pos_valid((-100, 100))))
        pygui.text("pygui.is_mouse_pos_valid((-MAX, -MAX)): {}".format(pygui.is_mouse_pos_valid((-pygui.FLT_MAX, -pygui.FLT_MAX))))
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.is_mouse_released()"):
        if pygui.is_mouse_released(pygui.MOUSE_BUTTON_LEFT):
            rand.mouse_press_log.append("pygui.is_mouse_released(pygui.MOUSE_BUTTON_LEFT)")
        pygui.text("Log for pygui.MOUSE_BUTTON_LEFT")
        if pygui.begin_child("Log for pygui.MOUSE_BUTTON_LEFT", (400, pygui.get_text_line_height_with_spacing() * 5), True):
            for event in rand.mouse_press_log:
                pygui.text(event)
        pygui.end_child()
        if pygui.button("Clear"):
            rand.mouse_press_log.clear()
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.is_window_appearing()"):
        pygui.checkbox("Show window", rand.show_window)
        
        is_collapsed = "Unknown"
        if rand.show_window:
            pygui.begin("Window utilities")
            pygui.text("Hello world")
            pygui.text("pygui.is_window_docked(): {}".format(pygui.is_window_docked()))
            pygui.text("pygui.is_window_hovered(): {}".format(pygui.is_window_hovered()))
            if pygui.is_window_appearing():
                rand.window_log.append("Appearing on frame {}".format(pygui.get_frame_count()))
            # If __ minimised
            is_collapsed = pygui.is_window_collapsed()
            pygui.end()
        
        if pygui.begin_child("#window log", (400, pygui.get_text_line_height_with_spacing() * 5), True):
            for event in rand.window_log:
                pygui.text(event)
        pygui.end_child()
        pygui.text("pygui.is_window_collapsed(): {}".format(is_collapsed))
        if pygui.button("Clear ##log"):
            rand.window_log.clear()
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.log_buttons()"):
        pygui.log_buttons()
        pygui.tree_pop()

    if pygui.tree_node("pygui.open_popup_id()"):
        if pygui.button("Open popup"):
            pygui.open_popup("Popup 1")
        
        if pygui.begin_popup("Popup 1"):
            pygui.text("Hello from popup 1")
            pygui.end_popup()
        
        pygui.text("The next should not open")
        if pygui.button("Open popup from nested begin"):
            pygui.open_popup("Popup 2")
        
        pygui.push_id("Nested Id")
        if pygui.begin_popup("Popup 2"):
            pygui.text("Hello from popup 2")
            pygui.end_popup()
        pygui.pop_id()

        
        if pygui.button("Open with open_popup_id"):
            popup_id = pygui.get_id("Popup 3")
            pygui.open_popup_id(popup_id)
        
        if pygui.begin_popup("Popup 3"):
            pygui.text("Hello from popup 3")
            pygui.end_popup()

        pygui.tree_pop()

    if pygui.tree_node("pygui.plot_histogram_callback()"):
        # Just performs some calculation inside the callback to show
        # it's doing something.
        values = [x for x in reversed(range(40))]
        def values_getter_callback(data, index: int) -> float:
            inc = (2 * math.pi) / (len(data) // 2)
            return 10 * math.sin(data[index] * inc)
        
        pygui.plot_histogram_callback(
            "My callback histogram", values_getter_callback,
            values, len(values), 0, None, -10, 10, (300, 100))

        # You can even use lambdas to define functions.
        pygui.plot_lines_callback(
            "My callback lines",
            lambda data, idx: 10 * math.cos(data[idx] / 5),
            values, len(values), 0, None, -10, 10, (300, 100))
        pygui.tree_pop()

    if pygui.tree_node("pygui.push_tab_stop()"):
        pygui.text("You can tab here")
        pygui.push_id("First")
        for i, buf in enumerate(rand.text_input):
            pygui.input_text("##{}".format(i), buf)
        pygui.pop_id()

        pygui.separator()

        pygui.text("You can't tab here")
        pygui.push_id("Second")
        pygui.push_tab_stop(False)
        for i, buf in enumerate(rand.text_input):
            pygui.input_text("##{}".format(i), buf)
        pygui.pop_tab_stop()
        pygui.pop_id()

        pygui.separator()

        pygui.text("You can tab here again")
        pygui.push_id("Third")
        for i, buf in enumerate(rand.text_input):
            pygui.input_text("##{}".format(i), buf)
        pygui.pop_id()
        pygui.tree_pop()

    if pygui.tree_node("pygui.set_cursor_pos()"):
        pygui.text("Hello World")
        cursor_pos = pygui.get_cursor_pos()
        pygui.set_cursor_pos((cursor_pos[0] + 50, cursor_pos[1] + 50))
        pygui.text("After setting xy cursor")
        pygui.text("After cursor")
        pygui.set_cursor_pos_x(cursor_pos[0] + 50)
        pygui.text("After setting x cursor")
        pygui.text("After cursor")
        cursor_pos = pygui.get_cursor_pos()
        pygui.set_cursor_pos_y(cursor_pos[1] + 50)
        pygui.text("After setting y cursor")
        pygui.text("After cursor")
        screen_cursor_pos = pygui.get_cursor_screen_pos()
        pygui.set_cursor_screen_pos((screen_cursor_pos[0] + 50, screen_cursor_pos[1] + 50))
        pygui.text("After setting xy screen cursor")
        pygui.text("After cursor")
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.set_mouse_cursor()"):
        cursor_names = [
            "pygui.MOUSE_CURSOR_ARROW",
            "pygui.MOUSE_CURSOR_TEXT_INPUT",
            "pygui.MOUSE_CURSOR_RESIZE_ALL",
            "pygui.MOUSE_CURSOR_RESIZE_NS",
            "pygui.MOUSE_CURSOR_RESIZE_EW",
            "pygui.MOUSE_CURSOR_RESIZE_NESW",
            "pygui.MOUSE_CURSOR_RESIZE_NWSE",
            "pygui.MOUSE_CURSOR_HAND",
            "pygui.MOUSE_CURSOR_NOT_ALLOWED",
        ]
        for i in range(len(cursor_names)):
            cursor_name = cursor_names[i]
            pygui.button(cursor_name)
            if pygui.is_item_hovered():
                pygui.set_mouse_cursor(i)

        pygui.tree_pop()

    if pygui.tree_node("pygui.set_next_window_bg_alpha()"):
        pygui.text("Check pass through central node in dockspace.")
        pygui.drag_float("Next window bg alpha", rand.next_window_alpha, 0.02, 0, 1)
        pygui.drag_float2("Next window content size", rand.next_window_content_size.as_floatptrs(), 2, 1, 1000)
        pygui.checkbox("Lock Size?", rand.next_window_do_size)
        pygui.drag_float2("Next window size", rand.next_window_size.as_floatptrs(), 2, 10, 1000)
        pygui.checkbox("Add Size Constraint?", rand.next_window_do_size_constraint)
        if rand.next_window_do_size_constraint:
            pygui.checkbox("Add callback? (Locks x resize)", rand.next_window_do_size_constraint_do_callback)
                
            pygui.drag_float2(
                "Next window TL constraint",
                rand.next_window_size_constraint_min.as_floatptrs(),
                2, 10, 1000)
            pygui.drag_float2(
                "Next window BR constraint",
                rand.next_window_size_constraint_max.as_floatptrs(),
                2, 10, 1000)
            # It's techincally possible to make the max smaller than the min,
            # but this makes window horribly flicker. I'm going to clamp the max
            # to be always bigger than the min.
            rand.next_window_size_constraint_max.x = max(
                rand.next_window_size_constraint_max.x,
                rand.next_window_size_constraint_min.x,
            )
            rand.next_window_size_constraint_max.y = max(
                rand.next_window_size_constraint_max.y,
                rand.next_window_size_constraint_min.y,
            )

            
        pygui.drag_float2("Next window scroll", rand.next_window_scroll.as_floatptrs(), 2, -1, 1000)
        pygui.checkbox("Next window collapsed", rand.next_window_collapsed)
        pygui.checkbox("Next window focused", rand.next_window_focus)
        pygui.checkbox("Next window in Main Viewport?", rand.next_window_in_main_viewport)
        pygui.checkbox("Spawn window", rand.next_window_spawned)
        
        def constraint_callback(data: pygui.ImGuiSizeCallbackData):
            rand.callback_log = []
            rand.callback_log.append("From callback:")
            rand.callback_log.append("data.user_data: {}".format(data.user_data))
            rand.callback_log.append("data.pos: {}".format(data.pos))
            rand.callback_log.append("data.current_size: {}".format(data.current_size))
            rand.callback_log.append("data.desired_size: {}".format(data.desired_size))
            # Look the x axis when resizing in the callback
            data.desired_size = (data.current_size[0], data.desired_size[1])

        if rand.next_window_spawned:
            if rand.next_window_do_size_constraint:
                if rand.next_window_do_size_constraint_do_callback:
                    pygui.set_next_window_size_constraints(
                    rand.next_window_size_constraint_min.tuple(),
                    rand.next_window_size_constraint_max.tuple(),
                    constraint_callback,
                    ("My custom", "Data", 2, "is cool"))
                    for line in rand.callback_log:
                        pygui.text(line)
                else:
                    pygui.set_next_window_size_constraints(
                    rand.next_window_size_constraint_min.tuple(),
                    rand.next_window_size_constraint_max.tuple())
            if rand.next_window_in_main_viewport:
                main_viewport = pygui.get_main_viewport()
                pygui.set_next_window_viewport(main_viewport.id)

            pygui.set_next_window_bg_alpha(rand.next_window_alpha.value)
            pygui.set_next_window_collapsed(rand.next_window_collapsed.value)
            pygui.set_next_window_content_size(rand.next_window_content_size.tuple())
            if rand.next_window_do_size:
                pygui.set_next_window_size(rand.next_window_size.tuple())
            pygui.set_next_window_scroll(rand.next_window_scroll.tuple())
            if rand.next_window_focus and rand.next_window_spawned:
                pygui.set_next_window_focus()
        
            if pygui.begin("The Next Window", rand.next_window_spawned, pygui.WINDOW_FLAGS_HORIZONTAL_SCROLLBAR):
                for i in range(100):
                    pygui.text("Adding text that is really long: Line {}".format(i))
            pygui.end()
        pygui.tree_pop()
    
    if pygui.tree_node("pygui.set_next_window_dock_id()"):
        pygui.checkbox("Next window auto-docked?", rand.next_window_docked)
        pygui.checkbox("Dock window spawned?", rand.next_window_dock_window_spawned)
        dock_id = pygui.get_id("My dockspace")
        pygui.dock_space(dock_id, (400, 200))
            
        if rand.next_window_dock_window_spawned:
            if rand.next_window_docked:
                pygui.set_next_window_dock_id(dock_id)
            
            if pygui.begin("Auto docked window", rand.next_window_dock_window_spawned, pygui.WINDOW_FLAGS_NO_BACKGROUND):
                pygui.text("Hello world")
            pygui.end()
        pygui.tree_pop()

    if pygui.tree_node("pygui.table_header()"):
        names = ["Apple", "Banana", "Mango", "Passionfruit"]
        if pygui.begin_table("Fruit Orders", 3, pygui.TABLE_FLAGS_BORDERS | pygui.TABLE_FLAGS_HIDEABLE):
            pygui.table_header("Bruh")
            pygui.table_setup_column("Name", pygui.TABLE_COLUMN_FLAGS_WIDTH_FIXED)
            pygui.table_setup_column("Amount")
            pygui.table_setup_column("Hidden")
            pygui.table_headers_row()
            pygui.table_set_column_enabled(2, False)
            for name in names:
                pygui.table_next_column()
                pygui.table_set_bg_color(pygui.TABLE_BG_TARGET_CELL_BG, pygui.get_color_u32_im_vec4((0, 0.3, 0, 1)))
                pygui.text(name)
                pygui.table_next_column()
                pygui.table_set_bg_color(pygui.TABLE_BG_TARGET_CELL_BG, pygui.get_color_u32_im_vec4((0, 0, 0.3, 1)))
                pygui.text(str((len(name) + 35) % 8))
                pygui.table_next_column()
                pygui.text("Hidden value")
            pygui.end_table()

        pygui.tree_pop()

    if pygui.tree_node("pygui.tree_push()"):
        if pygui.button("Click"):
            print("First")
        pygui.tree_push("First")
        if pygui.button("Click"):
            print("Second")
        pygui.tree_pop()

        pygui.tree_push("Second")
        if pygui.button("Click"):
            print("Third")
        pygui.tree_pop()

        pygui.tree_push("First")
        pygui.text("This one doesn't print anything")
        if pygui.button("Click"):
            print("Fourth")
        pygui.tree_pop()

        pygui.tree_pop()

    io = pygui.get_io()
    pygui.text("hash(pygui.get_io()): {}".format(hash(io)))
    pygui.text("pygui.get_io(): {}".format(io))

    pygui.pop_style_var()


class crash:
    error_text = pygui.String()
    catch_message = ""


def show_crash_test():
    if not pygui.collapsing_header("Crash ImGui"):
        return
    
    pygui.text("Test various crashes")
    pygui.same_line()
    help_marker(
        "1. This will call a function in ImGui that is known to crash. This crash"
        " originates from ImGui itself. If USE_CUSTOM_PYTHON_ERROR is defined then"
        " this will exception will be caught.\n"
        "2. This will call IM_ASSERT. If USE_CUSTOM_PYTHON_ERROR is defined then"
        " this function call will raise a pygui.ImGuiError, otherwise it will"
        " raise an AssertionError. In either cause, this should not crash because"
        " pygui.ImGuiError is AssertionError when USE_CUSTOM_PYTHON_ERROR is"
        " undefined.\n"
        "3. This uses python's assert keyword. If USE_CUSTOM_PYTHON_ERROR is"
        " defined this should crash your program because pygui.ImGuiError and"
        " AssertionError are different.\n"
        "4. This will call IM_ASSERT but will except by force using the ImGui's"
        " exposed dll exception. If USE_CUSTOM_PYTHON_ERROR is not defined, this"
        " will be caught, otherwise this will crash simply because you can't catch"
        " and exception with 'None'.\n"
    )

    if pygui.button("Clear"):
        crash.catch_message = ""
        crash.error_text.value = ""

    
    if pygui.button("Crash 1: pop_style_color() -> except pygui.Error"):
        try:
            pygui.pop_style_color(1)
        except pygui.ImGuiError as e:
            crash.catch_message = "Caught! You have custom exceptions on."
            crash.error_text.value = str(e)
    
    if pygui.button("Crash 2: pygui.IM_ASSERT(False) -> except pygui.Error"):
        try:
            pygui.IM_ASSERT(False, "I am an error message")
        except pygui.ImGuiError as e:
            crash.catch_message = "Caught! This should never crash."
            crash.error_text.value = str(e)
    
    if pygui.button("Crash 3: assert False -> except pygui.Error"):
        try:
            assert False, "I am another error message"
        except pygui.ImGuiError as e:
            crash.catch_message = "Caught! You have custom exceptions off."
            crash.error_text.value = str(e)
    
    if pygui.button("Crash 4: pygui.IM_ASSERT(False) -> except pygui.core.Error"):
        try:
            assert pygui.IM_ASSERT(False, "We are an error message")
        except pygui.get_imgui_error() as e:
            # Prefer to use pygui.ImGuiError as it is safer. This value could
            # be None if cimgui is not using a custom python exception. For this
            # example this is exactly what we want.
            crash.catch_message = "Caught! You have custom exceptions on."
            crash.error_text.value = str(e)
    
    if len(crash.catch_message) > 0:
        pygui.text(crash.catch_message)
        pygui.text_wrapped(crash.error_text.value)
    

class menu:
    b = pygui.Bool(True)


def show_menu_bar():
    if pygui.begin_menu_bar():
        if pygui.begin_menu("File"):
            show_menu_file()
            pygui.end_menu()
        if pygui.begin_menu("Edit"):
            if pygui.menu_item("Undo", "CTRL+Z"): pass
            if pygui.menu_item("Redo", "CTRL+Y", False, False): pass
            pygui.separator()
            if pygui.menu_item("Cut", "CTRL+X"): pass
            if pygui.menu_item("Copy", "CTRL+C"): pass
            if pygui.menu_item("Paste", "CTRL+V"): pass
            pygui.end_menu()
        if pygui.begin_menu("Examples"):
            pygui.menu_item_bool_ptr("Console", None, demo.show_app_console)
            pygui.menu_item_bool_ptr("Custom rendering", None, demo.show_custom_rendering)
            pygui.menu_item_bool_ptr("Documents", None, demo.show_app_documents)
            pygui.menu_item_bool_ptr("Custom fonts", None, demo.show_font_demo)
            pygui.end_menu()
        if pygui.begin_menu("Tools"):
            pygui.menu_item_bool_ptr("Debug Log", None, demo.show_debug_log_window)
            pygui.menu_item_bool_ptr("Font Selector", None, demo.show_font_selector)
            pygui.menu_item_bool_ptr("Metrics/Debugger", None, demo.show_metrics_window)
            pygui.menu_item_bool_ptr("Stack Tool", None, demo.show_stack_tool_window)
            pygui.menu_item_bool_ptr("Style Editor", None, demo.show_style_editor)
            pygui.menu_item_bool_ptr("Style Selector", None, demo.show_style_selector)
            pygui.menu_item_bool_ptr("User guide", None, demo.show_user_guide)
            pygui.menu_item_bool_ptr("About Dear ImGui", None, demo.show_about_window)
            pygui.end_menu()
        pygui.end_menu_bar()


def show_menu_file():
    pygui.menu_item("(demo menu)", None, False, False)
    if pygui.menu_item("New"): pass
    if pygui.menu_item("Open", "Ctrl+O"): pass
    if pygui.begin_menu("Open Recent"):
        pygui.menu_item("fish_hat.c")
        pygui.menu_item("fish_hat.inl")
        pygui.menu_item("fish_hat.h")
        if pygui.begin_menu("More.."):
            pygui.menu_item("Hello")
            pygui.menu_item("Sailor")
            if pygui.begin_menu("Recurse.."):
                show_menu_file()
                pygui.end_menu()
            pygui.end_menu()
        pygui.end_menu()
    if pygui.menu_item("Save", "Ctrl+S"): pass
    if pygui.menu_item("Save As.."): pass

    if pygui.begin_menu("Colors"):
        sz = pygui.get_text_line_height()
        for i in range(pygui.COL_COUNT):
            name = pygui.get_style_color_name(i)
            p = pygui.get_cursor_screen_pos()
            pygui.get_window_draw_list().add_rect_filled(
                p, (p[0] + sz, p[1] + sz),
                pygui.get_color_u32(i)
            )
            pygui.dummy((sz, sz))
            pygui.same_line()
            pygui.menu_item(name)
        pygui.end_menu()
    
    # Here we demonstrate appending again to the "Options" menu (which we already created above)
    # Of course in this demo it is a little bit silly that this function calls BeginMenu("Options") twice.
    # In a real code-base using it would make senses to use this feature from very different code locations.
    if pygui.begin_menu("Options"):
        pygui.checkbox("SomeOption", menu.b)
        pygui.end_menu()

    if pygui.begin_menu("Disabled", False):
        assert False # Should not be reached
    
    if pygui.menu_item("Checked", None, True): pass
    pygui.separator()
    if pygui.menu_item("Quit", "Alt+F4"): pass


class render:
    sz = pygui.Float(36)
    thickness = pygui.Float(3)
    ngon_sides = pygui.Int(6)
    circle_segments_override = pygui.Bool(False)
    circle_segments_override_v = pygui.Int(12)
    curve_segments_override = pygui.Bool(False)
    curve_segments_override_v = pygui.Int(8)
    colf = pygui.Vec4(1, 1, 0.4, 1)
    points = []
    scrolling = [0, 0]
    opt_enable_grid = pygui.Bool(True)
    opt_enable_context_menu = pygui.Bool(True)
    adding_line = False
    draw_bg = pygui.Bool(True)
    draw_fg = pygui.Bool(True)


def show_app_custom_rendering(p_open: pygui.Bool):
    if not pygui.begin("Example: Pygui Custom rendering", p_open):
        pygui.end()
        return
    
    # Tip: If you do a lot of custom rendering, you probably want to use your own geometrical types and benefit of
    # overloaded operators, etc. Define IM_VEC2_CLASS_EXTRA in imconfig.h to create implicit conversions between your
    # types and ImVec2/ImVec4. Dear ImGui defines overloaded operators but they are internal to imgui.cpp and not
    # exposed outside (to avoid messing with your types) In this example we are not using the maths operators!
    if pygui.begin_tab_bar("##TabBar"):
        if pygui.begin_tab_item("Primitives"):
            pygui.push_item_width(-pygui.get_font_size() * 15)
            draw_list = pygui.get_window_draw_list()

            # Draw gradients
            # (note that those are currently exacerbating our sRGB/Linear issues)
            # Calling ImGui::GetColorU32() multiplies the given colors by the current Style Alpha, but you may pass the IM_COL32() directly as well..
            pygui.text("Gradients")
            gradient_size = (pygui.calc_item_width(), pygui.get_frame_height())
            p0 = pygui.get_cursor_screen_pos()
            p1 = (p0[0] + gradient_size[0], p0[1] + gradient_size[1])
            col_a = pygui.IM_COL32(0, 0, 0, 255)
            col_b = pygui.IM_COL32(255, 255, 255, 255)
            draw_list.add_rect_filled_multi_color(p0, p1, col_a, col_b, col_b, col_a)
            pygui.invisible_button("##gradient1", gradient_size)

            p0 = pygui.get_cursor_screen_pos()
            p1 = (p0[0] + gradient_size[0], p0[1] + gradient_size[1])
            col_a = pygui.get_color_u32_im_vec4((0, 1, 0, 1)) # Just to showcase the different colour functions
            col_b = pygui.get_color_u32_im_vec4((1, 0, 0, 1))
            draw_list.add_rect_filled_multi_color(p0, p1, col_a, col_b, col_b, col_a)
            pygui.invisible_button("##gradient2", gradient_size)

            # Draw a bunch of primitives
            pygui.text("All primitives")
            pygui.drag_float("Size", render.sz, 0.2, 2, 100, "%.0f")
            pygui.drag_float("Thickness", render.thickness, 0.05, 1, 8, "%.02f")
            pygui.slider_int("N-gon sides", render.ngon_sides, 3, 12)
            pygui.checkbox("##circlesegmentoverride", render.circle_segments_override)
            pygui.same_line(0, pygui.get_style().item_inner_spacing[0])
            render.circle_segments_override.value |= pygui.slider_int("Circle segments override", render.circle_segments_override_v, 3, 40)
            pygui.checkbox("##curvessegmentoverride", render.curve_segments_override)
            pygui.same_line(0, pygui.get_style().item_inner_spacing[0])
            render.curve_segments_override.value |= pygui.slider_int("Curves segments override", render.curve_segments_override_v, 3, 40)
            pygui.color_edit4("Color", render.colf)

            p = pygui.get_cursor_screen_pos()
            col = render.colf.to_u32()
            sz = render.sz.value
            spacing = 10.0
            corners_tl_br = pygui.IM_DRAW_FLAGS_ROUND_CORNERS_TOP_LEFT | pygui.IM_DRAW_FLAGS_ROUND_CORNERS_BOTTOM_RIGHT
            rounding = render.sz.value / 5.0
            circle_segments = render.circle_segments_override_v.value if render.circle_segments_override else 0
            curve_segments = render.curve_segments_override_v.value if render.curve_segments_override else 0
            x = p[0] + 4.0
            y = p[1] + 4.0
            for n in range(2):
                # First line uses a thickness of 1.0f, second line uses the configurable thickness
                th = 1 if (n == 0) else render.thickness.value
                draw_list.add_ngon((x + sz*0.5, y + sz*0.5), sz*0.5, col, render.ngon_sides.value, th)
                x += sz + spacing  # N-gon
                draw_list.add_circle((x + sz*0.5, y + sz*0.5), sz*0.5, col, circle_segments, th)
                x += sz + spacing  # Circle
                draw_list.add_rect((x, y), (x + sz, y + sz), col, 0.0, pygui.IM_DRAW_FLAGS_NONE, th)
                x += sz + spacing  # Square
                draw_list.add_rect((x, y), (x + sz, y + sz), col, rounding, pygui.IM_DRAW_FLAGS_NONE, th)
                x += sz + spacing  # Square with all rounded corners
                draw_list.add_rect((x, y), (x + sz, y + sz), col, rounding, corners_tl_br, th)
                x += sz + spacing  # Square with two rounded corners
                draw_list.add_triangle((x+sz*0.5,y), (x+sz, y+sz-0.5), (x, y+sz-0.5), col, th)
                x += sz + spacing  # Triangle
                # draw_list->AddTriangle(ImVec2(x+sz*0.2f,y), ImVec2(x, y+sz-0.5f), ImVec2(x+sz*0.4f, y+sz-0.5f), col, th)
                # x+= sz*0.4f + spacing # Thin triangle
                draw_list.add_line((x, y), (x + sz, y), col, th)
                x += sz + spacing  # Horizontal line (note: drawing a filled rectangle will be faster!)
                draw_list.add_line((x, y), (x, y + sz), col, th)
                x += spacing       # Vertical line (note: drawing a filled rectangle will be faster!)
                draw_list.add_line((x, y), (x + sz, y + sz), col, th)
                x += sz + spacing  # Diagonal line

                # Quadratic Bezier Curve (3 control points)
                cp3 = [
                    (x, y + sz * 0.6),
                    (x + sz * 0.5, y - sz * 0.4),
                    (x + sz, y + sz),
                ]
                draw_list.add_bezier_quadratic(cp3[0], cp3[1], cp3[2], col, th, curve_segments)
                x += sz + spacing

                # # Cubic Bezier Curve (4 control points)
                cp4 = [
                    (x, y),
                    (x + sz * 1.3, y + sz * 0.3),
                    (x + sz - sz * 1.3, y + sz - sz * 0.3),
                    (x + sz, y + sz),
                ]
                draw_list.add_bezier_cubic(cp4[0], cp4[1], cp4[2], cp4[3], col, th, curve_segments)

                x = p[0] + 4
                y += sz + spacing
            
            draw_list.add_ngon_filled((x + sz * 0.5, y + sz * 0.5), sz*0.5, col, render.ngon_sides.value)
            x += sz + spacing  # N-gon
            draw_list.add_circle_filled((x + sz*0.5, y + sz*0.5), sz*0.5, col, circle_segments)
            x += sz + spacing  # Circle
            draw_list.add_rect_filled((x, y), (x + sz, y + sz), col)
            x += sz + spacing  # Square
            draw_list.add_rect_filled((x, y), (x + sz, y + sz), col, 10.0)
            x += sz + spacing  # Square with all rounded corners
            draw_list.add_rect_filled((x, y), (x + sz, y + sz), col, 10.0, corners_tl_br)
            x += sz + spacing  # Square with two rounded corners
            draw_list.add_triangle_filled((x+sz*0.5,y), (x+sz, y+sz-0.5), (x, y+sz-0.5), col)
            x += sz + spacing  # Triangle
            # draw_list.AddTriangleFilled(ImVec2(x+sz*0.2f,y), ImVec2(x, y+sz-0.5f), ImVec2(x+sz*0.4f, y+sz-0.5f), col); x += sz*0.4f + spacing; # Thin triangle
            draw_list.add_rect_filled((x, y), (x + sz, y + render.thickness.value), col)
            x += sz + spacing  # Horizontal line (faster than AddLine, but only handle integer thickness)
            draw_list.add_rect_filled((x, y), (x + render.thickness.value, y + sz), col)
            x += spacing * 2.0# Vertical line (faster than AddLine, but only handle integer thickness)
            draw_list.add_rect_filled((x, y), (x + 1, y + 1), col)
            x += sz            # Pixel (faster than AddLine)
            draw_list.add_rect_filled_multi_color((x, y), (x + sz, y + sz), pygui.IM_COL32(0, 0, 0, 255), pygui.IM_COL32(255, 0, 0, 255), pygui.IM_COL32(255, 255, 0, 255), pygui.IM_COL32(0, 255, 0, 255))

            pygui.dummy(((sz + spacing) * 10.2, (sz + spacing) * 3.0))
            pygui.pop_item_width()
            pygui.end_tab_item()
        
        if pygui.begin_tab_item("Canvas"):
            pygui.checkbox("Enable grid", render.opt_enable_grid)
            pygui.checkbox("Enable context menu", render.opt_enable_context_menu)
            pygui.text("Mouse Left: drag to add lines,\nMouse Right: drag to scroll, click for context menu.")

            # Typically you would use a BeginChild()/EndChild() pair to benefit from a clipping region + own scrolling.
            # Here we demonstrate that this can be replaced by simple offsetting + custom drawing + PushClipRect/PopClipRect() calls.
            # To use a child window instead we could use, e.g:
            #      ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding, ImVec2(0, 0));      // Disable padding
            #      ImGui::PushStyleColor(ImGuiCol_ChildBg, IM_COL32(50, 50, 50, 255));  // Set a background color
            #      ImGui::BeginChild("canvas", ImVec2(0.0f, 0.0f), true, ImGuiWindowFlags_NoMove);
            #      ImGui::PopStyleColor();
            #      ImGui::PopStyleVar();
            #      [...]
            #      ImGui::EndChild();

            # Using InvisibleButton() as a convenience 1) it will advance the layout cursor and 2) allows us to use IsItemHovered()/IsItemActive()
            canvas_p0 = pygui.get_cursor_screen_pos()      # ImDrawList API uses screen coordinates!
            canvas_sz = list(pygui.get_content_region_avail())   # Resize canvas to what's available
            if canvas_sz[0] < 50.0:
                canvas_sz[0] = 50.0
            if canvas_sz[1] < 50.0:
                canvas_sz[1] = 50.0
            canvas_sz = tuple(canvas_sz)
            canvas_p1 = (canvas_p0[0] + canvas_sz[0], canvas_p0[1] + canvas_sz[1])

            # Draw border and background color
            io = pygui.get_io()
            draw_list = pygui.get_window_draw_list()
            draw_list.add_rect_filled(canvas_p0, canvas_p1, pygui.IM_COL32(50, 50, 50, 255))
            draw_list.add_rect(canvas_p0, canvas_p1, pygui.IM_COL32(255, 255, 255, 255))

            # This will catch our interactions
            pygui.invisible_button("canvas", canvas_sz, pygui.BUTTON_FLAGS_MOUSE_BUTTON_LEFT | pygui.BUTTON_FLAGS_MOUSE_BUTTON_RIGHT)
            is_hovered = pygui.is_item_hovered()  # Hovered
            is_active = pygui.is_item_active()    # Held
            origin = (canvas_p0[0] + render.scrolling[0], canvas_p0[1] + render.scrolling[1]) # Lock scrolled origin
            mouse_pos_in_canvas = (io.mouse_pos[0] - origin[0], io.mouse_pos[1] - origin[1])

            # Add first and second point
            if is_hovered and not render.adding_line and pygui.is_mouse_clicked(pygui.MOUSE_BUTTON_LEFT):
                render.points.append(mouse_pos_in_canvas)
                render.points.append(mouse_pos_in_canvas)
                render.adding_line = True
            if render.adding_line:
                render.points[len(render.points) - 1] = mouse_pos_in_canvas
                if not pygui.is_mouse_down(pygui.MOUSE_BUTTON_LEFT):
                    render.adding_line = False
            
            # Pan (we use a zero mouse threshold when there's no context menu)
            # You may decide to make that threshold dynamic based on whether the mouse is hovering something etc.
            mouse_threshold_for_pan = -1 if render.opt_enable_context_menu else 0
            if is_active and pygui.is_mouse_dragging(pygui.MOUSE_BUTTON_RIGHT, mouse_threshold_for_pan):
                render.scrolling[0] += io.mouse_delta[0]
                render.scrolling[1] += io.mouse_delta[1]

            # Context menu (under default mouse threshold)
            drag_delta = pygui.get_mouse_drag_delta(pygui.MOUSE_BUTTON_RIGHT)
            if render.opt_enable_context_menu and drag_delta[0] == 0 and drag_delta[1] == 0:
                pygui.open_popup_on_item_click("context", pygui.POPUP_FLAGS_MOUSE_BUTTON_RIGHT)
            if pygui.begin_popup("context"):
                if render.adding_line:
                    render.points = render.points[:len(render.points) - 2]
                
                render.adding_line = False
                if pygui.menu_item("Remove one", None, False, len(render.points) > 0):
                    render.points.pop()
                    render.points.pop()
                if pygui.menu_item("Remove all", None, False, len(render.points) > 0):
                    render.points.clear()
                pygui.end_popup()

            # Draw grid + all lines in the canvas
            draw_list.push_clip_rect(canvas_p0, canvas_p1, True)
            if render.opt_enable_grid:
                GRID_STEP = 64

                x = render.scrolling[0] % GRID_STEP
                while x < canvas_sz[0]:
                    draw_list.add_line((canvas_p0[0] + x, canvas_p0[1]), (canvas_p0[0] + x, canvas_p1[1]), pygui.IM_COL32(200, 200, 200, 40))
                    x += GRID_STEP
                y = render.scrolling[1] % GRID_STEP
                while y < canvas_sz[1]:
                    draw_list.add_line((canvas_p0[0], canvas_p0[1] + y), (canvas_p1[0], canvas_p0[1] + y), pygui.IM_COL32(200, 200, 200, 40))
                    y += GRID_STEP
            for n in range(0, len(render.points), 2):
                first = render.points[n]
                second = render.points[n + 1]
                draw_list.add_line((origin[0] + first[0], origin[1] + first[1]), (origin[0] + second[0], origin[1] + second[1]), pygui.IM_COL32(255, 255, 0, 255), 2)
            draw_list.pop_clip_rect()

            pygui.end_tab_item()

        if pygui.begin_tab_item("BG/FG draw lists"):
            pygui.checkbox("Draw in Background draw list", render.draw_bg)
            pygui.same_line()
            help_marker("The Background draw list will be rendered below every Dear ImGui windows.")
            pygui.checkbox("Draw in Foreground draw list", render.draw_fg)
            pygui.same_line()
            help_marker("The Foreground draw list will be rendered over every Dear ImGui windows.")
            window_pos = pygui.get_window_pos()
            window_size = pygui.get_window_size()
            window_center = (window_pos[0] + window_size[0] * 0.5, window_pos[1] + window_size[1] * 0.5)
            if render.draw_bg:
                pygui.get_background_draw_list().add_circle(window_center, window_size[0] * 0.6, pygui.IM_COL32(255, 0, 0, 200), 0, 10 + 4)
            if render.draw_fg:
                pygui.get_foreground_draw_list().add_circle(window_center, window_size[1] * 0.6, pygui.IM_COL32(0, 255, 0, 200), 0, 10)
            pygui.end_tab_item()
        pygui.end_tab_bar()
    
    pygui.end()


class font:
    utf8_test = """
    Keyboard:
        abcdefghijklmnopqrstuvwxyz
        ABCDEFGHIJKLMNOPQRSTUVWXYZ
        `1234567890-=
        ~!@#$%^&*()_+
        []\;',./
        {{}}|:"<>?
        

    UTF-8 encoded sample plain-text file
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾

    Markus Kuhn [ˈmaʳkʊs kuːn] <mkuhn@acm.org> — 1999-08-20


    The ASCII compatible UTF-8 encoding of ISO 10646 and Unicode
    plain-text files is defined in RFC 2279 and in ISO 10646-1 Annex R.


    Using Unicode/UTF-8, you can write in emails and source code things such as

    Mathematics and Sciences:

        ∮ E⋅da = Q,  n → ∞, ∑ f(i) = ∏ g(i), ∀x∈ℝ: ⌈x⌉ = −⌊−x⌋, α ∧ ¬β = ¬(¬α ∨ β),

        ℕ ⊆ ℕ₀ ⊂ ℤ ⊂ ℚ ⊂ ℝ ⊂ ℂ, ⊥ < a ≠ b ≡ c ≤ d ≪ ⊤ ⇒ (A ⇔ B),

        2H₂ + O₂ ⇌ 2H₂O, R = 4.7 kΩ, ⌀ 200 mm

    Linguistics and dictionaries:

        ði ıntəˈnæʃənəl fəˈnɛtık əsoʊsiˈeıʃn
        Y [ˈʏpsilɔn], Yen [jɛn], Yoga [ˈjoːgɑ]

    APL:

        ((V⍳V)=⍳⍴V)/V←,V    ⌷←⍳→⍴∆∇⊃‾⍎⍕⌈

    Nicer typography in plain text files:

        ╔══════════════════════════════════════════╗
        ║                                          ║
        ║   • ‘single’ and “double” quotes         ║
        ║                                          ║
        ║   • Curly apostrophes: “We’ve been here” ║
        ║                                          ║
        ║   • Latin-1 apostrophe and accents: '´`  ║
        ║                                          ║
        ║   • ‚deutsche‘ „Anführungszeichen“       ║
        ║                                          ║
        ║   • †, ‡, ‰, •, 3–4, —, −5/+5, ™, …      ║
        ║                                          ║
        ║   • ASCII safety test: 1lI|, 0OD, 8B     ║
        ║                      ╭─────────╮         ║
        ║   • the euro symbol: │ 14.95 € │         ║
        ║                      ╰─────────╯         ║
        ╚══════════════════════════════════════════╝

    Greek (in Polytonic):

        The Greek anthem:

        Σὲ γνωρίζω ἀπὸ τὴν κόψη
        τοῦ σπαθιοῦ τὴν τρομερή,
        σὲ γνωρίζω ἀπὸ τὴν ὄψη
        ποὺ μὲ βία μετράει τὴ γῆ.

        ᾿Απ᾿ τὰ κόκκαλα βγαλμένη
        τῶν ῾Ελλήνων τὰ ἱερά
        καὶ σὰν πρῶτα ἀνδρειωμένη
        χαῖρε, ὦ χαῖρε, ᾿Ελευθεριά!

        From a speech of Demosthenes in the 4th century BC:

        Οὐχὶ ταὐτὰ παρίσταταί μοι γιγνώσκειν, ὦ ἄνδρες ᾿Αθηναῖοι,
        ὅταν τ᾿ εἰς τὰ πράγματα ἀποβλέψω καὶ ὅταν πρὸς τοὺς
        λόγους οὓς ἀκούω· τοὺς μὲν γὰρ λόγους περὶ τοῦ
        τιμωρήσασθαι Φίλιππον ὁρῶ γιγνομένους, τὰ δὲ πράγματ᾿ 
        εἰς τοῦτο προήκοντα,  ὥσθ᾿ ὅπως μὴ πεισόμεθ᾿ αὐτοὶ
        πρότερον κακῶς σκέψασθαι δέον. οὐδέν οὖν ἄλλο μοι δοκοῦσιν
        οἱ τὰ τοιαῦτα λέγοντες ἢ τὴν ὑπόθεσιν, περὶ ἧς βουλεύεσθαι,
        οὐχὶ τὴν οὖσαν παριστάντες ὑμῖν ἁμαρτάνειν. ἐγὼ δέ, ὅτι μέν
        ποτ᾿ ἐξῆν τῇ πόλει καὶ τὰ αὑτῆς ἔχειν ἀσφαλῶς καὶ Φίλιππον
        τιμωρήσασθαι, καὶ μάλ᾿ ἀκριβῶς οἶδα· ἐπ᾿ ἐμοῦ γάρ, οὐ πάλαι
        γέγονεν ταῦτ᾿ ἀμφότερα· νῦν μέντοι πέπεισμαι τοῦθ᾿ ἱκανὸν
        προλαβεῖν ἡμῖν εἶναι τὴν πρώτην, ὅπως τοὺς συμμάχους
        σώσομεν. ἐὰν γὰρ τοῦτο βεβαίως ὑπάρξῃ, τότε καὶ περὶ τοῦ
        τίνα τιμωρήσεταί τις καὶ ὃν τρόπον ἐξέσται σκοπεῖν· πρὶν δὲ
        τὴν ἀρχὴν ὀρθῶς ὑποθέσθαι, μάταιον ἡγοῦμαι περὶ τῆς
        τελευτῆς ὁντινοῦν ποιεῖσθαι λόγον.

        Δημοσθένους, Γ´ ᾿Ολυνθιακὸς

    Georgian:

        From a Unicode conference invitation:

        გთხოვთ ახლავე გაიაროთ რეგისტრაცია Unicode-ის მეათე საერთაშორისო
        კონფერენციაზე დასასწრებად, რომელიც გაიმართება 10-12 მარტს,
        ქ. მაინცში, გერმანიაში. კონფერენცია შეჰკრებს ერთად მსოფლიოს
        ექსპერტებს ისეთ დარგებში როგორიცაა ინტერნეტი და Unicode-ი,
        ინტერნაციონალიზაცია და ლოკალიზაცია, Unicode-ის გამოყენება
        ოპერაციულ სისტემებსა, და გამოყენებით პროგრამებში, შრიფტებში,
        ტექსტების დამუშავებასა და მრავალენოვან კომპიუტერულ სისტემებში.

    Russian:

        From a Unicode conference invitation:

        Зарегистрируйтесь сейчас на Десятую Международную Конференцию по
        Unicode, которая состоится 10-12 марта 1997 года в Майнце в Германии.
        Конференция соберет широкий круг экспертов по  вопросам глобального
        Интернета и Unicode, локализации и интернационализации, воплощению и
        применению Unicode в различных операционных системах и программных
        приложениях, шрифтах, верстке и многоязычных компьютерных системах.

    Thai (UCS Level 2):

        Excerpt from a poetry on The Romance of The Three Kingdoms (a Chinese
        classic 'San Gua'):

        [----------------------------|------------------------]
        ๏ แผ่นดินฮั่นเสื่อมโทรมแสนสังเวช  พระปกเกศกองบู๊กู้ขึ้นใหม่
        สิบสองกษัตริย์ก่อนหน้าแลถัดไป       สององค์ไซร้โง่เขลาเบาปัญญา
        ทรงนับถือขันทีเป็นที่พึ่ง           บ้านเมืองจึงวิปริตเป็นนักหนา
        โฮจิ๋นเรียกทัพทั่วหัวเมืองมา         หมายจะฆ่ามดชั่วตัวสำคัญ
        เหมือนขับไสไล่เสือจากเคหา      รับหมาป่าเข้ามาเลยอาสัญ
        ฝ่ายอ้องอุ้นยุแยกให้แตกกัน          ใช้สาวนั้นเป็นชนวนชื่นชวนใจ
        พลันลิฉุยกุยกีกลับก่อเหตุ          ช่างอาเพศจริงหนาฟ้าร้องไห้
        ต้องรบราฆ่าฟันจนบรรลัย           ฤๅหาใครค้ำชูกู้บรรลังก์ ฯ

        (The above is a two-column text. If combining characters are handled
        correctly, the lines of the second column should be aligned with the
        | character above.)

    Ethiopian:

        Proverbs in the Amharic language:

        ሰማይ አይታረስ ንጉሥ አይከሰስ።
        ብላ ካለኝ እንደአባቴ በቆመጠኝ።
        ጌጥ ያለቤቱ ቁምጥና ነው።
        ደሀ በሕልሙ ቅቤ ባይጠጣ ንጣት በገደለው።
        የአፍ ወለምታ በቅቤ አይታሽም።
        አይጥ በበላ ዳዋ ተመታ።
        ሲተረጉሙ ይደረግሙ።
        ቀስ በቀስ፥ ዕንቁላል በእግሩ ይሄዳል።
        ድር ቢያብር አንበሳ ያስር።
        ሰው እንደቤቱ እንጅ እንደ ጉረቤቱ አይተዳደርም።
        እግዜር የከፈተውን ጉሮሮ ሳይዘጋው አይድርም።
        የጎረቤት ሌባ፥ ቢያዩት ይስቅ ባያዩት ያጠልቅ።
        ሥራ ከመፍታት ልጄን ላፋታት።
        ዓባይ ማደሪያ የለው፥ ግንድ ይዞ ይዞራል።
        የእስላም አገሩ መካ የአሞራ አገሩ ዋርካ።
        ተንጋሎ ቢተፉ ተመልሶ ባፉ።
        ወዳጅህ ማር ቢሆን ጨርስህ አትላሰው።
        እግርህን በፍራሽህ ልክ ዘርጋ።

    Runes:

        ᚻᛖ ᚳᚹᚫᚦ ᚦᚫᛏ ᚻᛖ ᛒᚢᛞᛖ ᚩᚾ ᚦᚫᛗ ᛚᚪᚾᛞᛖ ᚾᚩᚱᚦᚹᛖᚪᚱᛞᚢᛗ ᚹᛁᚦ ᚦᚪ ᚹᛖᛥᚫ

        (Old English, which transcribed into Latin reads 'He cwaeth that he
        bude thaem lande northweardum with tha Westsae.' and means 'He said
        that he lived in the northern land near the Western Sea.')

    Braille:

        ⡌⠁⠧⠑ ⠼⠁⠒  ⡍⠜⠇⠑⠹⠰⠎ ⡣⠕⠌

        ⡍⠜⠇⠑⠹ ⠺⠁⠎ ⠙⠑⠁⠙⠒ ⠞⠕ ⠃⠑⠛⠔ ⠺⠊⠹⠲ ⡹⠻⠑ ⠊⠎ ⠝⠕ ⠙⠳⠃⠞
        ⠱⠁⠞⠑⠧⠻ ⠁⠃⠳⠞ ⠹⠁⠞⠲ ⡹⠑ ⠗⠑⠛⠊⠌⠻ ⠕⠋ ⠙⠊⠎ ⠃⠥⠗⠊⠁⠇ ⠺⠁⠎
        ⠎⠊⠛⠝⠫ ⠃⠹ ⠹⠑ ⠊⠇⠻⠛⠹⠍⠁⠝⠂ ⠹⠑ ⠊⠇⠻⠅⠂ ⠹⠑ ⠥⠝⠙⠻⠞⠁⠅⠻⠂
        ⠁⠝⠙ ⠹⠑ ⠡⠊⠑⠋ ⠍⠳⠗⠝⠻⠲ ⡎⠊⠗⠕⠕⠛⠑ ⠎⠊⠛⠝⠫ ⠊⠞⠲ ⡁⠝⠙
        ⡎⠊⠗⠕⠕⠛⠑⠰⠎ ⠝⠁⠍⠑ ⠺⠁⠎ ⠛⠕⠕⠙ ⠥⠏⠕⠝ ⠰⡡⠁⠝⠛⠑⠂ ⠋⠕⠗ ⠁⠝⠹⠹⠔⠛ ⠙⠑ 
        ⠡⠕⠎⠑ ⠞⠕ ⠏⠥⠞ ⠙⠊⠎ ⠙⠁⠝⠙ ⠞⠕⠲

        ⡕⠇⠙ ⡍⠜⠇⠑⠹ ⠺⠁⠎ ⠁⠎ ⠙⠑⠁⠙ ⠁⠎ ⠁ ⠙⠕⠕⠗⠤⠝⠁⠊⠇⠲

        ⡍⠔⠙⠖ ⡊ ⠙⠕⠝⠰⠞ ⠍⠑⠁⠝ ⠞⠕ ⠎⠁⠹ ⠹⠁⠞ ⡊ ⠅⠝⠪⠂ ⠕⠋ ⠍⠹
        ⠪⠝ ⠅⠝⠪⠇⠫⠛⠑⠂ ⠱⠁⠞ ⠹⠻⠑ ⠊⠎ ⠏⠜⠞⠊⠊⠥⠇⠜⠇⠹ ⠙⠑⠁⠙ ⠁⠃⠳⠞
        ⠁ ⠙⠕⠕⠗⠤⠝⠁⠊⠇⠲ ⡊ ⠍⠊⠣⠞ ⠙⠁⠧⠑ ⠃⠑⠲ ⠔⠊⠇⠔⠫⠂ ⠍⠹⠎⠑⠇⠋⠂ ⠞⠕
        ⠗⠑⠛⠜⠙ ⠁ ⠊⠕⠋⠋⠔⠤⠝⠁⠊⠇ ⠁⠎ ⠹⠑ ⠙⠑⠁⠙⠑⠌ ⠏⠊⠑⠊⠑ ⠕⠋ ⠊⠗⠕⠝⠍⠕⠝⠛⠻⠹ 
        ⠔ ⠹⠑ ⠞⠗⠁⠙⠑⠲ ⡃⠥⠞ ⠹⠑ ⠺⠊⠎⠙⠕⠍ ⠕⠋ ⠳⠗ ⠁⠝⠊⠑⠌⠕⠗⠎ 
        ⠊⠎ ⠔ ⠹⠑ ⠎⠊⠍⠊⠇⠑⠆ ⠁⠝⠙ ⠍⠹ ⠥⠝⠙⠁⠇⠇⠪⠫ ⠙⠁⠝⠙⠎
        ⠩⠁⠇⠇ ⠝⠕⠞ ⠙⠊⠌⠥⠗⠃ ⠊⠞⠂ ⠕⠗ ⠹⠑ ⡊⠳⠝⠞⠗⠹⠰⠎ ⠙⠕⠝⠑ ⠋⠕⠗⠲ ⡹⠳
        ⠺⠊⠇⠇ ⠹⠻⠑⠋⠕⠗⠑ ⠏⠻⠍⠊⠞ ⠍⠑ ⠞⠕ ⠗⠑⠏⠑⠁⠞⠂ ⠑⠍⠏⠙⠁⠞⠊⠊⠁⠇⠇⠹⠂ ⠹⠁⠞
        ⡍⠜⠇⠑⠹ ⠺⠁⠎ ⠁⠎ ⠙⠑⠁⠙ ⠁⠎ ⠁ ⠙⠕⠕⠗⠤⠝⠁⠊⠇⠲

        (The first couple of paragraphs of "A Christmas Carol" by Dickens)

    Compact font selection example text:

        ABCDEFGHIJKLMNOPQRSTUVWXYZ /0123456789
        abcdefghijklmnopqrstuvwxyz £©µÀÆÖÞßéöÿ
        –—‘“”„†•…‰™œŠŸž€ ΑΒΓΔΩαβγδω АБВГДабвгд
        ∀∂∈ℝ∧∪≡∞ ↑↗↨↻⇣ ┐┼╔╘░►☺♀ ﬁ�⑀₂ἠḂӥẄɐː⍎אԱა

    Greetings in various languages:

        Hello world, Καλημέρα κόσμε, コンニチハ

    Box drawing alignment tests:                                            █
                                                                            ▉
        ╔══╦══╗  ┌──┬──┐  ╭──┬──╮  ╭──┬──╮  ┏━━┳━━┓  ┎┒┏┑   ╷  ╻ ┏┯┓ ┌┰┐    ▊ ╱╲╱╲╳╳╳
        ║┌─╨─┐║  │╔═╧═╗│  │╒═╪═╕│  │╓─╁─╖│  ┃┌─╂─┐┃  ┗╃╄┙  ╶┼╴╺╋╸┠┼┨ ┝╋┥    ▋ ╲╱╲╱╳╳╳
        ║│╲ ╱│║  │║   ║│  ││ │ ││  │║ ┃ ║│  ┃│ ╿ │┃  ┍╅╆┓   ╵  ╹ ┗┷┛ └┸┘    ▌ ╱╲╱╲╳╳╳
        ╠╡ ╳ ╞╣  ├╢   ╟┤  ├┼─┼─┼┤  ├╫─╂─╫┤  ┣┿╾┼╼┿┫  ┕┛┖┚     ┌┄┄┐ ╎ ┏┅┅┓ ┋ ▍ ╲╱╲╱╳╳╳
        ║│╱ ╲│║  │║   ║│  ││ │ ││  │║ ┃ ║│  ┃│ ╽ │┃  ░░▒▒▓▓██ ┊  ┆ ╎ ╏  ┇ ┋ ▎
        ║└─╥─┘║  │╚═╤═╝│  │╘═╪═╛│  │╙─╀─╜│  ┃└─╂─┘┃  ░░▒▒▓▓██ ┊  ┆ ╎ ╏  ┇ ┋ ▏
        ╚══╩══╝  └──┴──┘  ╰──┴──╯  ╰──┴──╯  ┗━━┻━━┛           └╌╌┘ ╎ ┗╍╍┛ ┋  ▁▂▃▄▅▆▇█
    """
    use_index = pygui.Int(5)
    use_font = pygui.Bool(True)


def demo_fonts_init():
    """
    This function must be called before render if you want to test different
    fonts.
    """
    io = pygui.get_io()

    io.fonts.add_font_default()

    # utf-8 ranges from above
    builder = pygui.ImFontGlyphRangesBuilder.create()
    builder.add_text(font.utf8_test)
    ranges = builder.build_ranges()
    builder.destroy()

    # CascadiaMono font
    config = pygui.ImFontConfig.create()
    config.name = "CascadiaMono-SemiBold.otf without range"
    io.fonts.add_font_from_file_ttf("pygui/fonts/CascadiaMono-SemiBold.otf", 14, config)
    config.name = "CascadiaMono-SemiBold.otf with range"
    io.fonts.add_font_from_file_ttf("pygui/fonts/CascadiaMono-SemiBold.otf", 14, config, ranges)
    config.destroy()

    # NotoSansMath font
    config = pygui.ImFontConfig.create()
    config.name = "NotoSansMath-Regular.ttf without range"
    io.fonts.add_font_from_file_ttf("pygui/fonts/NotoSansMath-Regular.ttf", 20, config)
    config.name = "NotoSansMath-Regular.ttf with range"
    io.fonts.add_font_from_file_ttf("pygui/fonts/NotoSansMath-Regular.ttf", 20, config, ranges)
    config.destroy()

    # Selawk font
    config = pygui.ImFontConfig.create()
    config.name = "selawk.ttf without range"
    config.glyph_min_advance_x = 7.15
    config.glyph_max_advance_x = 7.15
    io.fonts.add_font_from_file_ttf("pygui/fonts/selawk.ttf", 15, config)
    config.name = "selawk.ttf with range"
    io.fonts.add_font_from_file_ttf("pygui/fonts/selawk.ttf", 15, config, ranges)
    config.destroy()

    # Merging multiple fonts together
    config = pygui.ImFontConfig.create()
    config.name = "CascadiaMono + Selawk + NotoSansMath"
    config.glyph_min_advance_x = 7.15
    config.glyph_max_advance_x = 7.15
    io.fonts.add_font_from_file_ttf("pygui/fonts/CascadiaMono-SemiBold.otf", 14, config, ranges)
    config.merge_mode = True
    io.fonts.add_font_from_file_ttf("pygui/fonts/NotoSansMath-Regular.ttf", 20, config, ranges)
    io.fonts.add_font_from_file_ttf("pygui/fonts/selawk.ttf", 15, config, ranges)
    config.destroy()

    # Showing the font glyph builder.
    builder = pygui.ImFontGlyphRangesBuilder.create()
    builder.add_text("Should not be visible")
    builder.clear()
    omega = ord("Ω")
    builder.add_text("asciiASCII")
    assert not builder.get_bit(omega)
    builder.set_bit(omega)
    assert builder.get_bit(omega)
    builder.add_char(ord("b"))
    custom_range = builder.build_ranges()
    builder.destroy()

    config = pygui.ImFontConfig.create()
    config.name = "Proggy + Droid Minimal"
    io.fonts.add_font_from_file_ttf("pygui/fonts/ProggyClean.ttf", 20, config, custom_range)
    config.merge_mode = True
    io.fonts.add_font_from_file_ttf("pygui/fonts/DroidSans.ttf", 11, config, ranges)
    config.destroy()

    # More fonts
    io.fonts.add_font_from_file_ttf("pygui/fonts/unifont-15.0.01.otf", 13, None, ranges)

    # Any fonts that need to be added should call build()
    io.fonts.build()

    # Since we need the ranges to be valid for the call to build, Python's gc
    # might clean up the ImGlyphRange before the call to build, resulting in
    # accessing freed memory. This is why we defer the destruction explicitly to
    # ensure the memory still availble for the build above. Aat that point. The
    # gc can safetly clean up the python ImFontConfig instance whenever it
    # needs.
    custom_range.destroy()
    ranges.destroy()


def show_fonts_demo():
    if pygui.begin("Custom fonts"):
        fonts = pygui.get_io().fonts.fonts
        selected_font = fonts[0]
        if pygui.begin("Style Editor"):
            pygui.checkbox("Push Font", font.use_font)
            pygui.list_box("Use font", font.use_index, [f.get_debug_name() for f in fonts], len(fonts))
            selected_font = fonts[font.use_index.value % len(fonts)]
            if pygui.collapsing_header("Style Editor"):
                pygui.show_style_editor()
        pygui.end()

        pygui.push_font(selected_font if font.use_font else fonts[0])
        pygui.text("After push こんにちは！テスト")
        pygui.text("©땔땕땗😀☠️⭐")
        pygui.text_unformatted(font.utf8_test)
        pygui.show_about_window()
        pygui.pop_font()
    pygui.end()
