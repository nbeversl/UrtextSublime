from urtext.utils import get_id_from_link, get_all_targets_from_string
import urtext.syntax as syntax
import traceback
import datetime

class UrtextFrame:

    def __init__(self, param_string, project, start_position, end_position):

        self.position = start_position
        self.end_position = end_position
        self.contents = None
        self.targets = []
        self.included_nodes = []
        self.excluded_nodes = []
        self.flags = []
        self.operations = []
        self.project = project
        self.preformat = False
        self.show = None
        self.param_string = param_string
        self.system_contents = []
        self.source_node = None  # set by node once compiled
        self.init_self(param_string)
        if not self.show:
            self.show = '$_link\n'
        self.ran = False

    def init_self(self, contents):
        self.contents = contents

        for match in syntax.function_c.finditer(contents):

            func, argument_string = match.group(1), match.group().strip(match.group(1)).replace(')(', '')
            argument_string = match.group(2)
            call = self.project.get_call(func)
            if call:
                op = call(self.project)
                op.argument_string = argument_string
                op.frame = self
                op.parse_argument_string(argument_string)
                op.on_added()
                self.operations.append(op)
            elif self.project.compiled:
                self.system_contents.append('call "%s" not found' % func)

    def is_manual(self):
        for op in self.operations:
            if op.is_manual:
                return True
        return False

    def preserve_title_if_present(self, target):
        if target.is_virtual and target.matching_string == '@self':
            source_node = self.project.get_node(self.source_node.id)
            if source_node:
                return ' ' + source_node.title + syntax.title_marker + '\n'
        if target.is_node:
            target_node = self.project.get_node(target.node_id)
            if target_node and target_node.first_line_title:
                return ' ' + target_node.title + syntax.title_marker + '\n'
        return ''

    def preserve_timestamp_if_present(self, target):
        if target.is_virtual and target.matching_string == '@self':
            source_node = self.project.get_node(self.source_node.id)
            if source_node:
                newest_timestamp = source_node.metadata.get_newest_timestamp()
                if newest_timestamp:
                    return newest_timestamp.wrapped_string
        if target.is_node:
            target_node = self.project.get_node(target.node_id)
            newest_timestamp = target_node.metadata.get_newest_timestamp()
            if newest_timestamp:
                return newest_timestamp.wrapped_string
        return ''

    def process_output(self):
        if not len(self.operations):
            return False
        self.included_nodes = []
        self.excluded_nodes = []
        self.project.run_hook('on_frame_process_started', self)
        accumulated_text = ''
        for operation in self.operations:
            if operation.should_continue() is False:
                return False

            current_text = accumulated_text
            try:
                transformed_text = operation.dynamic_output(current_text)
            except Exception as e:
                transformed_text = '`' + ''.join([
                    'error in ',
                    str(operation.name),
                    ': ',
                    traceback.format_exc(),
                    '\n'
                ]) + '`'
            if transformed_text is False:  # not None
                return ''
            if transformed_text is None:
                accumulated_text = current_text
                continue
            accumulated_text = transformed_text

        if accumulated_text == '':
            accumulated_text = self.default_output()

        self.flags = []
        self.project.run_hook('on_process_frame_ended', self)
        if self.system_contents:
            accumulated_text += '\n'.join(self.system_contents)
        return accumulated_text

    def default_output(self):
        for operation in list(reversed(self.operations)):
            if operation.should_continue() is False:
                return '%s specifies no text' % operation.name[0]
            try:
                transformed_text = operation.default_output()
            except Exception as e:
                transformed_text = '`' + ''.join([
                    'error in ',
                    str(operation.name),
                    ': ',
                    traceback.format_exc(),
                    '\n'
                ]) + '`'
                continue
            if transformed_text is None:
                continue
            if transformed_text is False:
                return False
            if transformed_text != '':
                return transformed_text
        return 'No call has text output'

    def have_flags(self, flag):
        if flag and flag[0] == '-':
            flag = flag[1:]
        if flag in self.flags:
            return True
        return False

    def get_definition_text(self):
        return '\n' + ''.join([
            syntax.frame_opening_wrapper,
            '\n'.join([line.strip() for line in self.contents.split('\n')]),
            syntax.frame_closing_wrapper
        ])

    def target_ids(self):
        target_ids = [t.node_id for t in self.targets if t.is_node]
        for t in self.targets:
            if t.is_virtual and t.matching_string == "@self":
                target_ids.append(self.source_node.id)
        return target_ids

    def target_files(self):
        return [t.filename for t in self.targets if t.is_file and t.filename is not None]

    def process(self, flags=None):
        if flags is None:
            flags = []
        self.flags = flags       
        output = self.process_output()
        self.ran = True
        return output

    def post_process(self, target, output):
        output = ''.join([
            self.preserve_timestamp_if_present(target),
            self.preserve_title_if_present(target),
            output])
        if target.is_virtual and target.matching_string == '@self':
            output += self.get_definition_text()
        return output

    def indent(self, contents, spaces=4):
        content_lines = contents.split('\n')
        content_lines[0] = content_lines[0].strip()
        for index, line in enumerate(content_lines):
            if line.strip() != '':
                content_lines[index] = '\t' * spaces + line
        return '\n' + '\n'.join(content_lines)
