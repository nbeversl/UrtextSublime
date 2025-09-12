import re

# Units
pattern_break = r'($|(?=[\s|\r|]))'
space = ' '
# Syntax Elements
node_opening_wrapper = '{'
node_closing_wrapper = '}'
link_opening_pipe = '|'
link_opening_pipe_escaped = re.escape(link_opening_pipe)
link_opening_wrapper = link_opening_pipe + space
node_link_modifiers = {
    'action'        : '!',
    'missing'       : '?',
    'bound'    : ':'
}
file_link_modifiers = {
    'file': '/',
    'missing': '?'
}
missing_node_link_opening_wrapper = ''.join([
    link_opening_pipe,
    node_link_modifiers['missing'],
    space,
    ])
whitespace_anchor = r'^\s*\.'
missing_file_link_opening_wrapper = ''.join([
    link_opening_pipe,
    file_link_modifiers['file'],
    file_link_modifiers['missing'],
    space,
    ])
bold_text = r'(\*\*)(.*)(\*\*)'
italic_text = r'(__)(.*)(__)'
node_link_modifiers_regex = {}
for modifier in node_link_modifiers:
    node_link_modifiers_regex[modifier] = ''.join([r'(?<=\|)', re.escape(node_link_modifiers[modifier])])
node_link_modifier_group = r'(' + '|'.join(
    ['(' + m + ')' for m in node_link_modifiers_regex.values()]) + ')?'

node_link_modifier_group = r'(' + '|'.join([
    '(' + m + ')' for m in [
        node_link_modifiers_regex['action'],
        node_link_modifiers_regex['missing'],
        node_link_modifiers_regex['bound'],
        ]
    ]) + ')?'

file_link_modifier_group = r'(' + re.escape(file_link_modifiers['missing']) + ')?'
link_closing_wrapper = ' >'
pointer_closing_wrapper = ' >>'
timestamp_opening_wrapper = '<'
timestamp_closing_wrapper = '>'
timestamp = r''.join([
    timestamp_opening_wrapper,
    r'([^-\/<\s][^=<]+?)',
    timestamp_closing_wrapper])
title_marker = ' _'
metadata_assignment_operator = '::'
metadata_closing_marker = ';'
metadata_separator = '-'
metadata_separator_syntax = ''.join([space, metadata_separator, space])
other_project_link_prefix = '=>'
frame_opening_wrapper = '[['
frame_closing_wrapper = ']]'
resolution_identifier = ' ^ '
virtual_target_marker = '@'
file_link_opening_wrapper = ''.join([
    link_opening_pipe,
    file_link_modifiers['file'],
    space])
project_link=r''.join([
    '(', other_project_link_prefix, ')', '\"([^\"]+?)\"'])
node_link_opening_wrapper_match = r''.join([
    '(?<!")',
    link_opening_pipe_escaped,
    node_link_modifier_group,
    r'\s'
    ])
# Base Patterns
closing_wrapper = r'(?<!\\)' + re.escape(node_closing_wrapper)
call_flag = '((-[\w_]+)|\*)(\s|$)'
call_flags = r''.join([
    '(^|\s)(',
    call_flag,
    ')+'
    ])
hash_key = r'#'
call_key = r'([^\'\-' + hash_key + virtual_target_marker + '][\w\._]+)'
call_key_with_opt_flags = r''.join([
    call_key,
    '\s*?',
    '(',
    call_flags,
    ')?',
    ])
frame = r'(?:\[\[)([^\]]*?)(?:\]\])'
dynamic_marker = '~'
missing_frame_marker = '?'
embedded_syntax_open = r'%%\w+'
embedded_syntax_close = r'%%'+pattern_break
format_key = r'\$_?[\.A-Za-z0-9_-]*'
metadata_arg_delimiter = r';|\r'
metadata_op_before = r'before'
metadata_op_after = r'after'
metadata_op_equals = r'='
metadata_op_not_equals = r'!='
metadata_op_contains = r'\?'
metadata_op_is_like = r'~'
metadata_ops_or = r'\|'
metadata_assigner = '::'
metadata_end_marker = r';'
metadata_entry_modifiers = r'[+]?\*{0,2}'
metadata_key = r'[\w_\?\!\#\d-]+?'
metadata_values = r'[^\n;]+($|\n|;)'
metadata_entry = r''.join([
    metadata_entry_modifiers,
    metadata_key,
    metadata_assigner,
    metadata_values,
    ])

