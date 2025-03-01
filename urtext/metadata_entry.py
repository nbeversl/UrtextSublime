from urtext.metadata_value import MetadataValue
import urtext.syntax as syntax
import urtext.utils as utils
import re

class MetadataEntry:  # container for a single metadata entry

    def __init__(self, 
        keyname, 
        values,
        node,
        start_position=None,
        end_position=None, 
        tag_self=False,
        tag_children=False,
        tag_descendants=False,
        from_node=None):

        self.node = node
        self.keyname = keyname
        self.tag_self = tag_self
        self.tag_children = tag_children
        self.tag_descendants = tag_descendants
        self.from_node = from_node
        self.start_position = start_position
        self.end_position = end_position
        self.meta_values = []
        for v in values:
            value = MetadataValue(self.node.project)
            if isinstance(v, str):
                value.set_from_text(v)
            else:
                value.set_as_node(v)
            value.entry = self
            self.meta_values.append(value)          
   
    def text_values(self):
        return [v.text for v in self.meta_values if v.text]

    def values_with_timestamps(self, lower=False):
        return [(v.text if not lower else v.text_lower, v.timestamp) for v in self.meta_values]

    def dynamic_output(self, m_format):
        m_format = m_format.replace('$title', self.node.title)
        m_format = m_format.replace('$_keyname', self.keyname)
        m_format = m_format.replace('$_entry', self.keyname + ' :: ' + ' - '.join([v.text for v in self.meta_values]))
        m_format = m_format.replace('$_value', ' - '.join([v.text for v in self.meta_values]))
        m_format = m_format.replace('$_link', self.node.link(position=self.start_position))
        m_format = m_format.replace('$_pointer', self.node.pointer())
        for match in re.finditer(r'(\$_lines:)(-?\d{1,9}),(-?\d{1,9})', m_format):
            lines = self.node.lines()
            entry_pos = self.node.line_from_pos(self.start_position)
            first_line = entry_pos + int(match.group(2))
            last_line = entry_pos + int(match.group(3))
            if first_line < 0: first_line = 0
            if last_line - 1> len(lines): last_line = len(lines)
            context = '\n'.join(self.node.lines()[first_line:last_line+1])
            m_format = m_format.replace(match.group(), context)
        m_format = m_format.replace('$_line', self.node.lines()[self.node.line_from_pos(self.start_position)])
        m_format = m_format.replace(r'\n', '\n')
        return m_format

    def log(self):
        print('key: %s' % self.keyname)
        print(self.start_position, self.end_position)
        if self.from_node:
            print('from_node: %s' % self.from_node.id)
        print('tag children: %s' % self.tag_children)
        print('tag descendats: %s' % self.tag_descendants)
        for value in self.meta_values:
            value.log()
        print('-------------------------')
