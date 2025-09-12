import urtext.syntax as syntax
import urtext.utils as utils

class UrtextAction:
    syntax = syntax
    utils = utils
    display = True
    inline_safe = False
    name = None

    def __init__(self, project_list):
        self.project_list = project_list
        self.selection_has_changed = False
        self.run_editor_method = project_list.run_editor_method
        self.source_node = None
        self.action_string = self.name.replace(' ','_').lower()

    def run(self):
        pass

    def on_node_visited(self, project, node_id):
        pass

    def open_the_node(self, selected_option):
        if selected_option == -1:
            return
        node_id = self.selections[selected_option].id
        self.project_list.current_project.open_node(node_id)

    def current_project(self):
        return self.project_list.current_project

    def doc(self):
        if self.source_node:
            documentation_node = self.source_node.get_sibling('Documentation')
            if not documentation_node:
                documentation_node = self.source_node.get_child('Documentation')
            if documentation_node:
                return documentation_node.contents(strip_first_line_title=True, stripped=False)
        return ''