metadata_entry_with_or_without_values = ''.join([
    metadata_entry_modifiers,
    metadata_key,
    metadata_assigner,
    '(', metadata_values, ')*'
    ])
metadata_key_only = r''.join([
    metadata_entry_modifiers, 
    metadata_key,
    metadata_assigner,
    ])                          
metadata_separator_pattern = r'\s' + metadata_separator + r'\s'
metadata_tag_self = r'\+'
metadata_tag_desc = r'\*'
meta_to_node = r'(\w+)(\:\:)\{'
opening_wrapper = r'(?<!\\)' + re.escape(node_opening_wrapper)
preformat = r'\`.*?\`'
sub_node = r'(?<!\\){(?!.*(?<!\\){)(?:(?!}).)*}'
virtual_target = r'' + virtual_target_marker + '[\w_]+'
disallowed_title_characters = [
    r'\|',
    r'\>',
    r'@',
    r'\n',
    r'\r',
    r'`',
    r'\^',
    r'\$',
    r'\[\[',
    r'\]\]',
    r'#',
    r'\{',
    r'\}',
]
title_pattern = r'^([^' + r''.join(disallowed_title_characters) + ']+)'
id_pattern = r'([^\|>\n\r]+)'

# (for syntax highlighting only)
sh_metadata_key = metadata_key + '(?='+metadata_assigner+')'
sh_metadata_values = r'(?<=::)[^\n};@]+;?'
sh_metadata_key_c = re.compile(sh_metadata_key)
sh_metadata_values_c = re.compile(sh_metadata_values)
metadata_flags = r'\+?\*{1,2}(?=' + metadata_key + ')' 
metadata_flags_c = re.compile(metadata_flags)
node_link_modifiers_regex_c = {
    'action': re.compile(node_link_modifiers_regex['action']),
    'missing': re.compile(node_link_modifiers_regex['missing']),
}

# Composite match patterns

embedded_syntax_full = embedded_syntax_open + '.*?' + embedded_syntax_close
hash_meta = r''.join([
    '(?:^|\s)',
    metadata_entry_modifiers,
    hash_key,
    '([A-Z,a-z][^-\s]*)(-',
    timestamp,
    ')?'
    ])
call_hash_meta = hash_key + r'[A-Z,a-z].*'
node_link_or_pointer = r''.join([
    link_opening_pipe_escaped,
    node_link_modifier_group,
    '\s',
    '(', id_pattern, ')',
    '(\s>{1,2})(\:\d{1,99})?(?!>)',
    ])

node_link = r''.join([
    link_opening_pipe_escaped,
    node_link_modifier_group,
    '(', id_pattern, ')',
    '(\s>)(\:\d{1,99})?(?!>)',
    ])

cross_project_link_with_node = r''.join ([
    project_link,
    node_link_or_pointer,
    ])

function = r'([A-Z_\-\+\>]+)\((((\|\s)(([^\|>\n\r])+)\s>)?([^\)]*?))\)(?![^\s\r\n]>)'

node_action_link = r''.join([
    link_opening_pipe_escaped,
    node_link_modifiers_regex['action'],
    '\s',
    '(',
    id_pattern,
    ')\s>{1,2}(?!>)'])
node_pointer = r''.join([
    node_link_opening_wrapper_match,
    '(',
    id_pattern,
    ')',
    pointer_closing_wrapper,
    '(?!>)'
    ])
node_title = r'^'+ title_pattern +r'(?=' + title_marker  + pattern_break + ')'

file_link = r''.join([
    link_opening_pipe_escaped,
    file_link_modifiers['file'],
    file_link_modifier_group,
    space,
    r'([^;\n\r]+?)',
    '(', link_closing_wrapper, ')',
    '((\:|\.)\d{1,99})?'
    '(?!>)'
    ])

not_metadata_separator = r'([^\s]*(\s([^-]|$)|\s-([^\s]|$)|))' 

special_metadata_patterns = r''.join([
    '(', 
    file_link, 
    ')|(',
    node_link_or_pointer,
    ')'
])

