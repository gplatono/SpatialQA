import enum
from gcs_micstream import ResumableMicrophoneStream
from google.cloud import speech
import sys
import re
import requests
from threading import Thread, RLock
import time
import operator

class HCIManager(object):
	"""Manages the high-level interaction loop between the user and the system."""

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

		#User's latest speech piece
		self.current_input = ""

		#The address of the avatar's speech processing servlet
		self.avatar_speech_servlet = 'http://ec2-35-162-37-211.us-west-2.compute.amazonaws.com:8080/avatar_control/'

		self.speech_lock = RLock()

	def start(self):
		"""Initiate the listening loop."""

		print ("Starting the listening thread...")
		mic_thread = Thread(target = self.mic_loop)
		mic_thread.start()
		#thread.join()
		print ("Starting the processing loop...")
		while True:
			self.speech_lock.acquire()
			if self.current_input != "":
				if re.search(r'\b(exit|quit)\b', self.current_input, re.I):
					self.speech_lock.release()
					break
				print ("you said: " + self.current_input)
				self.current_input = ""
			self.speech_lock.release()
			time.sleep(0.1)

	def say(self, text):
		print ("Avatar's response: " + text)
		req = requests.get(self.avatar_speech_servlet + "?say=" + text)
		avatar_status = str(req.status_code)
		print ("STATUS: " + avatar_status)

	def mic_loop(self):
		"""The mic listening loop."""

		# Audio recording parameters
		sample_rate = 16000
		chunk_size = int(sample_rate / 10)  # 100ms

		client = speech.SpeechClient()
		config = speech.types.RecognitionConfig(encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
			sample_rate_hertz=sample_rate, language_code='en-US', max_alternatives=1, enable_word_time_offsets=True,
			 enable_automatic_punctuation=True)
		streaming_config = speech.types.StreamingRecognitionConfig(config=config, interim_results=True)

		mic_manager = ResumableMicrophoneStream(sample_rate, chunk_size)

		with mic_manager as stream:
			while not stream.closed:
				audio_generator = stream.generator()
				requests = (speech.types.StreamingRecognizeRequest(audio_content=content)
					for content in audio_generator)

				responses = client.streaming_recognize(streaming_config, requests)

				responses = (r for r in responses if (r.results and r.results[0].alternatives))
				num_chars_printed = 0
				for response in responses:
					if not response.results:
						continue

					"""The `results` list is consecutive. For streaming, we only care about
					the first result being considered, since once it's `is_final`, it
					moves on to considering the next utterance."""
					result = response.results[0]
					if not result.alternatives:
						continue

					transcript = result.alternatives[0].transcript
					# Display interim results, but with a carriage return at the end of the
					# line, so subsequent lines will overwrite them.
					# If the previous result was longer than this one, we need to print
					# some extra spaces to overwrite the previous result
					overwrite_chars = ' ' * (num_chars_printed - len(transcript))

					if not result.is_final:
						sys.stdout.write(transcript + overwrite_chars + '\r')
						sys.stdout.flush()
						num_chars_printed = len(transcript)
					else:
						self.speech_lock.acquire()
						self.current_input = transcript.lower()
						self.speech_lock.release()

						# Exit recognition if any of the transcribed phrases could be one of our keywords.
						if re.search(r'\b(exit|quit)\b', transcript, re.I):
							print('Exiting..')
							stream.closed = True
							break

						num_chars_printed = 0

	# forgive me, much of this is not very "pythonic", I'm still getting more
	# comfortable with it
	def generate_response(self, user_input_surface, query_object, question_type, answer_set, is_ambiguous, certainty):
		# first a few helper functions

		# takes an entity list and returns an english list with no excess whitespace
		# the list must be of length at least 1
		# ents is the answer set, attribute is the attribute that should be listed
		def entities_to_english_list(ents, attribute):
			types = map(lambda x: lower(x.type_structure[:-1][0]), ents)
			attribs = map(operator.attrgetter(attribute), ents)
			uniform_type = all(x == type[0] for x in type)

			if len(list) == 1:
				return 'the ' + attribs[0]
			elif len(list) == 2:
				return 'the ' + attribs[0] + ' ' + types[0] + ' and the ' + attribs[1] + types[1]
			else:
				if uniform_type:
					out = 'the ' + attribs[0]
					for i in range(1, len(list)-1):
						out += ', ' + attribs[i]
					out += ', and ' + attribs[-1] + ' ' + types[-1] + 's'
					return out
				else:
					out = 'the ' + attribs[0] + ' ' + types[0]
					for i in range(1, len(list)-1):
						out += ', ' + attribs[i] + ' ' + types[i]
					out += ', and ' + attribs[-1] + ' ' + types[-1]
					return out
		# Sample Usage:
		# [_Nvidia_] -> (is...) "the Nvidia block" (is...)
		# [_Toyota_, _McDonalds_] ->
		#                  (...are) "the Toyota block and the McDonalds block" (are...)
		# [_SRI_, _Mercedes_, _Target_] ->
		#                      (...are) "the SRI, Mercedes, and Target blocks" (are...)
		# [_SRI_, _Mercedes_, _Support_] ->
		#  (...are) "the SRI block, the Mercedes block, and the Support stack" (are...)

		# returns two lists divided by the certainty about each entity
		# used in mixed certainty answers
		# assumes answers are already sorted by certainty
		def entities_to_english_lists_by_certainty(ents, attribute, certainty, threashold):
			out = []
			for i in range(0, len(certainty)):
				if certainty[i] < threashold:
					out.append(entities_to_english_list(ents[:i], attribute))
					out.append(entities_to_english_list(ents[i:], attribute))
					return out
			out.append(entities_to_english_list(ents, attribute))
			return out

		# First check which state we're in...
		if self.state == self.STATE.INIT:
			pass

		elif self.state == self.STATE.USER_GREET:
			pass # give a greeting

		elif self.state == self.STATE.QUESTION_PENDING:
			# Here, branch on the question type
			if question_type == IDENT:
				# These are the questions like "Which blocks are touching the SRI
				# block?" and "What block is above the Toyota block?"...  This
				# presuposes that the answer exists, but this will be treated very
				# similarly to the exists question, only with more emphasis on the
				# identification and less on the existance
				if len(answer_set) == 0:
					if certainty[0] > 0.7:
						pass # give a certain "it doesn't exist" answer
					else:
						pass # give an uncertain "it doesn't exist" answer
				else:
					if min(certainty) < 0.7:
						if max(certainty) > 0.7:
							pass # give a mixed certainty answer
						else:
							pass  # give an uncertain answer
					else:
						pass  # give a certain answer

			elif question_type == CONFIRM:
				# These are the questions like "Is the SRI block near the Toyota
				# block?" and "The Toyota block is red, right?"
				# How these will be handled depends very much on what the answer set
				# will give in these cases, I'm not sure. I will assume for now
				# that it just contains a boolean value in these cases
				if answer_set[0]:
					if certainty[0] > 0.7:
						pass # give a certain affirmative answer
					else:
						pass # give an uncertain affirmative answer
				else:
					if certainty[0] > 0.7:
						pass # give a certain negative answer
					else:
						pass # give an uncertain negative answer

			elif question_type == EXIST:
				# These are the questions like "Is there a block at height 3?"
				# or "Is there a block to the left of the SRI block?"
				# In these cases, the answer set will be empty if the answer is no,
				# and contain the applicable items if it is yes
				# this conditional branch is a good starting point
				if len(answer_set) == 0:
					if certainty[0] > 0.7:
						pass # give a certain negative answer
					else:
						pass # give an uncertain negative answer
				else:
					if min(certainty) < 0.7:
						if max(certainty) > 0.7:
							pass # give a mixed certainty positive answer
						else:
							pass  # give an uncertain positive answer
					else:
						pass  # give a certain positive answer

			elif question_type == ATTRIBUTIVE:
				# These are the questions like "What is the color of the leftmost
				# block?" and "how high is the Toyota block?".  They can be
				# identification, existance, or confirmation qustions themselves,
				# so these are difficult to answer
				pass
			elif question_type == ERROR:
				pass

		elif self.state == self.STATE.USER_BYE:
			pass # say goodbye

		elif self.state == self.STATE.END:
			pass


manager = HCIManager()
manager.start()
