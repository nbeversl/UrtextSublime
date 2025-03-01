import urtext.syntax as syntax
import webbrowser
import os

class UrtextLink:

	def __init__(self, matching_string, node, project_list):
		self.containing_node = node
		self.matching_string = matching_string
		self.filename = None
		self.project_list = project_list
		self.bound = False
		self.bound_argument = None
		self.project_name = None
		self.is_http = False
		self.is_node = False
		self.node_id = None
		self.is_pointer = False
		self.is_file = False
		self.is_action = False
		self.is_missing = False
		self.position_in_string = None
		self.dest_node_position = 0
		self.character_number = None
		self.line_number = None
		self.suffix = ''
		self.dest_file_line = 0
		self.url = None
		self.path = None

	def get_node(self):
		if self.is_node or self.is_pointer:
			dest_node = self.project_list.current_project.get_node(self.node_id)
			if dest_node:
				return dest_node

	def click(self):
		if self.bound:
			return self.bound_action()
		elif self.project_name:
			self.project_list.set_current_project(self.project_name)
		elif self.filename:
			self.project_list.set_current_project(os.path.dirname(self.filename))
		dest_node = self.get_node()
		if dest_node:
			if self.is_action:
				for frame in self.project_list.current_project._get_frames(target_node=dest_node):
					modified_buffers, _l = self.project_list.current_project._run_frame(frame, flags=['-target_link_clicked'])
					for b in modified_buffers:
						b.write_buffer_contents()
			else:
				return self.project_list.current_project.open_node(dest_node.id,
					position=dest_node.start_position + self.dest_node_position)
		elif self.is_node:
			return self.project_list.current_project.run_editor_method('popup', 'Node cannot be found in the current project.')
		elif self.is_file:
			path = None
			rel_path = os.path.abspath(os.path.join(self.project_list.current_project.entry_path, self.path))
			if os.path.exists(rel_path):
				path = rel_path
			else:
				abs_path = os.path.abspath(os.path.join(os.path.dirname(self.filename), self.path))
				if os.path.exists(abs_path):
					path = abs_path
			if path:
				ext = get_file_extension(self.path)
				editor_extensions = self.project_list.current_project.get_setting_as_text('open_in_editor')
				if editor_extensions and ext in editor_extensions:
					return self.project_list.current_project.run_editor_method(
						'open_file_to_position',
						path,
						character=self.character_number,
						line=self.line_number)
				return self.project_list.current_project.run_editor_method('open_external_file', path)
			return self.project_list.current_project.handle_info_message('Path does not exist')
		elif self.is_http:
			if open_http_link(self.url) is False:
				self.project_list.current_project.handle_info_message('Could not open the weblink')

	def hover(self):
		if self.is_node or self.is_pointer:
			dest_node = self.project_list.current_project.get_node(self.node_id)
			if dest_node:
				for frame in self.project_list.current_project._get_frames(source_node=dest_node):
					modified_buffers, _l = self.project_list.current_project._run_frame(frame, flags=['-link_hovered'])
					for b in modified_buffers:
						b.write_buffer_contents()
		self.project_list.current_project.run_hook('on_link_hovered', self)

	def bound_action(self):
		return self.project_list.bound_action(self.containing_node, self.bound_argument)

	def rewrite(self, include_project=False):
		# not currently used
		link_modifier = ''
		if self.is_action:
			link_opening_wrapper = ''.join([
					syntax.link_opening_wrapper,
					syntax.node_link_modifiers['action']
				])
		elif self.is_file:
			link_opening_wrapper = ''.join([
					syntax.link_opening_wrapper,
					file_link_modifiers['file']
				])

		return ''.join([
				syntax.other_project_link_prefix,
				'"%s"' % self.project_name if self.project_name and include_project else '',
				link_opening_wrapper,
				link_modifier,
				syntax.pointer_closing_wrapper if self.is_pointer else syntax.link_closing_wrapper,
				(':%s' % dest_node_position) if self.dest_node_position else ''
			])

	def exists(self):
		if self.is_file and self.path:
			if os.path.exists(self.path):
				return True
			if os.path.exists(os.path.abspath(
				os.path.join(os.path.dirname(self.containing_node.filename), self.path))):
				return True
			return False

	def replace(self, replacement):
		if self.containing_node:
			node_contents = self.containing_node.contents(stripped=False)
			replacement_contents = ''.join([
				node_contents[:self.start_position],
				replacement,
				node_contents[self.start_position+len(self.matching_string):]
				])
			self.containing_node.project._set_node_contents(
				containing_node.id,
				replacement_contents,
				preserve_title=False)

	def end_position(self):
		return self.position_in_string + len(self.matching_string)

def open_http_link(link):
    if link[:8] != 'https://' and link [:7] != 'http://':
        link = 'https://' + link
    return True if webbrowser.get().open(link) else False


def get_file_extension(filename):
    if len(os.path.splitext(filename)) == 2:
        return os.path.splitext(filename)[1].lstrip('.')