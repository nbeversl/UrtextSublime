from UrtextSublime.implementation.editor_methods import get_line_and_cursor, highlight_region, position_file
from UrtextSublime.implementation.project_list_manager import check_urtext_project_list
from sublime_plugin import EventListener, TextCommand
import sublime, sublime_plugin

class ToggleTraverse(sublime_plugin.TextCommand):

	def run(self, edit):

		# determine whether then view already has traverse settings attached
		# if already on, turn it off
		if self.view.settings().has('traverse'):
			if self.view.settings().get('traverse') == 'true':
				self.view.settings().set('traverse', 'false')
				self.view.set_status('traverse', 'Traverse: Off')
				groups = self.view.window().num_groups()
				groups -= 1
				if groups == 0:
					groups = 1
				size_to_groups(groups, self.view)
				self.view.settings().set("word_wrap", True)
				return

		# otherwise, if 'traverse' is not in settings or it's 'false',
		# turn it on.
		self.view.settings().set('traverse', 'true')
		self.view.set_status('traverse', 'Traverse: On')

		#
		# Add another group to the left if needed
		#
		groups = self.view.window().num_groups() # 1-indexed
		active_group = self.view.window().active_group()  # 0-indexed
		if active_group + 1 == groups:
			groups += 1

		size_to_thirds(groups,self.view)
		self.view.settings().set("word_wrap", False)

		#
		# move any other open tabs to rightmost pane.
		#

		views = self.view.window().views_in_group(active_group)
		index = 0
		for view in views:
			if view != self.view:
				self.view.window().set_view_index(
					view,
					groups - 1,  # 0-indexed from 1-indexed value
					index)
				index += 1

		self.view.window().focus_group(active_group)


