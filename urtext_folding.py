import sublime, sublime_plugin

folding_margins = {
    'frame.urtext' : [2,2],
    'entity.name.struct.datestamp.urtext' : [1,1],
    'metadata_entry.urtext' : [0,0],
    'inline_node_5.urtext' : [1,1],
    'inline_node_4.urtext' : [1,1],
    'inline_node_3.urtext' : [1,1],
    'inline_node_2.urtext' : [1,1],
    'inline_node_1.urtext' : [1,1],
    'inline_node_as_metadata_1.urtext' : [3,1] }

scopes_to_fold = [
    'frame.urtext',
    'entity.name.struct.datestamp.urtext',
    'metadata_entry.urtext',
    'inline_node_5.urtext',
    'inline_node_4.urtext',
    'inline_node_3.urtext',
    'inline_node_2.urtext',
    'inline_node_as_metadata_1.urtext',
    'inline_node_1.urtext',    
    ]

class ToggleFoldSingleCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        region = self.view.extract_scope(self.view.sel()[0].a)
        scope_name = self.view.scope_name(self.view.sel()[0].a).split(' ')
        scope = get_scope_for_folding(scope_name)
        if scope and region:
            region = expand_scope_for_folding(scope_name, region, self.view)
            if region:
                if self.view.is_folded(region):
                    self.view.unfold(region)
                else:
                    self.view.fold(region)

class ToggleFoldAllCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        region = self.view.extract_scope(self.view.sel()[0].a)
        scope_name = self.view.scope_name(self.view.sel()[0].a).split(' ')
        scope = get_scope_for_folding(scope_name)
        if scope:
            region = expand_scope_for_folding(scope_name, region, self.view)
            if region:
                all_regions = self.view.find_by_selector(scope)
                if self.view.is_folded(region):
                    action = self.view.unfold
                else:
                    action = self.view.fold
                for r in all_regions:
                    r = expand_scope_for_folding(scope, r, self.view)
                    action(r)

def get_scope_for_folding(scope_name):
    for s in scopes_to_fold:
        if s in scope_name:
            return s

def expand_scope_for_folding(scope_name, region, view):
    for s in scopes_to_fold:  
        if s in scope_name:
            region = view.expand_to_scope(region.a, s)
            if region:
                return sublime.Region(
                    region.a + folding_margins[s][0],
                    region.b - folding_margins[s][1])
    return region