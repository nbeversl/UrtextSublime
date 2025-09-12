import subprocess
import sublime
import os

def get_view():
    window = sublime.active_window()
    if window:
        return window.active_view()

def open_file_to_position(filename, line=None, character=None, highlight_range=None, new_window=False, preview_only=False):
    if sublime.active_window():
        new_view = sublime.active_window().find_open_file(filename)
        if not new_view:
            if new_window is True:
                previous_windows = set(sublime.windows())
                sublime.run_command("new_window")
                active_window = next(iter(set(sublime.windows()) - previous_windows), None)
            else:
                active_window = sublime.active_window()
            new_view = active_window.open_file(filename)
        if preview_only is False:
            new_view.window().focus_view(new_view)
        focus_position(new_view, line=line, character=character, highlight_range=highlight_range)

def get_file_extension(filename):
    if len(os.path.splitext(filename)) == 2:
        return os.path.splitext(filename)[1].lstrip('.')

def close_inactive(extensions='urtext'):
    pass
    #todo re-implement
    for window in sublime.windows():
        for sheet in window.sheets():
            if not sheet.is_selected():
                if sheet.file_name() and get_file_extension(sheet.file_name()) in extensions:
                    sheet.view().set_scratch(True)
                    sheet.close()

def select_file_or_folder(callback):
    sublime.open_dialog(callback, allow_folders=True)

def insert_text(text):
    view = get_view()
    if view:
        view.run_command("insert", {"characters": text})
        return True
    return False

def save_current():
    view = get_view()
    if view:
        view.run_command('save')
        return True
    return False

def save_file(filename):
    view = sublime.active_window().find_open_file(filename)
    if view:
        view.run_command('save')
        return True
    return False

def set_clipboard(text):
    sublime.set_clipboard(text)
    info_message(text + '\ncopied to the clipboard')

def info_message(text):
    view = get_view()
    if view:
        view = sublime.active_window().active_view()
        view.show_popup(
            ''.join([
                '<div style="overflow-wrap: break-word;">',
                text,
                '</div>'
                ]),
            max_width=800, 
            max_height=400)

def get_buffer_id():
    view = get_view()
    if view:
        return view.id()

def set_buffer(filename, contents, identifier=None):
    if identifier is not None:
        for view in sublime.active_window().views():
            if view.id() == identifier:
                break
    else:
        view = sublime.active_window().find_open_file(filename)
    if view:
        view.run_command('urtext_replace', {
            'start' : 0,
            'end' :view.size(),
            'replacement_text' : contents
            })
        return True
    return False

def get_buffer(filename):
    view = None
    if filename:
        view = sublime.active_window().find_open_file(filename)
    else:
        view = get_view()
    if view:
        return view.substr(sublime.Region(0, view.size()))

def get_current_filename():
    window = sublime.active_window()
    if window:
        view = get_view()
        if view:
            return view.file_name()

def show_status(message):
    view = get_view()
    if view:
        view.set_status('Urtext', message)

def replace(filename='', start=0, end=0, full_line=False, replacement_text=''):
    if filename:
        view = sublime.active_window().find_open_file(filename)
    else:
        view = get_view()
    if view:
        if full_line is True:
            line_region = view.line(get_position())
            start = line_region.a
            end = line_region.b
        view.run_command('urtext_replace', {
            'start' : start,
            'end' :end,
            'replacement_text' : replacement_text
            })

def open_external_file(filepath):
    if sublime.platform() == "osx":
        process = subprocess.Popen(('open', filepath))
        if process.returncode != 0:
            print("Error opening file: probably file permissions ")
    elif sublime.platform() == "windows":
        os.startfile(filepath)
    elif sublime.platform() == "linux":
        subprocess.Popen(('xdg-open', filepath))

def close_current():
    view = get_view()
    if view:
        view.close()

def close_file(filename, save=None): # save kwarg not used in ST
    view = sublime.active_window().find_open_file(filename)
    if view:
        view.set_scratch(True)
        view.close()

def retarget_view(old_filename, new_filename):
    view = sublime.active_window().find_open_file(old_filename)
    if view:
        view.retarget(new_filename)

def refresh_views(file_list):
    if not isinstance(file_list, list):
        file_list = [file_list]
    for f in file_list:
        view = sublime.active_window().find_open_file(f)
        if view:
            view.window().run_command('revert')

def get_open_files():
    open_files = {}
    for window in sublime.windows():
        for view in window.views():
            file_name = view.file_name()
            if file_name:
                open_files[file_name] = view.is_dirty()
    return open_files

def show_panel(selections, callback, on_highlight=None):
    """ shows a quick panel with an option to cancel if -1 """
    window = sublime.active_window()
    if window:
        window.show_quick_panel(selections, callback, selected_index=-1, # doesn't work; Sublime Text Bug
            on_highlight=on_highlight)

def get_position():
    window = sublime.active_window()
    if window:
        view = window.active_view()
        if view:
            return view.sel()[0].a

def set_position(position):
    view = get_view()
    if view:
        view.sel().clear()
        view.sel().add(sublime.Region(position, position)) 

