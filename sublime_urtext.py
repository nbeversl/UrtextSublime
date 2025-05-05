from UrtextSublime.implementation.urtext_folding import ToggleFoldSingleCommand, ToggleFoldAllCommand
from UrtextSublime.implementation.urtext_traverse import ToggleTraverse, TraverseFileTree
from UrtextSublime.implementation.editor_methods import editor_methods
from UrtextSublime.implementation.project_list_manager import initialize_project_list, check_urtext_project_list, _UrtextProjectList
from sublime_plugin import EventListener, ViewEventListener
from UrtextSublime.urtext.project_list import ProjectList
import sublime_plugin
import subprocess
import sublime
import os

class RunUrtextCallCommand(sublime_plugin.TextCommand):

    def run(self, edit, urtext_call):
        _UrtextProjectList = check_urtext_project_list()
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
        _UrtextProjectList = check_urtext_project_list()
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
        _UrtextProjectList = check_urtext_project_list()
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
        _UrtextProjectList = check_urtext_project_list()
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
    
        _UrtextProjectList = check_urtext_project_list()
        if _UrtextProjectList and _UrtextProjectList.current_project:
            if self.view and ( self.view.file_name() and self.view.is_dirty()
                and self.view.file_name() in _UrtextProjectList.current_project.files):
                    self.view.run_command('save')
                            
class MouseOpenUrtextLinkCommand(sublime_plugin.TextCommand):

    def run(self, edit, **kwargs):
        _UrtextProjectList = check_urtext_project_list()
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
            _UrtextProjectList = check_urtext_project_list()
            if not _UrtextProjectList:
                _UrtextProjectList = ProjectList(path, editor_methods=editor_methods)
            else:
                _UrtextProjectList.init_project(path, make_current=True, action='urtext_home')
        sublime.select_folder_dialog(create_project)

class UrtextDebugCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        _UrtextProjectList = check_urtext_project_list()
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