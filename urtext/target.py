class UrtextTarget:

	def __init__(self, string):
		self.matching_string = string
		self.is_virtual = False
		self.is_link = False
		self.is_node = False
		self.is_file = False
		self.node_id = None
		self.link = None
		self.is_raw_string = False