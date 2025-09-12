import re
import sys
import traceback
from io import StringIO
from urtext.utils import force_list, get_id_from_link, make_node_link
from urtext.file import UrtextFile, UrtextBuffer
from urtext.node import UrtextNode
from urtext.timestamp import UrtextTimestamp
from urtext.call import UrtextCall
import urtext.syntax as syntax

python_code_regex = re.compile(r'(%%Python)(.*?)(%%)', re.DOTALL)

class Exec:
    name = ["EXEC"]

    def dynamic_output(self, text_contents):
        target_is_self = False
        for target in self.frame.targets:
            if target.matching_string  == '@self':
                target_is_self = True
        if self.argument_string.strip() == '@self':
            node_to_exec = self.frame.source_node
            contents = self.frame.source_node.full_contents
        else:
            node_to_exec = self.project.get_node(get_id_from_link(self.argument_string))
            if node_to_exec:
                contents = node_to_exec.full_contents
            else: return text_contents + make_node_link(get_id_from_link(self.argument_string)) + ' : not found\n'
    
        python_embed = python_code_regex.search(contents)
        if python_embed:
            python_code = python_embed.group(2)
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            locals_parameter = {
                'ThisProject': self.project,
                'UrtextFile': UrtextFile,
                'UrtextBuffer': UrtextBuffer,
                'UrtextNode': UrtextNode,
                'UrtextTimestamp': UrtextTimestamp,
                'UrtextCall': UrtextCall,
                'UrtextSyntax': syntax,
                'ProjectList': self.project.project_list,
            }
            try:
                self.project.last_exec_node = node_to_exec
                exec(python_code, {}, locals_parameter)
                sys.stdout = old_stdout
                message = mystdout.getvalue()
                return_contents = text_contents + message 
                if target_is_self:
                    return_contents = python_embed.group() + '\n' + return_contents
                return return_contents
            except Exception as e:
                sys.stdout = old_stdout
                return text_contents + ''.join([
                    '\n',
                    '`',
                    'error in | ',
                    node_to_exec,
                    ' >',
                    ' ',
                    traceback.format_exc(),
                    '`'                    
                ])
        return text_contents + node_to_exec.link() + ' : no Python code found\n'
        
