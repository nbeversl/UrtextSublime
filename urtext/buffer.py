import re
from urtext.node import UrtextNode
from urtext.utils import strip_backtick_escape, get_id_from_link
import urtext.syntax as syntax

class UrtextBuffer:

    urtext_node = UrtextNode

    def __init__(self, project, filename, contents):
        self.contents = contents
        self.project = project
        self.identifier = None
        self.meta_to_node = []
        self.filename = filename
        self.nodes = []
        self.root_node = None
        self._lex_and_parse()
        
    def _lex_and_parse(self):
        self.nodes = []
        self.root_node = None
        self.meta_to_node = []
        contents = self._get_contents()
        symbols = self._lex(contents)
        self._parse(contents, symbols)
        for node in self.nodes:
            node.buffer = self
            node.filename = self.filename
        self._assign_parents(self.root_node)
        self._check_untitled_nodes()
        self._check_duplicate_ids()
        self.resolve_nodes()

    def _lex(self, contents, start_position=0):
        symbols = {}
        embedded_syntaxes = []
        ranges, contents = strip_backtick_escape(contents)

        for match in syntax.embedded_syntax_c.finditer(contents):
            embedded_syntaxes.append([match.start(), match.end()])
        for symbol, symbol_type in syntax.compiled_symbols.items():
            for match in symbol.finditer(contents):
                is_embedded = False
                for r in embedded_syntaxes:
                    if match.start() in range(r[0], r[1]):
                        is_embedded = True
                        break
                if is_embedded:
                    continue
                if symbol_type == 'meta_to_node':
                    self.meta_to_node.append(match)
                    continue
                symbols[match.start() + start_position] = {}
                symbols[match.start() + start_position]['type'] = symbol_type

                if symbol_type == 'pointer':
                    symbols[match.start() + start_position]['contents'] = get_id_from_link(match.group())

        symbols[len(contents) + start_position] = { 'type': 'EOB' }
        return symbols

    def _parse(self, contents, symbols, nested_levels={}, nested=0, child_group={}, start_position=0):
 
        ranges, unstripped_contents = strip_backtick_escape(contents)
        last_position = start_position
        pointers = {}

        for position in sorted(symbols.keys()):

            # Allow node nesting arbitrarily deep
            nested_levels[nested] = [] if nested not in nested_levels else nested_levels[nested]
            pointers[nested] = [] if nested not in pointers else pointers[nested]
            if symbols[position]['type'] == 'pointer':
                pointers[nested].append({ 
                    'id' : symbols[position]['contents'],
                    'position' : position
                    })
                continue

            elif symbols[position]['type'] == 'opening_wrapper':
                if position == 0:
                    nested_levels[nested].append([0, 0])
                    nested_levels[nested] = []
                else:
                    if position == last_position:
                        nested += 1
                        last_position += 1
                        #consecutive bracket nodes, i.e. }{
                        continue
                    nested_levels[nested].append([last_position, position])
                position += 1 #wrappers exist outside range
                nested += 1
 
            elif symbols[position]['type'] == 'closing_wrapper':
                nested_levels[nested].append([last_position, position])
                if nested <= 0:
                    contents = contents[:position] + contents[position + 1:]
                    return self.set_buffer_contents(contents)

                position += 1 #wrappers exist outside range
                node = self.add_node(
                    nested_levels[nested],
                    nested,
                    contents,
                    start_position=start_position)

                if nested + 1 in child_group:
                    for child in child_group[nested+1]:
                        child.parent = node
                    node.children = child_group[nested+1]
                    del child_group[nested+1]

                if nested in pointers:
                    node.pointers = pointers[nested]
                    del pointers[nested]
                
                child_group[nested] = child_group.get(nested, [])
                child_group[nested].append(node)
                if nested in nested_levels:
                    del nested_levels[nested]
                nested -= 1

            elif symbols[position]['type'] == 'EOB':
                # handle closing of buffer
                nested_levels[nested].append([last_position, position])
                root_node = self.add_node(
                    nested_levels[nested],
                    nested,
                    unstripped_contents,
                    root=True,
                    start_position=start_position)

                #TODO refactor?
                if nested + 1 in child_group:
                    for child in child_group[nested+1]:
                        child.parent = root_node
                    root_node.children = child_group[nested+1]
                    del child_group[nested + 1]

                if nested in pointers:
                    root_node.pointers = pointers[nested]
                    del pointers[nested]

                child_group[nested] = child_group.get(nested, [])
                child_group[nested].append(root_node)
                if nested in nested_levels:
                    del nested_levels[nested]
                nested -= 1
                continue

            last_position = position
        
        if nested >= 0:
            contents = ''.join([contents[:position],
                ' ',
                syntax.node_closing_wrapper,
                ' ',
                contents[position:]])
            return self.set_buffer_contents(contents)

        for node in self.nodes:
            node.filename = self.filename
            node.file = self

        for match in self.meta_to_node:
            # TODO optimize
            for node in self.nodes:
                for r in node.ranges:
                    if match.span()[1] in r:
                        node.is_meta = True
                        node.meta_key = match.group()[:-3]

        return nested_levels, child_group, nested

    def add_node(self, ranges, nested, contents, root=None, start_position=0):

        # Build the node contents and construct the node
        node_contents = ''.join([
            contents[r[0] - start_position:r[1] - start_position ] for r in ranges])

        new_node = self.urtext_node(node_contents, self.project, root=root, nested=nested)
        new_node.ranges = ranges
        new_node.start_position = ranges[0][0]
        new_node.end_position = ranges[-1][1]

        self.nodes.append(new_node)
        if new_node.is_root_node:
            self.root_node = new_node
        return new_node

    def _get_contents(self):
        buffer_setting = self.project.get_single_setting('use_buffer')
        if buffer_setting and buffer_setting.true():
            return self.project.run_editor_method('get_buffer', self.filename)
        return self.contents

    def set_buffer_contents(self, new_contents):
        self.contents = new_contents
        self._lex_and_parse()

    def write_buffer_contents(self, run_hook=None):
        self.project.run_editor_method(
            'set_buffer',
            self.filename,
            self.contents,
            identifier=self.identifier)

    def resolve_nodes(self, messages=None):
        unresolved_nodes = [n for n in self.nodes if n.needs_resolution]
        for node in unresolved_nodes:
            if not node.resolve_id(existing_nodes=[n for n in self.nodes if n != node]):
                return False

    def _check_untitled_nodes(self):        
        for node in [n for n in self.nodes if n.title == '(untitled)']:
            node.needs_resolution = True

    def _check_duplicate_ids(self):
        allocated_ids = [n.id for n in self.nodes]
        for node in [n for n in self.nodes if allocated_ids.count(n.id) > 1]:
            node.needs_resolution = True

    def get_ordered_nodes(self):
        return sorted( 
            list(self.nodes),
            key=lambda node : node.start_position)

    def _assign_parents(self, start_node):
        for child in start_node.children:
            child.parent = start_node
            self._assign_parents(child)

    def get_node_from_position(self, position):
        for node in self.nodes:
            for r in node.ranges:       
                if position in range(r[0],r[1]+1): # +1 in case the cursor is in the last position of the node.
                    return node

    def node_ids(self):
        return [n.id for n in self.nodes]

    def get_node(self, node_id):
        for n in self.nodes:
            if n.id == node_id:
                return n
