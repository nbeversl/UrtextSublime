from urtext.timestamp import UrtextTimestamp
import urtext.syntax as syntax
import urtext.utils as utils
import os

class MetadataValue:

    def __init__(self, project):
        self.timestamp = None
        self.project = project
        self.node_as_value = False
        self.text_lower = None
        self.text = None
        self.unparsed_text = None
        
    def set_as_node(self, node):
        self.node_as_value = node

    def set_from_text(self, value_string):
        self.unparsed_text = value_string
        for ts in syntax.timestamp_c.finditer(value_string):
            dt_string = ts.group(0).strip()
            value_string = value_string.replace(dt_string, '').strip()
            t = UrtextTimestamp(
                dt_string[1:-1],
                start_position=ts.start())
            if t.datetime:
                self.timestamp = t
        self.text = value_string
        self.text_lower = value_string.lower()

    def num(self):
        try:
            return float(self.text)
        except:
            return float('inf')

    def links(self):
        urtext_links, replaced_contents = utils.get_all_links_from_string(self.text, self.node, self.project.project_list)
        for urtext_link in urtext_links:
            if urtext_link.is_file:
                urtext_link.path = os.path.join(
                    os.path.dirname(self.entry.node.filename),
                    urtext_link.path)
        return urtext_links

    def node(self):
        if self.node_as_value:
            return self.node_as_value
        for l in self.links():
            if l.is_node:
                node = self.entry.node.project.get_node(l.node_id)
                if node: return node
        return False

    def __lt__(self, other):
        if self.text:
            return self.text < other.text
        return self.num() < other.num()

    def true(self):
        if self.text:
            if self.text.lower() in [
                'yes', 'true', 'y', 'on']:
                return True
        return False

    def log(self):
        print('text: %s' % ( 
            self.text if self.text else '' ))
        print('timestamp: %s' % (
            self.timestamp.unwrapped_string if self.timestamp else ''))
        print('-')