metadata_ops = r'(' + r'|'.join([
            metadata_op_before,
            metadata_op_after,
            metadata_op_equals,
            metadata_op_not_equals,
            metadata_op_contains,
            metadata_op_is_like,
        ]) + r')'
call_key_op_value = r''.join([
    '(',
    metadata_key,
    ')',
    '\s*',
    metadata_ops,
    '((',
    metadata_values,
    ')|(',
    timestamp,
    '))',
    ])
# Compiled Patterns
node_link_or_pointer_c = re.compile(node_link_or_pointer)
bold_text_c = re.compile(bold_text)

closing_wrapper_c = re.compile(closing_wrapper)
cross_project_link_with_node_c = re.compile(cross_project_link_with_node)
call_flags_c = re.compile(call_flags)
call_hash_meta_c = re.compile(call_hash_meta)
call_key_with_opt_flags = re.compile(call_key_with_opt_flags)
call_key_op_value_c = re.compile(call_key_op_value)
frame_c = re.compile(frame, flags=re.DOTALL)
dynamic_marker_c = re.compile(dynamic_marker)
file_link_c = re.compile(file_link)
embedded_syntax_open_c = re.compile(embedded_syntax_open, flags=re.DOTALL)
embedded_syntax_c = re.compile(embedded_syntax_full, flags=re.DOTALL)
embedded_syntax_close_c = re.compile(embedded_syntax_close, flags=re.DOTALL)
format_key_c = re.compile(format_key, flags=re.DOTALL)
function_c = re.compile(function, flags=re.DOTALL)
hash_key_c = re.compile(hash_key)
hash_meta_c = re.compile(hash_meta)
italic_text_c = re.compile(italic_text)
metadata_arg_delimiter_c = re.compile(metadata_arg_delimiter)
metadata_entry_c = re.compile(metadata_entry, flags=re.DOTALL)
metadata_entry_with_or_without_values_c = re.compile(metadata_entry, flags=re.DOTALL)
metadata_key_only_c = re.compile(metadata_key_only, flags=re.DOTALL)
metadata_ops_c = re.compile(metadata_ops)
metadata_ops_or_c = re.compile(metadata_ops_or)
special_metadata_patterns_c = re.compile(special_metadata_patterns)
metadata_separator_pattern_c = re.compile(metadata_separator_pattern)
meta_to_node_c = re.compile(meta_to_node, flags=re.DOTALL)
metadata_tag_self_c = re.compile(metadata_tag_self)
metadata_tag_desc_c = re.compile(metadata_tag_desc)
node_action_link_c = re.compile(node_action_link, flags=re.DOTALL)
node_pointer_c = re.compile(node_pointer)
node_title_c = re.compile(node_title, flags=re.MULTILINE)
metadata_assigner_c = re.compile(metadata_assigner)
node_link_c = re.compile(node_link)
node_link_or_pointer_c = re.compile(node_link_or_pointer)
opening_wrapper_c = re.compile(opening_wrapper)
pointer_closing_wrapper_c = re.compile(pointer_closing_wrapper)
preformat_c = re.compile(preformat, flags=re.DOTALL)
project_link_c = re.compile(project_link, flags=re.DOTALL)
subnode_regexp_c = re.compile(sub_node, flags=re.DOTALL)
timestamp_c = re.compile(timestamp)
title_regex_c = re.compile(title_pattern)
virtual_target_match_c = re.compile(virtual_target, flags=re.DOTALL)
whitespace_anchor_c = re.compile(whitespace_anchor, flags=re.M)
metadata_replacements = re.compile("|".join([
    r'(?:<)([^-/<\s`][^=<]+?)(?:>)', # timestamp
    r'\*{0,2}\w+\:\:([^\n}]+);?', # inline_meta
    r'\*{0,2}\w+\:\:\{[^\}]\}', # node as meta
    r'(?:^|\s)#[A-Z,a-z].*?(\b|$)', # shorthand_meta
    ]))
compiled_symbols = {
    opening_wrapper_c : 'opening_wrapper',
    closing_wrapper_c : 'closing_wrapper',
    re.compile(node_pointer) : 'pointer',
    meta_to_node_c : 'meta_to_node'
    }
embedded_syntax_symbols = {
    re.compile(embedded_syntax_open) : 'embedded_syntax_open', 
    re.compile(embedded_syntax_close) : 'embedded_syntax_close',

}