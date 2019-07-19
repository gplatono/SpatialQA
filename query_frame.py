import enum
import re
from ulf_grammar import NArg, NRel, NPred, NCardDet, TAdj, NColor, NConjArg

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
		CONFIRM = 1
		IDENT = 2
		DESCR = 3
		COUNT = 4
		ATTR_COLOR = 5
		ATTR_ORIENT = 6
		ERROR = 7

	def __init__(self, query_surface, query_ulf, query_parse_tree):
		self.surface = query_surface
		self.ulf = query_ulf
		self.raw = query_parse_tree.content

		#print ("QUERY REPRESENTATIONS: ")
		#print (self.surface)
		#print (self.ulf)
		#print (self.raw)
		self.query_type = self.QueryType.ERROR

		if query_parse_tree is None:
			self.query_type = self.QueryType.ERROR
			return

		self.is_question = query_parse_tree.is_question

		self.YN_FLAG = False
		self.COUNT_FLAG = False
		self.EXIST_FLAG = False
		self.IDENT_FLAG = False
		self.DESCR_FLAG = False

		self.arg = None
		
		self.predicate = None
		self.relatum = None
		self.referent = None
		self.resolve_relatum = False
		self.resolve_referent = False

		if type(self.raw) == NArg or type(self.raw) == NConjArg:
			self.content_type = self.ContentType.ARG
			self.arg = query_parse_tree.content			
		else:
			self.content_type = self.ContentType.PRED
			self.predicate = query_parse_tree.content
			self.relatum = self.predicate.children[0]
			if len(self.predicate.children) > 1:
				self.referent = self.predicate.children[1]

		if self.relatum is not None and type(self.relatum) == NArg:
			self.resolve_relatum = self.resolve_arg(self.relatum)
		if self.referent is not None and type(self.referent) == NArg:
			self.resolve_referent = self.resolve_arg(self.referent)

		#print ("BEFORE ENTERING QUERY TPYE:")
		self.scan_type()

		self.is_subject_plural = self.subj_plural()


		#print ("QUERY CONTENT:")
		#print ("PREDICATE: ", self.predicate)
		#print ("RELATUM: ", self.relatum)
		#print ("REFERENT: ", self.referent)
		#print ("RESOLVE RELATUM: ", self.resolve_relatum)
		#print ("RESOLVE REFERENT: ", self.resolve_referent)

	def resolve_arg(self, arg):
		if arg.det is not None:
			print (arg.det)
			if type(arg.det) == NCardDet or arg.det.content in ["which.d", "what.d", "HOWMANY", "how_many.d"]:
				print ("YES")
				return True
		return False

	def scan_type(self):
		self.YN_FLAG = True if re.search(r'^\(*(pres|past|pres perf\)|pres prog\)|prog) (be.v|do.aux|can.aux)', self.ulf, re.IGNORECASE) else False
		self.COUNT_FLAG = True if re.search(r'^\(*(how.adv-a many.a|how_many.d)', self.ulf, re.IGNORECASE) else False
		
		if re.search('^.*(how.mod-a many.a|how_many.d)', self.ulf, re.IGNORECASE):
			self.COUNT_FLAG = True
		
		self.IDENT_FLAG = True if re.search('^.*(what.d|which.d).*(block.n).*(be.v)', self.ulf, re.IGNORECASE) else False
		self.IDENT_FLAG = True if re.search('^.*(what.pro|which.pro).*(be.v)', self.ulf, re.IGNORECASE) else self.IDENT_FLAG

		if re.search(r'^\(*what.pro', self.ulf, re.IGNORECASE):
			self.IDENT_FLAG = True

		self.DESCR_FLAG = True if re.search(r'^\(*(where).*(be.v).*\|.*\|.* block.n', self.ulf, re.IGNORECASE) else False
		self.DESCR_FLAG = True if re.search(r'at.p \(what.d place.n\)', self.ulf, re.IGNORECASE) else self.DESCR_FLAG

		if self.COUNT_FLAG:
			self.query_type = self.QueryType.COUNT

		if self.IDENT_FLAG:
			self.query_type = self.QueryType.IDENT

		if self.DESCR_FLAG:
			self.query_type = self.QueryType.DESCR

		if self.YN_FLAG:
			self.query_type = self.QueryType.CONFIRM		

	def extract_subject_adj_modifiers(self):
		if self.arg is not None:
			mods = self.arg.mods
		else:
			mods = self.predicate.children[0].mods
		adjectives = []
		if mods is not None:
			for mod in mods:
				if type(mod) == TAdj or type(mod) == NColor:
					adjectives.append(mod.content.replace(".a", ""))
		return adjectives

	def subj_plural(self):
		if self.arg is not None:
			return self.arg.plur
		else: 
			return self.predicate.children[0].plur

