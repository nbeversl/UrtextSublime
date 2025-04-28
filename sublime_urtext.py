from sublime_plugin import EventListener, ViewEventListener
from UrtextSublime.urtext.project_list import ProjectList
import sublime_plugin
import subprocess
import sublime
import os

_UrtextProjectList = None

def check_urtext_project_list():
    global _UrtextProjectList
    window = sublime.active_window()
    if window:
        view = window.active_view()
    if not _UrtextProjectList:
        _UrtextProjectList = initialize_project_list(window)
    if _UrtextProjectList:
        folder = get_current_folder()
        if folder and not _UrtextProjectList.set_current_project(folder):
            _UrtextProjectList.init_project(folder, make_current=True)

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
    show_popup(text + '\ncopied to the clipboard')

def show_popup(text):
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

def preview_urtext_node(node_id):
    window = sublime.active_window()
    if _UrtextProjectList.current_project:
        filename, node_position = _UrtextProjectList.current_project.get_file_and_position(node_id)
        if filename:
            window.open_file(filename, flags=sublime.TRANSIENT)
            preview = window.active_sheet().view()
            focus_position(preview, character=node_position)

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
    'popup' : show_popup,
    'close_current': close_current,
    'write_to_console' : print,
    'get_current_folder': get_current_folder,
    'status_message' : show_status,
    'close_file': close_file,
    'save_file': save_file,
    'retarget_view' : retarget_view,
    'select_file_or_folder': select_file_or_folder,
    'refresh_files' : refresh_views,
    'preview_urtext_node': preview_urtext_node,
    # 'close_inactive': close_inactive,
    'show_panel': show_panel,
    'open_file_dialog': open_file_dialog,
    'get_current_filename': get_current_filename,
    'get_position': get_position,
    'set_position': set_position,
    'get_line_and_cursor': get_line_and_cursor,
    'scratch_buffer': scratch_buffer,
    'popup': popup,
    'hover_popup': hover_popup,
    'get_selection': get_selection
}

def initialize_project_list(window, add_project=True):

    global _UrtextProjectList

    if window:
        folder = get_current_folder()
        if _UrtextProjectList and _UrtextProjectList.current_project:
            if _UrtextProjectList.current_project.has_folder(folder):
                return _UrtextProjectList
        if _UrtextProjectList and folder:
            if not _UrtextProjectList.set_current_project(folder) and add_project:
                return _UrtextProjectList.initialize_project(folder)
        elif folder and add_project:
            _UrtextProjectList = ProjectList(folder, editor_methods=editor_methods)
        return _UrtextProjectList

class RunUrtextCallCommand(sublime_plugin.TextCommand):

    def run(self, edit, urtext_call):
        global _UrtextProjectList
        check_urtext_project_list()
        if _UrtextProjectList:
            if urtext_call == 'toggle_traverse':
                return self.view.run_command('toggle_traverse')
            if urtext_call == 'toggle_fold_single':
                return self.view.run_command('toggle_fold_single')
            if urtext_call == 'toggle_fold_all':
                return self.view.run_command('toggle_fold_all')
            if urtext_call == 'insert_link_to_file':
                return self.view.run_command('insert_file_link')
            if urtext_call == 'open_urtext_link':
                line, cursor, file_pos, line_range = get_line_and_cursor()
                return _UrtextProjectList.handle_link(line, self.view.file_name(), get_position(), col_pos=cursor, identifier=self.view.id())
            _UrtextProjectList.run_action(urtext_call)
 
class UrtextShowAllActionsCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        global _UrtextProjectList
        check_urtext_project_list()
        if _UrtextProjectList:
            _UrtextProjectList.run_action('show_all_actions')

class UrtextReplace(sublime_plugin.TextCommand):
    def run(self, edit, start=0, end=0, replacement_text=''):
        self.view.replace(edit, sublime.Region(start, end), replacement_text)    

