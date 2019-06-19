import enum
from ulf_grammar import NArg, NRel, NPred, NCardDet

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
		self.relatum = None
		self.referent = None
		self.resolve_relatum = False
		self.resolve_referent = False

		if type(self.raw) == NArg:
			self.content_type = self.ContentType.ARG
			self.arg = gr_sentence.content			
		else:
			self.content_type = self.ContentType.PRED
			self.predicate = gr_sentence.content
			self.relatum = self.predicate.children[0]
			if len(self.predicate.children) > 1:
				self.referent = self.predicate.children[1]

		self.resolve_relatum = self.resolve_arg(self.relatum)
		if self.referent is not None:
			self.resolve_referent = self.resolve_arg(self.referent)

		print ("QUERY CONTENT:")
		print ("PREDICATE: ", self.predicate)
		print ("RELATUM: ", self.relatum)
		print ("REFERENT: ", self.referent)
		print ("RESOLVE RELATUM: ", self.resolve_relatum)
		print ("RESOLVE REFERENT: ", self.resolve_referent)

	def resolve_arg(self, arg):
		if arg.det is not None:
			print (arg.det)
			if type(arg.det) == NCardDet or arg.det.content in ["which.d", "what.d", "HOWMANY"]:
				print ("YES")
				return True
		return False


