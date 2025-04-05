import re
from urtext.metadata import NodeMetadata
from urtext.frame import UrtextFrame
import urtext.utils as utils
import urtext.syntax as syntax

class UrtextNode:

    urtext_metadata = NodeMetadata

    def __init__(self, 
        contents,
        project,
        root=False,
        nested=None):

        self.project = project
        self.ranges = []
        self.is_tree = False
        self.is_node = True
        self.is_meta = False
        self.meta_key = None
        self.export_points = {}
        self.marked_dynamic = False
        self.is_dynamic = False
        self.id = None
        self.needs_resolution = False
        self.pointers = []
        self.display_detail = ''
        self.links = []
        self.is_root_node = root
        self.frames = []
        self.target_nodes = []
        self.untitled = False
        self.title_only = False
        self.title = ''
        self.parent = None
        self.children = []
        self.first_line_title = False
        self.title_from_marker = False
        self.nested = nested
        self.resolution = None
        self.filename = None
        self.embedded_syntax_ranges = []
        self.frame_ranges = []
        
        ranges, stripped_contents = utils.strip_backtick_escape(contents)
        self.embedded_syntax_ranges.extend(ranges)
        stripped_contents = utils.strip_whitespace_anchors(stripped_contents)
        self.full_contents = stripped_contents

        ranges, stripped_contents, replaced_contents = utils.strip_embedded_syntaxes(stripped_contents)
        self.embedded_syntax_ranges.extend(ranges)

        replaced_contents, _, self.marked_dynamic = check_dynamic_marker(replaced_contents)
        self._get_links(replaced_contents)
        self.frame_ranges, stripped_contents, replaced_contents = self.parse_frames(replaced_contents)
        self.metadata = self.urtext_metadata(self, self.project)        
        stripped_contents, replaced_contents = self.metadata.parse_contents(replaced_contents)
        self.replaced_contents = replaced_contents
        for link in self.links:
            stripped_contents = stripped_contents.replace(link.matching_string, '', 1)        
        self.title = self.set_title(stripped_contents)
        if not stripped_contents.strip().replace(self.title,'').replace(' _',''):
            self.title_only = True
        self.id = self.title
        for d in self.frames:
            d.source_node = self
        for entry in self.metadata.entries():
            entry.from_node = self
        self.stripped_contents = stripped_contents   
        self.text = utils.make_node_link(self.id)

    def get_file_position(self, node_position): 
        node_length = 0
        offset_position = node_position
        for r in self.ranges:
            range_length = r[1] - r[0]
            node_length += range_length
            if node_position <= node_length:
                return r[0] + offset_position
            offset_position -= range_length

    def get_date(self, date_keyword):
        return self.metadata.get_date(date_keyword)

    def contents(self,
        stripped=True,
        strip_dynamic_marker=False,
        strip_first_line_title=False):

        if stripped:
            contents = self.stripped_contents
        else:
            contents = self.full_contents

        if strip_dynamic_marker:
            contents = utils.strip_dynamic_markers(contents)

        if strip_first_line_title:
            contents = self.strip_first_line_title(contents)

        return contents

    def contents_with_contained_nodes(self):
        buffer_contents = self.buffer.contents
        return buffer_contents[self.start_position:self.end_position]

    def links_ids(self):
        return [link.node_id for link in self.links]

    def resolve_id(self, existing_nodes=[]):
        if self.resolution:
            return self.id
        newest_timestamp = self.metadata.get_newest_timestamp()
        existing_ids = [n.id for n in existing_nodes]
        if newest_timestamp:
            resolved_id = ''.join([
                self.title,
                syntax.resolution_identifier,
                newest_timestamp.unwrapped_string, 
                ])
            if resolved_id not in existing_ids:
                self.resolution = newest_timestamp.unwrapped_string
                self.id = resolved_id
                return self.id

        if self.is_meta:
            resolved_id = ''.join([
                self.title,
                syntax.resolution_identifier,
                self.meta_key
            ])
            if resolved_id not in existing_ids:
                self.resolution = self.meta_key
                self.id = resolved_id
                return self.id
        # try resolving to parent title
        if self.parent and self.parent.title != '(untitled)':
            resolved_id = ''.join([
                self.title,
                syntax.resolution_identifier,
                self.parent.title])
            if resolved_id not in existing_ids:
                self.resolution = self.parent.title
                self.id = resolved_id
                return self.id
        existing_resolutions = [n.resolution for n in existing_nodes if n.resolution]
        inline_timestamps = self.metadata.get_values('_inline_timestamp')
        existing_resolutions.extend([t.timestamp.unwrapped_string for t in inline_timestamps])
        timestamp = self.project.timestamp(ensure_unique=True, existing_resolutions=existing_resolutions)
        contents, marker, _ = check_dynamic_marker(self.contents_with_contained_nodes())
        self._set_contents(''.join([
            marker, ' ', timestamp.wrapped_string, ' ', contents]),
            preserve_title=False)
        self.buffer.write_buffer_contents(re_parse=False)
        return False

    def _get_links(self, positioned_contents):
        urtext_links, replaced_contents = utils.get_all_links_from_string(positioned_contents, self, self.project.project_list)
        for urtext_link in urtext_links:
            urtext_link.containing_node = self
            self.links.append(urtext_link)

    def set_title(self, contents):
        """
        - `title` metadata key overrides any _ marker.
        - Then the first ` _` marker overrides any subsequent one.
            - If it is on the first line, 
            we need to remember this for dynamic nodes.
        - if nothing else found, title is the first non-blank line
        """
        t = self.metadata.get_first_value('title')
        if t:
            return t.text

        first_non_blank_line = None
        contents_lines = contents.strip().split('\n')
        for line in contents_lines:
            first_non_blank_line = line.strip()
            first_non_blank_line = utils.strip_nested_links(first_non_blank_line).strip()
            if first_non_blank_line and first_non_blank_line not in ['_', '~']:
                break
        title = syntax.node_title_c.search(contents)
        if title:
            title = title.group().strip()
            title = title.strip(syntax.title_marker).strip()
        if title:
            self.title_from_marker = True
            if title in first_non_blank_line:
                self.first_line_title = True 
        elif first_non_blank_line:
            title = first_non_blank_line
            for character in syntax.disallowed_title_characters:
                title = re.sub(character, ' ', title)
            self.first_line_title = True
        if not title:
            title = '(untitled)'
            self.untitled = True
        if len(title) > 255:
            title = title[:255].strip()
        title = title.strip()
        self.metadata.add_entry('title', title, self)
        return title
   
    def log(self):
        print(self.id)
        print(self.filename)
        self.metadata.log()

    def bound_action(self, action_string):
        # this does not work as hoped
        self.project.project_list.run_action(action_string)

    def consolidate_metadata(self, separator='::'):
        
        keynames = {}
        for entry in self.metadata.entries():
            if entry.keyname in [
                '_newest_timestamp',
                '_oldest_timestamp', 
                '_inline_timestamp']:
                continue
            if entry.keyname not in keynames:
                keynames[entry.keyname] = []
            keynames[entry.keyname] = [v.unparsed_text for v in entry.meta_values]

        return self.build_metadata(keynames, separator=separator)

    @classmethod
    def build_metadata(self, 
        metadata, 
        separator=syntax.metadata_assignment_operator):

        if not metadata:
            return ''

        line_separator = '\n'
        new_metadata = ''

        for keyname in metadata:
            new_metadata += keyname + separator
            if isinstance(metadata[keyname], list):
                new_metadata += ' - '.join(metadata[keyname])
            else:
                new_metadata += str(metadata[keyname])
            new_metadata += line_separator
        return new_metadata.strip()

    def _set_contents(self, new_contents, preserve_title=True):
        """
        use project._set_node_contents() method instead of using this directly.

        file should be parsed before this, in case the content
        has been modified manually by a call
        """
        if preserve_title and self.first_line_title:
            new_node_contents = ''.join([ 
                self.title,
                syntax.title_marker,
                '\n',
                new_contents,
                ])
        else:
            new_node_contents = new_contents
        buffer_contents = self.buffer._get_contents()
        new_buffer_contents = ''.join([
            buffer_contents[:self.start_position],
            new_node_contents,
            buffer_contents[self.end_position:]])
        self.buffer.set_buffer_contents(new_buffer_contents)
        # re-parses within buffer but does not re-parse into project

    def replace_range(self, 
        range_to_replace, 
        replacement_contents):

        self.project._parse_file(self.filename)
        file_contents = self.file._get_contents()
        file_range_to_replace = [
            self.get_file_position(range_to_replace[0]),
            self.get_file_position(range_to_replace[1])]

        new_file_contents = ''.join([
            file_contents[0:file_range_to_replace[0]],
            replacement_contents,
            file_contents[file_range_to_replace[1]:]])
        self.file.set_buffer_contents(new_file_contents)

    def parse_frames(self, contents): 
        frame_ranges = []
        stripped_contents = contents
        replaced_contents = contents
        for d in syntax.frame_c.finditer(contents):
            frame_ranges.append([d.start(),d.end()])
            param_string = d.group(0)[2:-2]
            self.frames.append(
                UrtextFrame(
                    param_string, 
                    self.project, 
                    d.start(),
                    d.end()))
            stripped_contents = stripped_contents.replace(
                d.group(), 
                ' '*len(d.group()), 
                1)
            replaced_contents = replaced_contents.replace(
                d.group(), 
                '', 
                1)

        return frame_ranges, stripped_contents, replaced_contents

    def strip_first_line_title(self, contents):
        if self.first_line_title:
            contents = contents.replace(self.title,'',1)
        if self.title_from_marker:
            contents = contents.replace(syntax.title_marker,'',1)
        return contents

    def ancestors(self):
        return node_ancestors(self)

    def descendants(self):
        return node_descendants(self)

    def siblings(self):
        if self.parent:
            return [n for n in self.parent.children if n.id != self.id]
        return []

    def get_sibling(self, node_title):
        for n in self.siblings():
            if n.title == node_title:
                return n

    def get_child(self, node_title):
        for c in self.children:
            if c.title == node_title:
                return c

    def replace_links(self, original_id, new_id='', new_project=''):
        if self.is_dynamic:
            return
        if not new_id and not new_project:
            return None
        if not new_id:
            new_id = original_id
        pattern_to_replace = re.escape(utils.make_node_link(original_id))
        if new_id:
            replacement = utils.make_node_link(new_id)
        if new_project:
            replacement = replacement = utils.make_project_link(new_project) + replacement
        new_contents = self.contents(stripped=False)
        for link in re.finditer(pattern_to_replace, new_contents):
            new_contents = new_contents.replace(link.group(), replacement, 1)
        self._set_contents(new_contents)

    def link(self, include_project=False, position=0):
        project_link = ''
        if include_project:
            project_link = utils.make_project_link(self.project.title())
        return ''.join([
            project_link,
            utils.make_node_link(self.id, position=position)])

    def pointer(self):
        return utils.make_node_pointer(self.id)

    def ranges_with_embedded_syntaxes(self):
        ranges_with_embedded_syntaxes = {}
        for r in self.ranges:
            for embedded in self.embedded_syntax_ranges:                
                if embedded[0] in range(r[0],r[1]):
                    ranges_with_embedded_syntaxes[r[0]] = {
                        'start' : r[0],
                        'kind': 'urtext',
                        'end' : embedded[0]}
                    ranges_with_embedded_syntaxes[embedded[0]] = {
                        'start' : embedded[0],
                        'kind': 'embedded',
                        'end' : embedded[1]}
                    ranges_with_embedded_syntaxes[embedded[1]] = {
                        'start' : embedded[1],
                        'kind': 'urtext',
                        'end' : r[1]}
            if r[0] not in ranges_with_embedded_syntaxes:
                ranges_with_embedded_syntaxes[r[0]] = {
                    'start' : r[0],
                    'starts_node' : r == self.ranges[0],
                    'ends_node' : r == self.ranges[-1],
                    'kind': 'urtext',
                    'end' : r[1]}

        return ranges_with_embedded_syntaxes

    def append_child_node(self, contents, kind='bracket'):
        full_contents = self.contents_with_contained_nodes()
        self.project._set_node_contents(
            self.id,
            ''.join([
                full_contents,
                syntax.node_opening_wrapper,
                ' ',
                contents, ' \n',
                syntax.node_closing_wrapper, '\n',
                ]))

    def lines(self, strip_dynamic_marker=False):
        return self.contents(stripped=False, strip_dynamic_marker=strip_dynamic_marker).split('\n')

    def line_from_pos(self, position):
        length = 0
        for index, l in enumerate(self.lines()):
            length += len(l)
            if position < length:
                return index
        return index # temporary fallback

    def dynamic_output(self, m_format):
        m_format = m_format.replace('$title', self.title)
        m_format = m_format.replace('$_link', self.link())
        m_format = m_format.replace('$_pointer', self.pointer()) 
        m_format = m_format.replace('$_meta', self.metadata.dynamic_output(m_format))

        contents_syntax = re.compile(r'\$_contents(:\d*)?', flags=re.DOTALL)      
        contents_match = re.search(contents_syntax, m_format)
        if contents_match:
            contents = self.contents(strip_dynamic_marker=True)
            suffix = ''
            if contents_match.group(1):
                suffix = contents_match.group(1)
                length_str = suffix[1:]
                length = int(length_str)
                if len(contents) > length:
                    contents = contents[0:length] + ' (...)'
            m_format = m_format.replace(''.join(['$_contents',suffix]), ''.join([ contents, '\n']))

        for match in re.finditer(r'(\$_lines:)(\d{1,9})(,\d{1,9})?', m_format):
            lines = self.lines(strip_dynamic_marker=True)
            if match.group(3):
                first_line = int(match.group(2))
                last_line = int(match.group(3))
            else:
                first_line = 0
                last_line = int(match.group(2))
            if first_line - 1 > len(lines): first_line = len(lines) - 1
            if last_line - 1 > len(lines): last_line = len(lines) 
            m_format = m_format.replace(match.group(), '\n'.join(lines[first_line:last_line+1]))

        other_format_keys = re.findall(r'\$[\.A-Za-z0-9_-]+', m_format)
        for match in other_format_keys:
            meta_key = match.lstrip('$')
            values = self.metadata.get_extended_values(meta_key)
            m_format = m_format.replace(match, values)
        m_format = m_format.replace(r'\n', '\n')
        return m_format

def node_descendants(node, known_descendants=[]):
    # differentiate between pointer and "real" descendants
    all_descendants = [n for n in node.children if n not in known_descendants]
    for descendant in all_descendants:
        all_descendants.extend(
            node_descendants(descendant, known_descendants=all_descendants))
    return all_descendants

def node_ancestors(node, known_ancestors=[]):
    # differentiate between pointer and "real" descendants
    if node.parent:
        known_ancestors.append(node.parent)
        return node_ancestors(node.parent, known_ancestors)
    return known_ancestors

def check_dynamic_marker(text):
    marked_dynamic = False
    marker = ''
    text = text.lstrip()
    while True:
        text = text.lstrip()
        if not len(text):
            break
        if text[0] == syntax.dynamic_marker:
            marked_dynamic = True
            marker = syntax.dynamic_marker
            text = text[1:]
            if len(text) and text[0] == syntax.missing_frame_marker:
                marker += syntax.missing_frame_marker
                text = text[1:]
                break
        else:
            break
    return text, marker, marked_dynamic

