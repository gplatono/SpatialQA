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
			for i in range(0, len(ents)):
				if certainty[i] < threashold:
					out.append(entities_to_english_list(ents[:i], attribute))
					out.append(entities_to_english_list(ents[i:], attribute))
					if i >= 1:
						out[0] += " are"
					else:
						out[0] += " is"
					return out
			out.append(entities_to_english_list(ents, attribute))
			return out

		def english_sentence_to_list(sentence):
			# Divide the sentence into words
			list = sentence.split()

			# Next, we need to split the punctuation marks from the words
			# ie. ['Is', 'this...', 'pig-latin?'] -> ['Is', 'this', '...', 'pig-latin', '?']
			diff = 1
			i = 0
			while i < len(list):
				# if the word ends in a punctuation mark
				if not list[i][-1].isalpha():
					cutoff_len = 1;
					for j in range(2, len(list[i])):
						if list[i][-j].isalpha():
							cutoff_len = j-1
							break
					else:
						i += 1
						continue

					list.insert(i+diff, list[i][-cutoff_len:])
					list[i] = list[i][:-cutoff_len]

					diff += 1
					i -= 1
				i += 1
			return list

		# There needs to be a better way to do this...  To cover cases where it is
		# non-obvious
		def get_verb_phrase(user_input_surface, is_are):
			if not is_are == "*":
				return is_are + user_input_surface.split(is_are)[1]
			else:
				return add(user_input_list.split()[3:])


		# pre-processing
		user_input_surface = lower(user_input_surface)
		user_input_list = english_sentence_to_list(user_input_surface)
		while not user_input_surface[-1].isalpha():
			user_input_surface = user_input_surface[:-1]
		is_are = "*"
		pos_isare = ["is", "are", "does", "do"]
		for ia in pos_isare:
			if ia in user_input_list:
				is_are = ia
				break
		type = "thing"
		pos_types = ["block", "row", "stack", "group", "blocks", "rows", "stacks", "groups"]
		for t in range(0, 8):
			if t == user_input_list[t]:
				type = user_input_list[t%4]
				break
		plural_type = type + "s"

		# Check which state we're in...
		if self.state == self.STATE.INIT:
			pass

		elif self.state == self.STATE.USER_GREET:
			pass

		elif self.state == self.STATE.QUESTION_PENDING:
			# Here, branch on the question type
			if question_type == IDENT:
				# These are the questions like "Which blocks are touching the SRI
				# block?" and "What block is above the Toyota block?"...  This
				# presuposes that the answer exists, but this will be treated very
				# similarly to the exists question, only with more emphasis on the
				# identification and less on the existance

				post_is = get_verb_phrase(user_input_surface, is_are, false)
				use_post_is = is_are in user_input_surface

				if len(answer_set) == 0:
					if len(certainty) == 0 or certainty[0] > 0.7:
						# give a certain "it doesn't exist" answer
						if use_post_is:
							return "There " + is_are + " no " + post_is + "."
						else:
							return "Such a " + type + " doesn't exist."
					else: # note this is probably not reachable
						if use_post_is:
							return "There " + is_are + " no " + post_is + "."
						else:
							return "That doesn't exit."

				ans_list = entities_to_english_list(answer_set, 'name')

				if len(answer_set) == 1:
					if certainty[0] > 0.7:
						# give a certain affirmative answer
						if use_post_is:
							return "Only " + ans_list + " is " + post_is + "."
						else:
							return "Just " + ans_list + " is."
					else:
						# give an uncertain affirmative answer
						if use_post_is:
							return "I think only " + ans_list + " is " + post_is + "."
						else:
							return "Probably just " + ans_list + " is."
				else:
					if min(certainty) < 0.7:
						if max(certainty) > 0.7:
							# give a mixed certainty answer
							cert_lists = entities_to_english_lists_by_certainty(answer_set, "name", certainty, 0.7)
							ver = ""
							if use_post_there:
								return "I am sure that " + cert_lists[0] + is_are + post_there + ", but less certain about " + cert_lists[1] + "."
							else:
								return "I am certain that " + cert_lists[0] + is_are + ", but less sure about " + cert_lists[1] + "."
						else:
							# give an uncertain answer
							if use_post_is:
								return "Maybe " + ans_list + " are " + post_is + "."
							else:
								return "Perhaps " + ans_list + " are."
					else:
						# give a certain answer
						if use_post_is:
							return capitalize(ans_list) + " are " + post_is + "."
						else:
							return capitalize(ans_list) + " are."

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

				# do some pre-processing
				post_there = user_input_surface.split("there")[1]
				use_post_there = user_input_surface.startswith("is there") or user_input_surface.startswith("are there")
				#use_post_there = use_post_there or user_input_surface.startswith("does there exist") or user_input_surface.startswith("do there exist"):
				#can't decide if it sounds more natural with/out this

				if len(answer_set) == 0:
					if len(certainty) == 0 or certainty[0] > 0.7:
					# give a certain negative answer
						if use_post_there:
							return "No, there " + is_are + " not " + post_there + "."
						else:
							return "No, there " + is_are + "not."
					else: # note that this is probably not reachable
					# give an uncertain negative answer
						return "I do not think there " + is_are + "."
				else:
					if min(certainty) < 0.7:
						if max(certainty) > 0.7:
							# give a mixed certainty positive answer
							cert_lists = entities_to_english_lists_by_certainty(answer_set, "name", certainty, 0.7)
							if use_post_there:
								return "I am sure that " + cert_lists[0] + is_are + post_there + ", but less certain about " + cert_lists[1] + "."
							else:
								return "I am certain that " + cert_lists[0] + is_are + ", but less sure about " + cert_lists[1] + "."
						else:
							# give an uncertain positive answer
							if use_post_there:
								return "I think there " + is_are + post_there + "."
							else:
								return "Yes, there probably" + is_are + "."
					else:
						# give a certain positive answer
						if use_post_there:
							return "Yes, there " + is_are + post_there + "."
						else:
							return "Yes, I am certain of it."

			elif question_type == ATTRIBUTIVE:
				# These are the questions like "What is the color of the leftmost
				# block?" and "how high is the Toyota block?".  They can be
				# identification, existance, or confirmation qustions themselves,
				# so these are difficult to answer
				pass

			elif question_type == CARDINALITY:
				# These are questions like "How many blocks are to the left of the
				# NVidia block" and "How many blocks touch the McDonals block?"
				# If it is just one, we want to say that and name it, otherwise
				# just give a number based on the size of the answer set and
				# adjust for certainty

				# preprocessing
				post_is = get_verb_phrase(user_input_surface, is_are, true)
				use_post_is = post_is.startswith(is_are)
				# ideally this would be "are to the left of the Nvidia block" and
				# "touch the McDonals block"

				if len(answer_set) == 0:
					return "There are no " + plural_type + " that " + post_is + "."  # say there are none

				ans_list = entities_to_english_list(answer_set, 'name')

				# This part is very much like the identification
				if len(answer_set) == 1:
					if certainty[0] > 0.7:
						if use_post_is:
							return "Just " + ans_list + post_is + "." # name the one, with certainty
						else:
							return "Only " + ans_list
					else:
						if use_post_is:
							return "I think just " + ans_list + post_is + "." # name the one, with certainty
						else:
							return "Probably only " + ans_list
				else:
					if certainty[0] > 0.7:
						pass # give the number, with certainty
					else:
						pass # give the number, with uncertainty
				pass

			elif question_type == ERROR:
				pass

		elif self.state == self.STATE.USER_BYE:
			pass

		elif self.state == self.STATE.END:
			pass


manager = HCIManager()
manager.start()

