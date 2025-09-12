from urtext.buffer import UrtextBuffer
import urtext.syntax as syntax
import urtext.utils as utils

class UrtextFile(UrtextBuffer):
   
    def __init__(self, filename, project):
        self.filename = filename
        self.project = project
        super().__init__(project, filename, self._read_contents())

    def _get_contents(self):
        if not self.contents:
            self.contents = self._read_contents()
        return self.contents

    def _read_contents(self):
        """ returns the file contents, filtering out Unicode Errors, directories, other errors """
        buffer_setting = self.project.get_single_setting('use_buffer')
        if buffer_setting and buffer_setting.true():
            contents = self.project.run_editor_method('get_buffer', self.filename)
            if contents:
                return contents
        try:
            with open(self.filename, 'r', encoding='utf-8') as theFile:
                full_file_contents = theFile.read()
        except IsADirectoryError:
            return None
        except UnicodeDecodeError:
            self._log_error(''.join([
                'UnicodeDecode Error: ',
                syntax.file_link_opening_wrapper,
                self.filename,
                syntax.link_closing_wrapper]), 0)
            return None
        except TimeoutError:
            return print('Timed out reading %s' % self.filename)
        except FileNotFoundError:
            return print('Cannot read file from storage %s' % self.filename)
        return full_file_contents

    def write_buffer_contents(self, run_hook=False, re_parse=True):
        if run_hook: # for last modification only
            self.project.run_hook('on_write_file_contents', self)
        existing_contents = self._read_contents()
        if existing_contents == self.contents:
            return False
        if self.filename:
            utils.write_file_contents(self.filename, self.contents)
            buffer_setting = self.project.get_single_setting('use_buffer')
            if buffer_setting and buffer_setting.true():
                self.project.run_editor_method('set_buffer', self.filename, self.contents)
            else:
                open_files = self.project.run_editor_method('get_open_files')
                if self.filename in open_files and open_files[self.filename] == False:
                    self.project.run_editor_method('refresh_files', self.filename)
        elif self.identifier:
            self.project.run_editor_method('set_buffer', None, self.contents, identifier=self.identifier)
        if re_parse:
            self.project._parse_file(self.filename)
        return True
