import enum

class DialogManager(object):
	"""Manages the high-level interaction between the user and the system."""
	
	class STATE(enum.Enum):
		"""Enumeration of all the states that the system can assume."""
		INIT = 1
		USER_GREET = 2
		QUESTION_PENDING = 3
		USER_BYE = 4
		END = 5


	def __init__(self):

		#Stores the context of the conversation. For future use.
		self.context = None

		#Current state = initial state
		self.state = self.STATE.INIT

	



manager = DialogManager()