def get_line_and_cursor():
    view = get_view()
    file_pos = view.sel()[0].a
    col_pos = view.rowcol(file_pos)[1]
    full_line_region = view.line(view.sel()[0])
    full_line = view.substr(full_line_region)
    return full_line, col_pos, file_pos, [full_line_region.a, full_line_region.b]

def scratch_buffer(contents):
    window = sublime.active_window()
    view = window.new_file()
    view.set_scratch(True)
    view.assign_syntax("Packages/Urtext/sublime_urtext.sublime-syntax")
    view.run_command('urtext_replace', {
            'start' : 0,
            'end' :view.size(),
            'replacement_text' : contents
            })
    view.sel().clear()
    view.sel().add(sublime.Region(0, 0))
    return view.id()

def hover_popup(content, location=0):
    view = get_view()
    if view:
        content = content.replace('\n', '<br/>')
        markup = popup_markup % content
        view.show_popup(markup, location=location, max_width=512, max_height=512,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY)

def get_selection():
    view = get_view()
    if view:
        region = view.sel()[0]
        selection = view.substr(region)
        return selection, region.a

def open_file_dialog(callback, allow_folders=True):
    sublime.open_dialog(callback, allow_folders=allow_folders)

popup_markup = """
            <body id="linked_node_contents">
                <style>
                    h1 {
                        font-size: 1.1rem;
                        font-weight: 500;
                        margin: 0 0 0.5em 0;
                        font-family: system;
                    }
                    p {
                        margin-top: 0;
                    }
                    a {
                        font-weight: normal;
                        font-style: italic;
                        padding-left: 1em;
                        font-size: 1.0rem;
                    }
                    span.nums {
                        display: inline-block;
                        text-align: right;
                        color: color(var(--foreground) a(0.8))
                    }
                    span.context {
                        padding-left: 0.5em;
                    }
                </style>
                %s
            </body>
        """
def popup(content):
    view = get_view()
    if view:
        content = content.replace('\n', '<br/>')
        markup = popup_markup % content
        view.show_popup(markup, max_width=512, max_height=512, location=get_position())

def preview_file_at_position(filename, position):
    window = sublime.active_window()
    window.open_file(filename, flags=sublime.TRANSIENT)
    preview = window.active_sheet().view()
    focus_position(preview, character=position)

def focus_position(focus_view, line=None, character=None, highlight_range=None):
    if not focus_view.is_loading():
        if focus_view.window():
            if line is not None:
                focus_view.run_command("goto_line", {"line": line})
                return
            if character is not None:
                position_file(character, view=focus_view)
            if highlight_range:
                highlight_region(focus_view, highlight_range)
    else:
        sublime.set_timeout(lambda: focus_position(focus_view, line=line, character=character), 50) 
        sublime.set_timeout(lambda: focus_position(focus_view, line=line, character=character, highlight_range=highlight_range), 50) 

def highlight_region(view, highlight_range):
    view.add_regions(
        'highlight',
        [sublime.Region(highlight_range[0], highlight_range[1])],
        scope="region.yellowish")
    sublime.set_timeout(lambda: view.erase_regions('highlight'), 200)
            
def position_file(position, focus=True, view=None): 
    if view is None: view = get_view()
    if view:
        if focus:
            view.sel().clear()
            view.sel().add(sublime.Region(position, position))
        r = view.text_to_layout(position)
        view.show_at_center(position, animate=True)

def get_current_folder():
    window = sublime.active_window()
    view = window.active_view()
    folder = None

    if view and view.file_name():
        folder = os.path.dirname(view.file_name())

    if not folder:
        folders = window.folders()
        if folders:
            folder = folders[0]
    if not folder:
        project_data = window.project_data()
        if project_data and "folders" in project_data and project_data["folders"]:
            folder = project_data["folders"][0]["path"]
    return folder

editor_methods = {
    'open_file_to_position' : open_file_to_position,
    'error_message' : sublime.error_message,
    'insert_text' : insert_text,
    'save_current' : save_current,
    'set_clipboard' : set_clipboard,
    'open_external_file' : open_external_file,
    'get_buffer' : get_buffer,
    'set_buffer' : set_buffer,
    'replace' : replace,
    'info_message' : info_message,
    'close_current': close_current,
    'write_to_console' : print,
    'get_current_folder': get_current_folder,
    'status_message' : show_status,
    'close_file': close_file,
    'save_file': save_file,
    'retarget_view' : retarget_view,
    'select_file_or_folder': select_file_or_folder,
    'refresh_files' : refresh_views,
    'get_open_files': get_open_files,
    'preview_file_at_position' : preview_file_at_position,
    'close_inactive': close_inactive,
    'show_panel': show_panel,
    'open_file_dialog': open_file_dialog,
    'get_current_filename': get_current_filename,
    'get_position': get_position,
    'set_position': set_position,
    'get_line_and_cursor': get_line_and_cursor,
    'scratch_buffer': scratch_buffer,
    'hover_popup': hover_popup,
    'get_selection': get_selection
}
