from UrtextSublime.urtext.project_list import ProjectList
from UrtextSublime.implementation.editor_methods import editor_methods, get_current_folder
import sublime

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
    return _UrtextProjectList

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