from urtext.timestamp import UrtextTimestamp, default_date
import urtext.syntax as syntax
from urtext.metadata_entry import MetadataEntry
import urtext.utils as utils

class NodeMetadata:

    def __init__(self, 
        node,
        project):

        self.node = node
        self.entries_dict = {}
        self.project = project
   
    def parse_contents(self, full_contents):
        parsed_contents = full_contents
        remaining_contents = full_contents

        for m in syntax.metadata_entry_c.finditer(full_contents):
            keyname, contents = m.group().strip(syntax.metadata_end_marker).split(syntax.metadata_assigner, 1)
            value_list = []
            for pattern in syntax.special_metadata_patterns_c.finditer(contents):
                value_list.append(pattern.group())
                contents = contents.replace(pattern.group(),'')
            value_list.extend(syntax.metadata_separator_pattern_c.split(contents))       
            value_list = [v.strip() for v in value_list if v.strip()]
            tag_self, tag_children, tag_descendants, keyname = determine_desc_tagging(keyname)

            self.add_entry(
                keyname,
                value_list,
                self.node,
                tag_self=tag_self,
                tag_children=tag_children,
                tag_descendants=tag_descendants,
                start_position=m.start(),
                end_position=m.start() + len(m.group().strip()))

            parsed_contents = parsed_contents.replace(m.group(), ' '*len(m.group()), 1)
            remaining_contents = remaining_contents.replace(m.group(), '', 1)

        for m in syntax.hash_meta_c.finditer(parsed_contents):
            tag_self=False
            tag_children=False
            tag_descendants=False
            
            entry = m.group().strip()
            tag_self, tag_children, tag_descendants, entry = determine_desc_tagging(entry)
            value = entry.strip().replace('-',' ')
            value = value[1:]

            keyname = '#'
            if self.project.compiled:
                hash_key_setting = self.project.get_single_setting('hash_key')
                if hash_key_setting:
                    keyname = hash_key_setting.text

            self.add_entry(
                keyname,
                value,
                self.node,
                tag_self=tag_self,
                tag_children=tag_children,
                tag_descendants=tag_descendants,
                start_position=m.start(), 
                end_position=m.start() + len(m.group()))
            
            parsed_contents = parsed_contents.replace(m.group(), ' '*len(m.group()), 1)
            remaining_contents = remaining_contents.replace(m.group(), '', 1)

        # inline timestamps:
        for m in syntax.timestamp_c.finditer(parsed_contents):
            self.add_entry(
                '_inline_timestamp',
                m.group(),
                self.node,
                start_position=m.start(),
                end_position=m.start() + len(m.group()))
            parsed_contents = parsed_contents.replace(m.group(), ' '*len(m.group()), 1)
            remaining_contents = remaining_contents.replace(m.group(), '', 1)

        #remove from contents entries without or entries that are nodes:
        for m in syntax.metadata_key_only_c.finditer(parsed_contents):
            parsed_contents = parsed_contents.replace(m.group(), ' '*len(m.group()), 1)
            remaining_contents = remaining_contents.replace(m.group(), '', 1)

        for m in syntax.bold_text_c.finditer(parsed_contents):
            self.add_entry(
                '_bold',
                m.group(),
                self.node,
                start_position=m.start(),
                end_position=m.start() + len(m.group()))
            parsed_contents = parsed_contents.replace(m.group(), ' '*len(m.group()), 1)
            remaining_contents = remaining_contents.replace(m.group(), '', 1)

        for m in syntax.italic_text_c.finditer(parsed_contents):
            self.add_entry(
                '_italic',
                m.group(),
                self.node,
                start_position=m.start(),
                end_position=m.start() + len(m.group()))
            parsed_contents = parsed_contents.replace(m.group(), ' '*len(m.group()), 1)
            remaining_contents = remaining_contents.replace(m.group(), '', 1)

        self.add_system_keys()
        return remaining_contents, parsed_contents

    def add_entry(self, 
        key,
        values,
        node,
        start_position=0,
        end_position=0,
        tag_self=True,
        from_node=None,
        tag_children=False,
        tag_descendants=False):

        if not isinstance(values, list):
            values = [values]

        key = key.lower().strip()
        e = MetadataEntry(
            key, 
            values,
            node,
            start_position=start_position, 
            end_position=end_position,
            from_node=from_node,
            tag_self=tag_self,
            tag_children=tag_children,
            tag_descendants=tag_descendants)

        self.entries_dict[key] = self.entries_dict.get(key, [])        
        self.entries_dict[key].append(e)

    def get_keys(self, exclude=[]):
        keys = {}
        for k in self.entries_dict.keys():
            keys[k] = len(self.entries_dict[k])
        return keys

    def get_entries(self, keyname):
        keyname = keyname.lower()
        if keyname not in self.entries_dict:
            return []
        return [e for e in self.entries_dict[keyname] if e.tag_self]

    def entries(self):
        all_entries = []
        for k in self.entries_dict:
            all_entries.extend(self.entries_dict[k])
        return all_entries

    def add_system_keys(self):
        inline_timestamp_entries = self.get_entries('_inline_timestamp')
        if inline_timestamp_entries:
            inline_timestamps = sorted(
                inline_timestamp_entries,
                key=lambda t: t.meta_values[0].timestamp)
            self.add_entry(
                '_oldest_timestamp', 
                inline_timestamps[0].meta_values[0].timestamp.wrapped_string,
                self.node,
                start_position=inline_timestamps[0].start_position,
                end_position=inline_timestamps[0].end_position)
            self.add_entry(
                '_newest_timestamp',
                inline_timestamps[-1].meta_values[0].timestamp.wrapped_string,
                self.node,
                start_position=inline_timestamps[-1].start_position,
                end_position=inline_timestamps[-1].end_position)

    def get_first_value(self, keyname, order_by='default'):
        values = self.get_values(keyname, order_by=order_by)
        if values:
            return values[0]

    def get_values_with_frequency(self, keyname):

        # TODO FIX

        values = {}
        entries = self.get_entries(keyname)

        for e in entries:
            for v in e.meta_values:
                node_as_value = v.node()
                if node_as_value:
                    link_as_value = node_as_value.link()
                    values[link_as_value] = values.get(link_as_value,0)
                    values[link_as_value] += 1
                    continue                 
                values[v] = values.get(v, 0)
                values[v] +=1
        return values

    def get_values(self, keyname, order_by=None):

        values = []
        entries = self.get_entries(keyname)

        for e in entries:
            values.extend(e.meta_values)

        if order_by in ['-pos','-position']:
            return sorted(
                list(values),
                key = lambda v: v.entry.start_position)

        if order_by == 'default':
            return sorted(list(values))

        return list(values)

    def get_extended_values(self, extended_key):
        """
        from an optionally extended key, returns the value(s) as a formatted string
        """
        if '.' not in extended_key:
            extended_keyname = [extended_key]
        else:
            extended_keyname = extended_key.split('.')
        values = get_extended_metadata(extended_keyname, self.node)        
        values = list(set(values))
        return syntax.metadata_separator_syntax.join(values)

    def get_matching_entries(self, keyname, value):
        entries = self.get_entries(keyname)
        if value == '*':
            return entries
        matching_entries = []
        if entries:
            for e in entries:
                if isinstance(value, UrtextTimestamp):
                    meta_values = [v.timestamp for v in e.meta_values]
                else:
                    meta_values = [v.text for v in e.meta_values]
                for v in meta_values:
                    if v == value:
                        matching_entries.append(e)
        return matching_entries

    def get_date(self, keyname):
        """
        Returns the timestamp of the FIRST matching metadata entry with the given key.
        #TODO possibly remove
        """
        value = self.get_first_value(keyname)
        if value:
            return value.timestamp
        return default_date
      
    def clear_from_source(self, source_node):
        for k in self.entries_dict:
            for entry in self.entries_dict[k]:
                if entry.from_node == source_node:
                    self.entries_dict[k].remove(entry)
    
    def convert_hash_keys(self):
        hash_key_setting = self.project.get_single_setting('hash_key')
        if hash_key_setting:
            hash_key_setting = hash_key_setting.text
            if '#' in self.entries_dict:
                for entry in self.get_entries('#'):
                    entry.keyname = hash_key_setting
                self.entries_dict.setdefault(hash_key_setting, [])                
                self.entries_dict[hash_key_setting].extend(self.entries_dict['#'])
                del self.entries_dict['#']

    def get_oldest_timestamp(self):
        value = self.get_first_value('_oldest_timestamp')
        if value:
            return value.timestamp

    def get_newest_timestamp(self):
        value = self.get_first_value('_newest_timestamp')
        if value:
            return value.timestamp                    

    def log(self):
        for entry in self.entries():
            entry.log()

    def dynamic_output(self, m_format):
        return ''

