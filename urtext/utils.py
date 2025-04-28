from urtext.target import UrtextTarget
from urtext.link import UrtextLink
from urtext.url import url_match_c
import urtext.syntax as syntax
import os

def strip_backtick_escape(contents):
    ranges = []
    for e in syntax.preformat_c.finditer(contents):
        contents = contents.replace(e.group(),' '*len(e.group()))
        ranges.append([e.start(), e.end()])
    return ranges, contents

def force_list(thing):
	if not isinstance(thing, list):
		thing = [thing]
	return thing

def strip_illegal_file_characters(filename):
    for c in [
        '<', '>', '\:', '"', '/', '\\', '|', '?','*', '.', ';', '%']:
        filename = filename.replace(c,' ')
    return filename

def get_id_from_link(target):
    match = syntax.node_link_or_pointer_c.search(target)
    if match:
        return match.group(5)
    return target

def make_project_link(project_name):
    return ''.join([
        syntax.other_project_link_prefix,
        '"%s"' % project_name
        ])

def make_action_link(action_string):
    return ''.join([
        syntax.link_opening_pipe,
        syntax.node_link_modifiers['bound'],
        ' ',
        action_string,
        syntax.link_closing_wrapper     
        ])

def write_file_contents(filename, contents):
    with open(filename, 'w', encoding='utf-8' ) as f:
        f.write(contents)

def get_path_from_link(link):
    match = syntax.file_link_c.match(link)
    if match:
        return match.group(2)
    return link

def make_file_link(path):
    return ''.join([
        syntax.file_link_opening_wrapper,
        path,
        syntax.link_closing_wrapper])

def make_node_link(node_id, position=0):
    position_str = ''
    if position != 0:
        position_str = str(position)
    if position_str:
        position_str = ":" + position_str
    return ''.join([
        syntax.link_opening_wrapper,
        node_id,
        syntax.link_closing_wrapper,
        position_str])

def make_bound_link(text):
    return ''.join([
        syntax.link_opening_pipe,
        syntax.node_link_modifiers['bound'],
        ' ',
        text,
        syntax.link_closing_wrapper,
        ])

def make_node_pointer(node_id):
    return ''.join([
        syntax.link_opening_wrapper,
        node_id,
        syntax.pointer_closing_wrapper])

def get_all_targets_from_string(string, node, project_list):
    targets = []
    links, replaced_contents = get_all_links_from_string(string, node, project_list)
    for link in links:
        target = UrtextTarget(link.matching_string)
        target.is_link = True
        target.link = link
        target.containing_project_name = link.containing_project_name
        link.containing_node = node
        target.is_node = link.is_node
        target.filename = link.filename
        target.path = link.path
        target.node_id = link.node_id
        target.is_file = link.is_file
        target.is_missing = link.is_missing
        targets.append(target)
    for match in syntax.virtual_target_match_c.finditer(replaced_contents):
        target = UrtextTarget(match.group())
        target.is_virtual = True
        targets.append(target)
        replaced_contents = replaced_contents.replace(match.group(),'', 1)
    if replaced_contents.strip():
        target = UrtextTarget(replaced_contents.strip())
        target.is_raw_string = True
        target.is_node = True
        target.node_id = replaced_contents.strip()
        targets.append(target)
    return targets

