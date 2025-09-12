import os
import concurrent.futures
import sys
import shutil

if os.path.exists(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sublime.txt')):
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../vendor'))
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from urtext.project import UrtextProject
from urtext.call import UrtextCall
import urtext.syntax as syntax
import urtext.utils as utils

class ProjectList:
    utils = utils

    def __init__(self,
                 entry_point,
                 is_async=True,
                 base_project_path=os.path.join(os.path.dirname(__file__), 'base_project'),
                 urtext_location=None,
                 editor_methods=None):

        if urtext_location:
            sys.path.append(urtext_location)

        self.is_async = is_async
        #self.is_async = False  # development
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.editor_methods = editor_methods if editor_methods else {}
        self.entry_point = entry_point.strip()
        self.calls = {}
        self.actions = {}
        self.project_instance_calls = {}
        self.project_list_instance_calls = {}
        self.projects = []
        self.entry_points = []
        self.current_project = None
        self.node_opened = False
        if base_project_path:
            self.base_project_path = base_project_path
            self.init_project(os.path.abspath(base_project_path), visible=False)
        if os.path.abspath(base_project_path) != os.path.abspath(self.entry_point):
            self.init_project(os.path.abspath(self.entry_point), initial=True, visible=True)

    def init_project(self,
        entry_point,
        new_file_node_created=False,
        initial=False,
        visible=True,
        make_current=False,
        action=None):
        self.execute(self._init_project, entry_point, new_file_node_created=new_file_node_created, initial=initial, make_current=make_current, visible=visible, action=action)

    def _init_project(self,
        entry_point,
        new_file_node_created=False,
        initial=None,
        visible=True,
        make_current=False,
        action=None):

        if self.get_project(entry_point):
            return

        project = UrtextProject(entry_point,
                                project_list=self,
                                editor_methods=self.editor_methods,
                                initial=initial,
                                new_file_node_created=new_file_node_created)
        self.projects.append(project)
        if initial or make_current:
            self.current_project = project
        if project.initialize(visible=visible, make_current=make_current, action=action):
            if initial or make_current:
                self.current_project = project
            self.entry_points.append(project.entry_point)
            if action:
                self.run_action(action)
        else:
            self.projects.remove(project)

    def execute(self, function, *args, **kwargs):
        if self.is_async:
            return self.executor.submit(function, *args, **kwargs)
        return function(*args, **kwargs)
    
    def get_setting(self, setting, calling_project):
        for project in [p for p in self.projects if p.entry_point != calling_project.entry_point]:
            if setting in project.get_propagated_settings(_called_from_project_list=True):
                values = project.get_setting(setting, _called_from_project_list=True)
                if values:
                    return values
        return []

    def _get_project_from_buffer(self, buffer_id):
        for project in self.projects:
            if buffer_id in project.buffers:
                return project

    def on_hover(self, string, filename, file_pos, col_pos=0, identifier=None):
        for p in self.projects:
            p.run_hook('on_hover', string, filename, file_pos, col_pos=col_pos, identifier=None)

    def parse_link(self, string, filename, file_pos, col_pos=0, identifier=None):
        project = None
        node = None
        if filename:
            project = self._get_project_from_path(filename)
        if filename is None and identifier is not None:
            project = self._get_project_from_buffer(identifier)
        if project:
            node = project.get_node_from_position(filename, file_pos, identifier=identifier) if project else None
        link = utils.get_link_from_position_in_string(string, col_pos, node, self, include_http=True)
        return link

    def bound_action(self, node, action_string):
        if node:
            node = self.current_project.get_node(node.id)
            if node:
                return node.bound_action(action_string)
        return self.run_action(action_string)

    def handle_link(self, string, filename, file_pos, col_pos=0, identifier=None):
        link = self.parse_link(string, filename, file_pos, col_pos=col_pos, identifier=identifier)
        if not link:
            return self.handle_unusable_link()
        link.filename = filename
        link.click()

    def handle_unusable_link(self):
        if self.current_project and not self.current_project.compiled:
            message = "Project is still compiling"
        else:
            message = "No link"
        return self.run_editor_method('info_message', message)

    def on_modified(self, filename):
        return self.execute(self._on_modified, filename)

    def _on_modified(self, filename):
        project = self._get_project_from_path(
            os.path.dirname(filename))
        if project:
            self.current_project = project
            return project.on_modified(filename)
        else:
            self._init_project(filename)

    def _get_project_from_path(self, path):
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        for project in self.projects:
            if path in project.get_settings_paths():
                return project

    def _get_project_from_title(self, title):
        for project in self.projects:
            if title == project.title():
                return project

    def get_project(self, title_or_path):
        project = self._get_project_from_title(title_or_path)
        if not project:
            project = self._get_project_from_path(title_or_path)
        return project

    def set_current_project(self, project_or_title_or_path, visible=True, run_hook=False):
        if isinstance(project_or_title_or_path, UrtextProject):
            project = project_or_title_or_path
        else:
            project = self.get_project(project_or_title_or_path)
        if not project:
            return
        if (not self.current_project) or (
                project.title() != self.current_project.title()):
            self.current_project = project
            if visible:
                self.run_editor_method('info_message', 'Switched to project: %s ' % self.current_project.title())
            project_paths = self.current_project.get_settings_paths()
            if project_paths and run_hook:
                self.current_project.on_selected()
        return self.current_project

    def build_contextual_link(self,
                              node_id,
                              project_title=None,
                              pointer=False,
                              include_project=False):

        if node_id:
            if project_title is None:
                project = self.current_project
            else:
                project = self.get_project(project_title)
            if pointer:
                link = self.utils.make_node_pointer(node_id)
            else:
                link = self.utils.make_node_link(node_id)
            if include_project or project != self.current_project:
                link = ''.join([
                    self.utils.make_project_link(project.title()),
                    link])
            return link

    def project_titles(self):
        return [p.title() for p in self.projects if p.visible]

    def get_project_title_from_link(self, target):
        match = syntax.project_link_c.search(target)
        if match:
            return match.group(2).strip()
        return target

    def get_project_from_link(self, target):
        project_name = self.get_project_title_from_link(target)
        project = self.get_project(project_name)
        return project if project else None

    def get_current_project(self, path):
        for project in self.projects:
            if path in project.get_settings_paths():
                return project
        return None

    def visit_file(self, filename):
        self.set_current_project(filename)
        if self.current_project:
            self.notify_node_opened()
            return self.execute(self.current_project.visit_file, filename)

    def move_file(self,
                  old_filename,
                  source_project_name_or_path,
                  destination_project_name_or_path,
                  replace_links=True):

        # TODO - should the source project be needed if the
        # filename is provided?

        """
        Move a file from one project to another, checking for
        node ID duplication in the new project location, and 
        optionally replacing links to every affected node.
        """
        source_project = self.get_project(source_project_name_or_path)
        destination_project = self.get_project(destination_project_name_or_path)

        if not destination_project:
            self.run_editor_method('info_message', 'Destination project was not found.')
            return None

        if old_filename not in source_project.files:
            self.run_editor_method('info_message', 'File not included in the current project.')
            return None

        moved_nodes = list(source_project.files[old_filename].nodes)
        source_project.drop_buffer(source_project.files[old_filename])
        new_filename = os.path.join(
            destination_project.get_settings_paths()[0],
            os.path.basename(old_filename))
        os.rename(old_filename, new_filename)
        """
        add_file() will raise an exception if the file makes
        duplicate nodes in the destination project
        """
        changed_ids = destination_project.add_file(new_filename)

        if replace_links:
            for moved_node in moved_nodes:
                nodes_with_links = source_project.get_links_to(moved_node.id)
                for node_with_link in nodes_with_links:
                    node_with_link.replace_links(
                        moved_node.id,
                        new_project=destination_project.title())

        source_project.run_hook('on_file_moved_to_other_project',
                                source_project,
                                destination_project,
                                old_filename,
                                new_filename)

        self.run_editor_method('info_message', 'File moved.')
        self.run_editor_method('close_file', old_filename, save=False)
        return changed_ids

    def editor_copy_link_to_node(self, 
                                 position,
                                 filename,
                                 include_project=False):

        project = self.set_current_project(filename)
        if project:
            project.editor_copy_link_to_node(position, filename, include_project=include_project)

    def get_all_paths(self):
        paths = [os.path.abspath(os.path.dirname(p)) for p in self.entry_points]
        return paths

    def get_all_meta_pairs(self):
        meta_values = []
        for project in self.projects:
            meta_pairs = project.get_all_meta_pairs()
            for pair in meta_pairs:
                if pair not in meta_values:
                    meta_values.append(pair)
        return meta_values

    def replace_links(self,
                      old_project_path_or_title,
                      new_project_path_or_title,
                      node_id):
        old_project = self.get_project(old_project_path_or_title)
        new_project = self.get_project(new_project_path_or_title)
        old_project.replace_links(node_id, new_project=new_project.title())

    def titles(self):
        title_list = {}
        for project in self.projects:
            for node_id in project.nodes:
                title_list[project.nodes[node_id].title] = (project.title(), node_id)
        return title_list

    def is_in_export(self, filename, position):
        if not self.current_project:
            return None
        return self.current_project.is_in_export(filename, position)

    def editor_insert_link_to_node(self, node, project_title=None):
        if project_title is None:
            project_title = self.current_project.title()
        if project_title:
            link = self.build_contextual_link(node.id, project_title=project_title)
            self.run_editor_method('insert_text', link)

    def delete_file(self, file_name, project=None):
        if not project:
            project = self.current_project
        project.delete_file(file_name)

    def run_editor_method(self, method_name, *args, **kwargs):
        if method_name in self.editor_methods:
            return self.editor_methods[method_name](*args, **kwargs)
        print('Not implemented (%s)' % method_name)
        return False

    def handle_message(self, message):
        self.run_editor_method('info_message', message)
        print(message)

    def add_call(self, call):
        
        for n in call.name:
            self.calls[n] = call

        class call(call, UrtextCall):
            pass
            
        if call.project_list_instance:
            if call.name[0] not in self.project_list_instance_calls:
                instance_call = call(self)
                instance_call.on_added()
                self.project_list_instance_calls[call.name[0]] = instance_call
                return

        if call.project_instance:
            self.project_instance_calls[n[0]] = call

    def get_call_instance(self, call_name):
        get_call_instance = None
        if call_name in self.project_list_instance_calls:
            get_call_instance = self.project_list_instance_calls[call_name]
        return get_call_instance

    def run_call(self, call_name, *args, **kwargs):
        call_instance = self.get_call_instance(call_name)
        if not call_instance:
            self.handle_message('call %s is not available' % call_name)
            return None
        return call_instance.run(*args, **kwargs)

    def make_file_link(self, path):
        if path:
            return utils.make_file_link(path)

    def notify_node_opened(self):
        self.node_opened = True

    def node_has_been_opened(self):
        return self.node_opened

    def action_menu(self):
        
        def callback(selection):
            selections = list(self.actions.keys())
            if selection > -1 :
                if selections[selection] in self.actions:
                    return self.actions[selections[selection]].run()
                return self.handle_message('No selection for %s' % selections[selection])

        selections = list(self.actions.keys())
        self.run_editor_method('show_panel', selections, callback)

    def run_action(self, selection):
        selection = selection.replace(' ', '_').lower()
        if self.current_project and selection in self.current_project.actions:
            if self.current_project.actions[selection].inline_safe:
                return self.current_project.actions[selection].run()
            return self.execute(self.current_project.actions[selection].run)
        if selection in self.actions:
            if self.actions[selection].inline_safe:
                return self.actions[selection].run()
            self.execute(self.actions[selection].run)

    @classmethod
    def make_starter_project(self, folder):
        if os.path.isdir(folder):
            starter_proj_dir = os.path.join(os.path.dirname(__file__), 'starter_project')
            for f in os.listdir(os.path.join(os.path.dirname(__file__), 'starter_project')):
                file_path = os.path.join(starter_proj_dir, f)
                if os.path.basename(file_path) == 'Urtext Starter Project.urtext':
                    with open(file_path, 'r', encoding="utf-8") as f:
                        contents = f.read()
                    contents = contents.replace(NO_MODIFY_WARNING,'')
                    with open(os.path.join(folder, os.path.basename(file_path)), "w", encoding="utf-8") as f:
                        f.write(contents)
                    continue
                if not os.path.isdir(file_path):
                    if len(os.path.splitext(file_path)) == 2 and os.path.splitext(file_path)[1] == '.urtext':
                        shutil.copyfile(file_path, os.path.join(folder, f))
        else:
            print(folder, 'is not a folder')


NO_MODIFY_WARNING = """!---------------------------------------------------
IF YOU ARE SEEING THIS TEXT, YOU ARE VIEWING THE STARTER PROJECT IN THE URTEXT LIBRARY. Do not modify it here; instead, copy it to a new project using either "Urtext: Create Starter Project" in the Sublime Command palette or the "Create Starter Project" action from within Urtext.
!-----------------------------------------------------"""