class TraverseFileTree(EventListener):

	def on_selection_modified(self, view):
		_UrtextProjectList = initialize_project_list(view.window(), add_project=False)
		if not _UrtextProjectList or not _UrtextProjectList.current_project:
			return
		
		called_from_view = view 
		#
		# TODO:
		# Add a failsafe in case the user has closed the next group to the left
		# but traverse is still on.
		#
		if called_from_view.window() == None:
			return
		if called_from_view.settings().get('traverse') == 'false':
			return

		# 1-indexed number of current groups ("group" = window division)
		self.groups = called_from_view.window().num_groups()        

		# 0-indexed number of the group with the tree view
		# Tree group is always made to be the view this was called from.
		self.tree_group = called_from_view.window().active_group() 
		if called_from_view.window().active_group() + 1 == self.groups:
			# if the called_from_group is rightmost, return
			# OR what if checking to see if the filenames are the same?
			return

		# 0-indexed number of the group with the content 
		# (may not yet exist)
		self.content_group = self.tree_group + 1        
		
		# TAB of the content (right) view. ("sheet" = tab)        
		self.content_tab = called_from_view.window().active_sheet_in_group(self.tree_group)
	  
		# the contents of the content tab. 
		contents = view.substr(sublime.Region(0, view.size()))

		""" 
		Scroll to a given position of the content 
		and then return focus to the tree view.
		"""
		def move_to_location(moved_view, 
			position, 
			tree_view):
			
			if not moved_view.is_loading():

				# focus on the window division with the content
				moved_view.window().focus_group(self.content_group)

				# show the content tab with the given position as top=				
				self.content_tab.view.sel().clear()
				self.content_tab.view.sel().add(sublime.Region(position, position))
				r = self.content_tab.view.text_to_layout(position)
				self.content_tab.view.set_viewport_position(r)

				# Make this the selected spot and set word wrap
				moved_view.sel().clear()
				moved_view.sel().add(position)
				moved_view.settings().set("word_wrap", "auto")

				# refocus the tree (left) view
				self.return_to_left(moved_view, tree_view)

			else:
				sublime.set_timeout(lambda: move_to_location(moved_view, position), 1)

		""" Only if Traverse is on for this group (window division) """
		if called_from_view.settings().get('traverse') == 'true':

			this_file = called_from_view.file_name()			
			if not this_file:
				return

			tree_view = called_from_view
			window = called_from_view.window()

			full_line, cursor, file_pos, _ = get_line_and_cursor()

			link = _UrtextProjectList.parse_link(full_line, this_file, cursor)

			if not link or not link.node_id or link.node_id not in _UrtextProjectList.current_project.nodes:
				return

			filename = _UrtextProjectList.current_project.get_file_name(link.node_id)
			position = _UrtextProjectList.current_project.nodes[link.node_id].start_position
			
			""" If the tree is linking to another part of its own file """
			if filename == this_file:
				instances = self.find_filename_in_window(filename, window)

				# Only allow two total instances of this file; 
				# one to navigate, one to edit
				if len(instances) < 2:
					window.run_command("clone_file")
					duplicate_file_view = self.find_filename_in_window(filename, window)[1]

				if len(instances) >= 2:
					duplicate_file_view = instances[1]
				
				""" If the duplicate view is in the content group """
				if duplicate_file_view in window.views_in_group(self.content_group):
					window.focus_view(duplicate_file_view)
					
					duplicate_file_view.sel().clear()
					duplicate_file_view.sel().add(sublime.Region(position, position))
					r = duplicate_file_view.text_to_layout(position)
					duplicate_file_view.set_viewport_position(r)
					
					self.return_to_left(duplicate_file_view, tree_view)
					duplicate_file_view.settings().set('traverse', 'false')
					return

				""" If the duplicate view is in the tree group """
				if duplicate_file_view in window.views_in_group(self.tree_group):
					window.focus_group(self.tree_group)
					duplicate_file_view.settings().set('traverse', 'false')  # this is for the cloned view
					window.set_view_index(duplicate_file_view, self.content_group, 0)

					duplicate_file_view.sel().clear()
					duplicate_file_view.sel().add(sublime.Region(position, position))
					r = duplicate_file_view.text_to_layout(position)
					duplicate_file_view.set_viewport_position(r)

					window.focus_view(tree_view)
					window.focus_group(self.tree_group)
					self.restore_traverse(view, tree_view)
					return

			else:
				""" The tree is linking to another file """
				window.focus_group(self.content_group)
				file_view = window.open_file(filename, sublime.TRANSIENT)
				file_view.sel().clear()
				file_view.sel().add(sublime.Region(position, position))
				r = file_view.text_to_layout(position)
				file_view.set_viewport_position(r)

				file_view.sel().add(position)
				window.focus_group(self.tree_group)

				def focus_position(focus_view, position):
					if not focus_view.is_loading():
						if focus_view.window():
							focus_view.window().focus_view(focus_view)
							position_file(position, view=focus_view)
							highlight_region(file_view, [
								_UrtextProjectList.current_project.nodes[link.node_id].start_position,
								_UrtextProjectList.current_project.nodes[link.node_id].end_position
								])
							window.focus_group(self.tree_group)
					else:
						sublime.set_timeout(lambda: focus_position(focus_view, position), 50) 

				focus_position(file_view, position)

	def find_filename_in_window(self, filename, window):
		instances = []
		for view in window.views():
			if view.file_name() == filename:
				instances.append(view)
		return instances

	def restore_traverse(self, wait_view, traverse_view):
		if not wait_view.is_loading():
			traverse_view.settings().set('traverse', 'true')
		else:
			sublime.set_timeout(
				lambda: self.return_to_left(wait_view, traverse_view), 1)
			return

	""" 
	Return to the left (tree) view,
	after waiting for another view to finish loading.
	"""

	def return_to_left(self, 
		wait_view, 
		return_view):
		
		if not wait_view.window():
			return

		if not wait_view.is_loading():
			wait_view.window().focus_view(return_view)
			wait_view.window().focus_group(self.tree_group)
		
		else:
			sublime.set_timeout(lambda: self.return_to_left(wait_view, return_view), 1)

def size_to_groups(groups, view):
	panel_size = 1 / groups
	cols = [0]
	cells = [[0, 0, 1, 1]]
	for index in range(1, groups):
		cols.append(cols[index - 1] + panel_size)
		cells.append([index, 0, index + 1, 1])
	cols.append(1)
	view.window().set_layout({"cols": cols, "rows": [0, 1], "cells": cells})

def size_to_thirds(groups,view):
	# https://forum.sublimetext.com/t/set-layout-reference/5713
	# {'cells': [[0, 0, 1, 1], [1, 0, 2, 1]], 'rows': [0, 1], 'cols': [0, 0.5, 1]}
	view.window().set_layout({"cols": [0.0, 0.3333, 1], "rows": [0, 1], "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]})