def get_all_links_from_string(string, node, project_list, include_http=False):
    links = []
    replaced_contents = string
    for match in syntax.cross_project_link_with_node_c.finditer(replaced_contents):
        link = UrtextLink(match.group(), node, project_list)
        link.target_project_name = match.group(2)
        link.node_id = match.group(7)
        link.is_node = True
        if match.group(9):
            try:
                link.dest_node_position = int(match.group(9)[1:])
            except:
                pass
        link.position_in_string = match.start()
        links.append(link)
        replaced_contents = replaced_contents.replace(match.group(),' ', 1)

    for match in syntax.file_link_c.finditer(replaced_contents):
        link = UrtextLink(match.group(), node, project_list)
        if match.group(1) == syntax.file_link_modifiers['missing']:
            link.is_missing = True
        link.path = match.group(2)
        link.is_file = True
        link.position_in_string = match.start()
        if match.group(4):
            if match.group(4)[0] == ":":
               link.character_number = int(match.group(4)[1:])
            if match.group(4)[0] == ".":
               link.line_number = int(match.group(4)[1:])
            link.suffix = match.group(4)
        links.append(link)
        replaced_contents = replaced_contents.replace(match.group(),' ', 1)
    
    for match in syntax.node_link_or_pointer_c.finditer(replaced_contents):
        link = UrtextLink(match.group(), node, project_list)
        kind = None
        if match.group(1) in syntax.node_link_modifiers.values():
            for kind in syntax.node_link_modifiers:
                if match.group(1) == syntax.node_link_modifiers[kind]:
                    kind = kind.upper()
                    break

        if kind == 'ACTION':
            link.is_action = True

        if kind == 'MISSING':
            link.is_missing = True

        if kind == 'BOUND':
            link.bound = True
            link.bound_argument = match.group(5).strip()

        link.node_id = match.group(5).strip()
        link.is_node = True
        if match.group(8):
            try:
                link.dest_node_position = int(match.group(8)[1:])
            except:
                pass
        if match.group(7) == syntax.pointer_closing_wrapper:
            link.is_pointer = True  
        link.position_in_string = match.start()
        links.append(link)
        replaced_contents = replaced_contents.replace(match.group(),' ', 1)
    
    for match in syntax.project_link_c.finditer(replaced_contents):
        link = UrtextLink(match.group(), node, project_list)        
        link.project_name = match.group(2)      
        link.position_in_string = match.start()
        links.append(link)
        replaced_contents = replaced_contents.replace(match.group(),' ', 1)

    if include_http:
        for match in url_match_c.finditer(replaced_contents):
            if match.group(1):
                http_link = match.group(1)
            else:
                http_link = match.group(3)
            link = UrtextLink(http_link, node, project_list)          
            link.is_http = True
            link.url = http_link
            link.position_in_string = match.start()
            links.append(link)
            replaced_contents = replaced_contents.replace(http_link,' ', 1)

    for l in links:
        l.project_list = project_list 
    return links, replaced_contents

def get_file_extension(filename):
    if len(os.path.splitext(filename)) == 2:
        return os.path.splitext(filename)[1].lstrip('.')

def strip_whitespace_anchors(contents):
    matches = syntax.whitespace_anchor_c.findall(contents)
    for e in matches:
        contents = contents.replace(e, ' ' * len(e), 1)
    return contents

def get_link_from_position_in_string(string, string_pos, node, project_list, include_http=True):
    if not string.strip():
        return None
    links, r = get_all_links_from_string(string, node, project_list, include_http=include_http)
    if links:
        links = sorted(links, key=lambda l: l.position_in_string)
        for link in links:
            if string_pos in range(link.position_in_string, link.position_in_string+len(link.matching_string)):
                return link
        return link

def strip_nested_links(title):
    stripped_title = title
    for nested_link in syntax.node_link_or_pointer_c.finditer(title):
        stripped_title = title.replace(nested_link.group(), '')
    return stripped_title

def strip_dynamic_markers(contents):
    if len(contents) and contents[0] == '~':
        contents = contents[1:]
        if len(contents) and contents[0] == '?':
            contents = contents[1:]
    return contents

def strip_embedded_syntaxes(contents):
    replaced_contents = contents
    stripped_contents = contents
    ranges = []
    for e in syntax.embedded_syntax_c.finditer(contents):
        contents = e.group()
        stripped_contents = stripped_contents.replace(contents, '')
        replaced_contents = replaced_contents.replace(contents, ' '*len(contents))
        ranges.append([e.start(), e.end()])
    return ranges, stripped_contents, replaced_contents

def strip_frames(contents):
    stripped_contents = contents
    for m in syntax.frame_c.finditer(contents):
        stripped_contents = stripped_contents.replace(m.group(),'', 1)
    return stripped_contents

def strip_metadata(contents):
    stripped_contents = contents
    for m in syntax.metadata_entry_with_or_without_values_c.finditer(contents):
        stripped_contents = stripped_contents.replace(m.group(),'', 1)
    return stripped_contents

def strip_urtext_syntax(contents):
    ranges, stripped_contents = strip_backtick_escape(contents) 
    stripped_contents = strip_whitespace_anchors(stripped_contents)
    ranges, stripped_contents, replaced_contents = utils.strip_embedded_syntaxes(stripped_contents)

    return contents