class UrtextEventListeners(EventListener):

    def on_activated(self, view):
        if view and view.file_name() and _UrtextProjectList:
            _UrtextProjectList.visit_file(view.file_name())
                
    def on_post_save(self, view):
        visited_files = []
        if view and view.file_name() and _UrtextProjectList:
            _UrtextProjectList.on_modified(view.file_name())
            visited_files.append(view.file_name())
            window = view.window()
            if window:
                num_groups = window.num_groups()
                for index in range(0, num_groups):
                    active_view = window.active_sheet_in_group(index)
                    if active_view:
                        filename = active_view.file_name()
                        if filename and filename not in visited_files:
                            _UrtextProjectList.on_modified(filename)
                            visited_files.append(filename)

    def on_hover(self, view, point, hover_zone):
        if view.is_folded(sublime.Region(point, point)) and _UrtextProjectList:
            for r in view.folded_regions():
                if point in [r.a, r.b]:
                    contents = view.export_to_html(sublime.Region(r.a,r.b))

            def unfold_region(href_region):
                points = href_region.split('-')
                region = sublime.Region(int(points[0]), int(points[1]))
                view.unfold(region)
                view.hide_popup()

            contents += '<a href="%s-%s">unfold</a>' % (r.a, r.b)
            row, col_pos = self.view.rowcol(point)
            view.show_popup(contents, 
                max_width=512, 
                max_height=512, 
                location=get_position(),
                on_navigate=unfold_region)

        if _UrtextProjectList and _UrtextProjectList.current_project:
            row, col_pos = view.rowcol(point)
            full_line = view.substr(view.full_line(view.line(point)))
            _UrtextProjectList.on_hover(full_line, view.file_name(), point, col_pos=col_pos, identifier=view.id())

    def on_query_completions(self, view, prefix, locations):
        _UrtextProjectList = initialize_project_list(view.window(), add_project=False)
        if _UrtextProjectList and _UrtextProjectList.current_project:
            if _UrtextProjectList.set_current_project(os.path.dirname(view.file_name())):
                subl_completions = []
                proj_completions = _UrtextProjectList.current_project.get_all_meta_pairs()
                for c in proj_completions:
                    if '::' in c:
                        t = c.split('::')
                        if len(t) > 1:
                            subl_completions.append([t[1]+'\t'+c, c])
                    elif c[0] == '#':
                        subl_completions.append(['#'+c[1:]+'\t'+c, c])
                for t in _UrtextProjectList.current_project.title_completions():
                    subl_completions.append([t[0],t[1]])
                return (subl_completions, sublime.INHIBIT_WORD_COMPLETIONS, sublime.DYNAMIC_COMPLETIONS)

class UrtextViewEventListener(ViewEventListener):

    def on_deactivated(self):

        if _UrtextProjectList and _UrtextProjectList.current_project:
            if self.view and ( self.view.file_name() and self.view.is_dirty()
                and self.view.file_name() in _UrtextProjectList.current_project.files):
                    self.view.run_command('save')
                            
class MouseOpenUrtextLinkCommand(sublime_plugin.TextCommand):

    def run(self, edit, **kwargs):
        global _UrtextProjectList
        if _UrtextProjectList:
            click_position = self.view.window_to_text((kwargs['event']['x'],kwargs['event']['y']))
            region = self.view.line(click_position)
            file_pos = region.a
            full_line_region = self.view.full_line(region)
            row, col_pos = self.view.rowcol(click_position)
            full_line = self.view.substr(sublime.Region(full_line_region.a-1, full_line_region.b))
            link = _UrtextProjectList.handle_link(
                full_line,
                self.view.file_name(),
                file_pos,
                identifier=self.view.id(),
                col_pos=col_pos)

    def want_event(self):
        return True

class UrtextStarterProjectCommand(sublime_plugin.TextCommand):
   
    def run(self, edit):
        def create_project(path):
            ProjectList.make_starter_project(path)
            global _UrtextProjectList
            if not _UrtextProjectList:
                _UrtextProjectList = ProjectList(path, editor_methods=editor_methods)
            else:
                _UrtextProjectList.init_project(path, make_current=True, action='urtext_home')
        sublime.select_folder_dialog(create_project)

class UrtextDebugCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        global _UrtextProjectList
        if _UrtextProjectList:

            node = _UrtextProjectList.current_project.get_node_from_position(
                self.view.file_name(), 
                self.view.sel()[0].a)
            if not node:
                return print('No Node found here')
                
            print('UNTITLED: %s' % node.untitled)
            print('DYNAMIC: %s' % node.is_dynamic)
            print('NODE ID: %s' % node.id)
            print('First line title: %s' % node.first_line_title)
            print('NESTED: %s' % str(node.nested))
            print('RANGES: ')
            print(node.ranges)
            print('IS ROOT: %s' % node.is_root_node)
            print('IS META: %s' % node.is_meta)
            print('NODE PARENT: %s' % node.parent)
            print('LINKS: ')
            print(node.links)
            print('LINKS IDS: ')
            print(node.links_ids())
            print('METADATA: ')
            print(node.metadata.log())
            print('EXPORTS:')
            print(node.export_points)
            print('DESCENDANTS:')
            for n in node.descendants():
                print(n.id)
            print('EMBEDDED SYNTAXES')
            print(node.ranges_with_embedded_syntaxes())
            # n = node
            # for r in n.embedded_syntax_ranges:
            #     print('IN NODE:')
            #     print(r)
            #     print('IN FILE:')
            #     pos0 = n.get_file_position(r[0])
            #     pos1 = n.get_file_position(r[1])
            #     print(pos0, pos1)
            #     # print(self.view.sel()[0].a in range(r[0], r[1]))
            #     print(self.view.sel()[0].a in range(pos0, pos1))
            print('------------------------')
        else:
            return print('No urtext project')

class NoAsync(sublime_plugin.TextCommand):

    def run(self, edit):
        if _UrtextProjectList:
            _UrtextProjectList.is_async = False
            print("async off")
        else:
            print("no urtext project")

"""
Utility functions
"""


def get_view():
    window = sublime.active_window()
    if window:
        return window.active_view()
