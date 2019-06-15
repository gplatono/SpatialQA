import enum
from ulf_parser import NArg, NRel, NPred

class QueryFrame(object):
	"""Represents and incapsulates the query data in a frame-like format."""

	class ContentType(enum.Enum):
		"""The nature of the qury top-level node,
		can predicate/relation or argument."""		
		PRED = 0
		ARG = 1

	class QueryType(enum.Enum):
		"""Possible categories of questions (subject to a change)."""
		EXIST = 0
		CONFRM = 1
		IDENT = 2
		DESCR = 3
		COUNT = 4
		ATTR_COLOR = 5
		ATTR_ORIENT = 6
		ERROR = 7

	def __init__(self, gr_sentence):
		self.raw = gr_sentence.content
		self.is_question = gr_sentence.is_question

		self.arg = None
		self.predicate = None
		self.pred_args = []

		if type(self.raw) == NArg:
			self.content_type = self.ContentType.ARG
			self.arg = gr_sentence.content
		else:
			self.content_type = self.ContentType.PRED
			self.predicate = gr_sentence.content