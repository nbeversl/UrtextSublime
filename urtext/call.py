import urtext.syntax as syntax
from urtext.utils import force_list, get_id_from_link
import urtext.utils as utils
from anytree import Node, RenderTree, PreOrderIter
from anytree.render import ContStyle
from urtext.timestamp import UrtextTimestamp

class UrtextCall:

    syntax = syntax
    utils = utils
    name = []
    Node = Node
    RenderTree = RenderTree
    PreOrderIter = PreOrderIter
    UrtextTimestamp = UrtextTimestamp
    project_instance = False
    project_list_instance = False
    is_manual = False
    
    def __init__(self, project_or_project_list):
        self.keys_with_flags = []
        self.flags = []
        self.links = []
        self.params = []
        self.arguments = []
        self.params_dict = {}
        if self.project_list_instance:
            self.project_list = project_or_project_list
        else:
            self.project = project_or_project_list
            self.project_list = self.project.project_list

        self.argument_string = None
        self.frame = None

    def add_doc_name(self):
        for n in list(self.names):
            self.names.append(n+'_DOC')

    def run(self, *args, **kwargs):
        pass

    def trigger(self, *args, **kwargs):
        self.run(*args, **kwargs)

    def on_added(self):
        pass

    def on_node_visited(self, project, node_id):
        pass
        
    def _dynamic_output(self, input_contents):
        # here capture whether the end is DOCS and write the doc
        pass
    
    def dynamic_output(self, input_contents):
        return False

    def parse_argument_string(self, argument_string):
        self.argument_string = argument_string.strip()
        argument_string = self._parse_links(argument_string)
        arguments = self.syntax.metadata_arg_delimiter_c.split(argument_string)     
        for arg in arguments:
            arg = arg.strip()
            key_op_value = syntax.call_key_op_value_c.match(arg)          
            if key_op_value:
                key = key_op_value.group(1)
                op = key_op_value.group(2)
                value = key_op_value.group(3)
                self.params.append((key,value,op))
                continue

            key_with_opt_flags = syntax.call_key_with_opt_flags.match(arg)
            if key_with_opt_flags:
                key = key_with_opt_flags.group(1).strip()
                flags = []
                #TODO works, could be improved:
                if len(key_with_opt_flags.groups()) > 1:
                    flags = key_with_opt_flags.group().replace(key,'',1).split(' ')
                    flags = [f.strip() for f in flags if f]
                self.keys_with_flags.append((key, flags))
                continue

            flags = syntax.call_flags_c.match(arg)
            if flags:
                flags = flags.group().split(' ')
                flags = [f.strip() for f in flags if f]
                self.flags.extend(flags)
                continue
            
            hash_value = syntax.call_hash_meta_c.match(arg)
            if hash_value:
                hash_value = hash_value.group()[1:]
                self.params.append((
                    self.project.get_single_setting('hash_key').text,
                    hash_value,
                    '='))
                continue

            self.arguments.append(arg.strip())

        for param in self.params:

            self.params_dict[param[0]] = self.params_dict.get(param[0], [])
            self.params_dict[param[0]].extend(param[1:])
        
    def _parse_links(self, argument_string):
        self.links, remaining_contents = self.utils.get_all_links_from_string(
            argument_string,
            self.frame.source_node,
            self)
        return remaining_contents

    def get_param(self, keyname):
        if keyname in self.params_dict:
            return self.params_dict[keyname][0] if self.params_dict[keyname][1] == '=' else None

    def have_flags(self, flags):
        for f in force_list(flags):
            if f in self.flags:
                return True
        return False

    def check_param(self, keyname, operator, value):
        if keyname in self.params_dict:
            if self.params_dict[keyname] == (keyname, value, operator):
                return True
        return False

    def should_continue(self):
        return True

    def on_added(self):
        pass

    def default_output(self):
        return ''

    def have_keys(self, keys):
        #TODO disambiguate "keys" from params dict keys
        #(terminology)
        keys = force_list(keys)
        for f in keys:
            if f in [k[0] for k in self.params_dict.keys()]:
                return True
        return False