def determine_desc_tagging(string):
    tag_self=False
    tag_children=False
    tag_descendants=False
    
    if not syntax.metadata_tag_self_c.match(string[0]) and ( 
        not syntax.metadata_tag_desc_c.match(string[0])):
        tag_self=True
    else:
        if syntax.metadata_tag_self_c.match(string[0]):
            tag_self = True
            string = string[1:]
        if syntax.metadata_tag_desc_c.match(string[0]):
            tag_children = True
            string = string[1:]
        if syntax.metadata_tag_desc_c.match(string[0]):
            tag_descendants = True
            string = string[1:]

    return tag_self, tag_children, tag_descendants, string

def get_extended_metadata(extended_keyname, node):
    if len(extended_keyname) == 0: return []
    entries = node.metadata.get_entries(extended_keyname[0])
    values = []
    use_timestamp_setting = node.project.get_setting_as_text('use_timestamp')
    for e in entries:
        for v in e.meta_values:
            if v.node():
                if len(extended_keyname) == 1:
                    values.append(v.node().link())
                elif len(extended_keyname) > 1:
                    values.append(v.node().dynamic_output('$'+'.'.join(extended_keyname[1:])))
                continue
            elif len(extended_keyname) == 1:
                if extended_keyname[0] in use_timestamp_setting and v.timestamp:
                    values.append(v.timestamp.unwrapped_string)
                else:
                    values.append(v.text)
                continue
            elif len(extended_keyname) == 2 and extended_keyname[1] in ['timestamp','timestamps'] and v.timestamp:
                values.append(v.timestamp.unwrapped_string) 
                continue
    return values
