import enum
import os
import sys
import re
import requests
from threading import Thread, RLock
import time
import operator
import collections

class HCIManager(object):
	"""Manages the high-level interaction loop between the user and the system."""

	class STATE(enum.Enum):
		"""Enumeration of all the states that the system can assume."""
		INIT = 1
		USER_GREET = 2
		QUESTION_PENDING = 3
		USER_BYE = 4
		END = 5

	def __init__(self, debug_mode = False):

		#Stores the context of the conversation. For future use.
		self.context = None

		self.debug_mode = debug_mode

		#Current state = initial state
		self.state = self.STATE.INIT

		#User's latest speech piece
		self.current_input = ""

		#The address of the avatar's speech processing servlet
		self.avatar_speech_servlet = 'http://ec2-35-162-37-211.us-west-2.compute.amazonaws.com:8080/avatar_control/'

		self.speech_lock = RLock()

		self.lissa_path = ".." + os.sep + "lissa-blocksworld" + os.sep
		self.lissa_input = self.lissa_path + "input.lisp"
		self.lissa_ulf = self.lissa_path + "ulf.lisp"
		self.lissa_reaction = self.lissa_path + "reaction.lisp"
		self.lissa_output = self.lissa_path + "output.txt"

		# print (self.lissa_input)
		# print (self.lissa_ulf)
		# print (self.lissa_reaction)
		# print (self.lissa_output)

		# print (os.path.isfile(self.lissa_ulf))
		# print (os.path.isfile(self.lissa_reaction))
		# print (os.path.isfile(self.lissa_output))

	def start(self):
		"""Initiate the listening loop."""
		if self.debug_mode == False:			
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

				if self.debug_mode == False:
					print ("ENTERING LISSA EXCHANGE BLOCK...")
					lisp_formatted_input = "(setq *next-input* \"" + self.current_input + "\")"

					lissa_inp_file = open(self.lissa_input, 'w+')
					lissa_inp_file.write(lisp_formatted_input)
					lissa_inp_file.close()

					time.sleep(0.5)

					print ("WAITING FOR ULF...")
					
					lissa_ulf_file = open(self.lissa_ulf, 'r+')					
					ulf = lissa_ulf_file.readline()
					lissa_ulf_file.truncate(0)
					lissa_ulf_file.close()
					
					ulf_counter = 1
					while ulf is None or ulf == "":
						time.sleep(0.2)
						lissa_ulf_file = open(self.lissa_ulf, 'r+')
						ulf = lissa_ulf_file.readline()
						lissa_ulf_file.truncate(0)
						lissa_ulf_file.close()					
						ulf_counter += 1
						if ulf_counter==7:
							break

					print (ulf)
									
					if ulf_counter == 7:
						continue

					print ("WRITING REACTION...")
					lisp_formatted_response = "(setq *next-reaction* \"" + "test" + "\")"
					lissa_react_file = open(self.lissa_reaction, 'w+')					
					lissa_react_file.write(lisp_formatted_response)
					lissa_react_file.close()

					print ("WAITING FOR RESPONSE...")

					time.sleep(0.2)

					lissa_out_file = open(self.lissa_output, 'r+')
					responses = lissa_out_file.readlines()
					lissa_out_file.truncate(0)
					lissa_out_file.close()
					while responses is None or responses == "" or responses == []:
						lissa_out_file = open(self.lissa_output, 'r+')
						responses = lissa_out_file.readlines()
						lissa_out_file.truncate(0)
						lissa_out_file.close()
						time.sleep(0.1)

					response = ""
					responses = [r.strip() for r in responses if r.strip() != ""]
					print ("response: " + str(responses))

				self.current_input = ""
			self.speech_lock.release()
			time.sleep(0.1)

	def say(self, text):
		print ("Avatar's response: " + text)
		req = requests.get(self.avatar_speech_servlet + "?say=" + text)
		avatar_status = str(req.status_code)
		print ("STATUS: " + avatar_status)

	def load_as_text(self, text):
		def load_loop():
			for utterance in text:
				while True:
					self.speech_lock.acquire()
					if self.current_input == "":
						self.current_input = utterance
						self.speech_lock.release()
						break
					self.speech_lock.release()

		ll_th = Thread(target = load_loop)
		ll_th.start()

	def mic_loop(self):
		"""The mic listening loop."""

		# Audio recording parameters

		from gcs_micstream import ResumableMicrophoneStream
		from google.cloud import speech

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

	'''
Here is a (nonexhaustive) list of questions that I think I can answer in a very natural way:
1: Existential Questions -
	Q: Is there a block at height 3?
	A: No, there is not a block that is at height 3.

	Q: Are there blocks to the left of the SRI block?
	A: Yes, a block that is to the left of the SRI block is the Toyota block.

	Q: Does there exist a red block touching a blue block?
	A: Yes, there probably does.
2: Identification Questions -
	Q: What block is above the Toyota block?
	A: There is no block that is above the Toyota block.

	Q: Which blocks are below the SRI block?
	A: The Toyota block and the Nvidia block are below the SRI block.

	Q: Which three blocks are below the SRI block?
	A: The Toyota block and the Nvidia block are below the SRI block,
				but it is less certain for the McDonald's block.
3. Counting Questions -
	Q: How many blocks are to the left of the Nvidia block?
	A: There are 7 blocks that are to the left of the Nvidia block.

	Q: How many blocks touch the Nvidia block?
	A: There are 3 blocks that touch the Nvidia block: the Toyota, Starbucks, and Mercedes blocks.

	Q: What is the number of blocks at height 5:
	A: There are 2: the SRI and Nvidia blocks
4. Questions about Color -
	Q: What is the color is the leftmost block?
	A: It is yellow.

	Q: What color are the blocks touching the McDonald's block?
	A: There is a red block and a green block that are touching the McDonald's block
5. Confirmation / Error:
	Q: What is the meaning of life?
	A: There is no object that satisfies those parameters, please rephrase and ask again.

	Q: Is there a yellow block touching a green block?
	A: No.

	Q: Can a block fit between the SRI and Nvidia blocks?
	A: Yes.

	'''
	def generate_response(self, user_input_surface, query_object, question_type, answer_set, certainty):

		# Check which state we're in...
		if self.state == self.STATE.INIT:
			pass

		elif self.state == self.STATE.USER_GREET:
			pass

		elif self.state == self.STATE.QUESTION_PENDING:
			# Here, branch on the question type
			# (mostly) completed types:  EXIST, ERROR, IDENT, ATTR_COLOR
			#       EXIST: perhaps use query object to generate desired property
			#       ERROR: perhaps alter boilerplate
			#       IDENT: perhaps use query object to generate desired property
			#       ATTR_COLOR: perhaps use query object to generate desired property
			#       COUNT: perhaps use query object to generate desired property
			#       CONFIRM: consider making more verbose
			# incomplete types: ATTR_ORIENT,
			# empty types: DESCR
			# Need to work on initial pre-processing as well

			# pre-processing
			user_input_surface = lower(user_input_surface)
			user_input_list = english_sentence_to_list(user_input_surface)
			while not user_input_surface[-1].isalpha():
				user_input_surface = user_input_surface[:-1]

			type_surf = "thing"
			pos_types = ["block", "row", "stack", "group", "blocks", "rows", "stacks", "groups"]
			for t in range(0, len(pos_types)):
				if t == user_input_list[t]:
					type_surf = user_input_list[t%4]
					break
			plural_type_surf = type_surf + "s"

			threashold = 0.7

			if question_type == question_type.IDENT:
				# These are the questions like "Which blocks are touching the SRI
				# block?" and "What block is above the Toyota block?"...  This
				# presuposes that the answer exists, but this will be treated very
				# similarly to the exists question, only with more emphasis on the
				# identification and less on the existance

				# PREPROCESSING: --------------------------------------------------
				# first we want to isolate the desired property that we will use for
				# grounding, i.e. "touching the SRI block" or "above the Toyota block"
				des_prop = user_input_surface.split(type_surf)[1].split(' ', 1)[1]
				# NOTE: consider using the query_object, much (MUCH) more reliable
				#       and consistant with the system

				# it is helpful to know how the question was posed so that it can
				# be answered more naturally
				surf_aux = "*"
				if "is" in user_input_list:
					surf_aux = "is"
				elif "are" in user_input_list:
					surf_aux = "are"

				# decide when it will sound natural to ground our response
				use_grounding = not surf_aux == "*"
				# this is kinda an easy way out and somewhat arbitrary but
				# it probably won't sound unnatural

				if len(answer_set) == 0:
				# give an "it doesn't exist" answer
					if len(certainty) == 0 or certainty[0] > threashold:
					# give a certain "it doesn't exist" answer
						if use_grounding:
						# give a certain "it doesn't exist" answer with grounding
							if surf_aux == "is":
								return "There is no " + type_surf + " that is " + des_prop + "."
							elif surf_aux == "are":
								return "There are no " + plural_type_surf + " that are " + des_prop + "."
						else:
						# give a certain "it doesn't exist" answer without grounding
							return "There is no such" + type_surf + "."
					else: # note this is probably not reachable
					# give an uncertain "it doesn't exist answer"
						return "That probably doesn't exist."

				ans_list = entities_to_english_list(answer_set, 'name')

				if len(answer_set) == 1:
				# identify the only answer
					if certainty[0] > threashold:
					# identify the only answer with certainty
						if use_grounding:
						# identify the only answer with certainty and grounding
							return "Just " + ans_list + " is " + des_prop + "."
						else:
						# identify the only answer with certainty and without grounding
							return "Only " + ans_list + "."
					else:
					# identify the only answer with uncertainty
						if use_vp:
						# identify the only answer with uncertainty and grounding
							return "I think only " + ans_list + " is " + des_prop + "."
						else:
						# identify the only answer with uncertainty and without grounding
							return "Probably just " + ans_list + " is."

				else:
				# identify the multiple answers
					if min(certainty) < threashold:
						if max(certainty) > threashold:
						# identify the multiple answers with mixed certainty

							# split the answers by certainty
							cert_lists = entities_split_by_certainty(answer_set, certainty, threashold)
							cert_items = entities_to_english_list(cert_lists[0])
							uncert_items = entities_to_english_list(cert_lists[1])

							if use_grounding:
							# identify the multiple answers with mixed certainty and grounding
								if len(cert_lists[0]) == 1:
									return cert_items.capitalize() + " is " + des_prop + ", but it is less certain for " + uncert_items + "."
								else:
									return cert_items.capitalize() + " are " + des_prop + ", but it is less certain for " + uncert_items + "."
							else:
							# identify the multiple answers with mixed certainty and without grounding
								if len(cert_lists[0]) == 1:
									return cert_items.capitalize() + " does, but it is less certain for " + uncert_items + "."
								else:
									return cert_items.capitalize() + " do, but it is less certain for " + uncert_items + "."
						else:
						# identify the multiple answers uncertainly
							if use_grounding:
							# identify the multiple answers uncertainly with grounding
								return "Possibly " + ans_list + " are " + des_prop + "."
							else:
							# identify the multiple answers uncertainly without grounding
								return "Perhaps " + ans_list + " do."
					else:
					# identify the multiple answers with certainty
						if use_grounding:
						# identify the multiple answers with certainty with grounding
							return ans_list.capitalize() + " are " + des_prop + "."
						else:
						# identify the multiple answers with certainty without grounding
							return capitalize(ans_list) + " do."

			elif question_type == question_type.CONFIRM:
				# These are the questions like "Is the SRI block near the Toyota
				# block?" and "The Toyota block is red, right?"
				# How these will be handled depends very much on what the answer set
				# will give in these cases, I'm not sure. I will assume for now
				# that it just contains a boolean value in these cases

				if len(answer_set) == 0:
				# return certain no
					return "No."
				else:
				# return yes
					if certainty[0] > threashold:
					# return certain yes
						return "Yes."
					else:
					# return uncerain yes
						return "Probably."
			elif question_type == question_type.EXIST:
				# These are the questions like "Is there a block at height 3?"
				# or "Is there a block to the left of the SRI block?"
				# In these cases, the answer set will be empty if the answer is no,
				# and contain the applicable items if it is yes

				# PREPROCESSING: --------------------------------------------------
				# first let's isolate the property that we're looking for, i.e.
				# "at height 3" or "to the left of the SRI block"
				des_prop = user_input_surface.split(type_surf)[1].strip()
				# NOTE: consider using the query_object, much more reliable
				#       and consistant with the system

				# now, decide if we will ground the answer
				use_grounding = user_input_surface.startswith("is there") or user_input_surface.startswith("are there")
				# I think this is a good policy, if the user asks "does there exist
				# a block at height 3" we can respond simply "Yes.", and if there
				# is only one we can name it

				# it is helpful to know how the question was posed so that it can
				# be answered more naturally
				surf_aux = "*"
				if "is" in user_input_list:
					surf_aux = "is"
				elif "are" in user_input_list:
					surf_aux = "are"
				elif "does" in user_input_list:
					surf_aux = "does"
				elif "do" in user_input_list:
					surf_aux = "do"
				# use the list to ensure it only considers full words, i.e.
				# "McDonald's" contains do

				if len(answer_set) == 0:
				# give a negative answer
					if len(certainty) == 0 or certainty[0] > threashold:
					# give a certain negative answer
						if use_grounding:
						# give a certain negative answer with grounding
							if surf_aux == "is":
								return "No, there is not a " + type_surf + " that is " + des_prop + "."
							elif surf_aux == "are":
								return "No, there are no " + plural_type_surf + " that are " + des_prop + "."
						else:
						# give a certain negative answer without grounding
							return "No."
					else:
					# give an uncertain negative answer
						return "Probably not."

				elif len(answer_set) == 1:
				# give a positive answer and identify it

					# identify the entity
					ans_list = entities_to_english_list(answer_set, 'name')
					# ex. "the Nvidia block", "the afsk32313 stack"

					if certainty[0] > threashold:
					# give a certain positive answer and identify it
						if use_grounding:
						# give a certain positive answer w/ grounding and identify it
							if surf_aux == "is":
								return "Yes, the " + type_surf + " that is " + des_prop + " is " + ans_list + "."
							elif surf_aux == "are":
								return "Yes, a " + type_surf + " that is " + des_prop + " is " + ans_list + "."
							# I think this is a good distinction, i.e. for the qs:
							# "Is there a block on the SRI block?" should be answered:
							#       "Yes, the block that is on the SRI block is the Toyota block."
							# "Are there any blocks on the SRI block?" sba:
							#       "Yes, a block that is on the SRI block is the Toyota block."

						else:
						# give a certain positive answer w/out grounding and identify it
							if surf_aux == "do":
								return "Yes, " + ans_list + " is one."
							return     "Yes, it is " + ans_list + "."
							# Similar to above, i.e. for the qs:
							# "Do there exist blocks on the SRI block?" should be answered:
							#       "Yes, the Toyota block is one."
							# "Does there exist a block on the SRI block?" should be answered:
							#       "Yes, it is the Toyota block."
					else:
					# give an uncertain positive answer and identify it
						if use_grounding:
						# give an uncertain positive answer w/ grounding and identify it
							return "Perhaps, the " + ans_list + " may be " + des_prop + "."
						else:
						# give an uncertain positive answer w/out grounding and identify it
							return "Perhaps, the " + ans_list + " might be."

				# there is more than one answer
				else:
				# give a positive answer
					if min(certainty) < threashold:
						if max(certainty) > threashold:
							# give a mixed certainty positive answer

							# split the answers by certainty
							cert_lists = entities_split_by_certainty(answer_set, certainty, threashold)
							cert_items = entities_to_english_list(cert_lists[0])
							uncert_items = entities_to_english_list(cert_lists[1])

							if use_grounding:
							# give a mixed certainty postive answer with grounding
								if len(cert_items) == 1:
									return "It is uncertain.  " + cert_items.capitalize() + " is " + des_prop + ", but it is less sure for " + uncert_items + "."
								else:
									return "It is uncertain.  " + cert_items.capitalize() + " are " + des_prop + ", but it is less sure for " + uncert_items + "."
							else:
							# give a mixed certainty postive answer without grounding
								if len(cert_items) == 1:
									return "It is uncertain.  " + cert_items.capitalize() + " is definately, but it is less sure for " + uncert_items + "."
								else:
									return "It is uncertain.  " + cert_items.capitalize() + " are definately, but it is less sure for " + uncert_items + "."
						else:
						# give an uncertain positive answer
							if use_grounding:
							# give an uncertain postive answer with grounding
								return "I think there are " + plural_type_surf + " that are " + post_there + "."
							else:
							# give an uncertain postive answer without grounding
								return "Yes, there probably " + surf_aux + "."
								# when being this vague we want to echo back the question's language, even though there is no grounding
					else:
					# give a certain positive answer
						if use_grounding:
						# give a certain positive answer with grounding
							return "Yes, there are " + plural_type_surf + " that are " + des_prop + "."
						else:
						# give a certain positive answer without grounding
							return "Yes."
			elif question_type == question_type.ATTR_COLOR:
				# These are the questions like "What is the color of the leftmost
				# block?" or "Which color blocks are touching the Nvidia block"

				# PREPROCESSING: --------------------------------------------------
				# first let's isolate the property that we're looking for, i.e.
				# "the leftmost block" or "touching the Nvidia block"
				des_prop = user_input_surface.split(surf_aux)[1].strip()
				# NOTE: consider using the query_object, much more reliable
				#       and consistant with the system

				# now, decide if we will ground the answer
				use_grounding = user_input_surface.startswith("what color")
				# I'm not sure what a good policy is here, I'll write code even if it's
				# unreachable in case it sounds unnatural and this is changed

				if len(answer_set) == 0:
					# there is no such object
					return "There is no such " + type_surf + "."

				# a simple list of colors
				ans_list_simple = entities_to_color_list(answer_set)
				ans_list_complex = entities_to_english_list(answer_set, 'color')

				if len(answer_set) == 1:
					if certainty[0] > threashold:
					# give a certain answer
						if use_grounding:
						# give a certain answer with grounding
							return "There is a " + ans_list_complex.split()[1] + " that is " + des_prop + "."
						else:
						# give a certain answer without grounding
							return "It is " + ans_list_simple + "."
					else:
						# give an uncertain answer
						if use_vp:
							return "Perhaps there is a " + ans_list_complex.split()[1] + " that is " + des_prop + "."
						else:
							return "It may be " + ans_list_simple + "."

				else:
					# ans_list looks like "red, blue, and green" or "yellow and orange"
					if all(cert > threashold for cert in certainty):
					# give a certain answer
						if use_grounding:
						# give a certain answer with grounding
							return "There is a " + ans_list_complex.split()[1] + " that are " + des_prop + "."
						else:
						# give a certain answer without grounding
							return "They are " + ans_list_simple + "."
					else:
					# give an uncertain answer
						if use_grounding:
						# give an uncertain answer w/ grounding
							return "Perhaps there are a " + ans_list_complex.split()[1] + " that are " + des_prop + "."
						else:
						# give an uncertain answer w/out grounding
							return "They may be " + ans_list_simple + "."
			elif question_type == question_type.ATTR_ORIENT:
				# These are the questions like "What is the orientation of the SRI
				# block?"
				pass
			elif question_type == question_type.COUNT:
				# These are questions like "How many blocks are to the left of the
				# NVidia block" and "How many blocks touch the McDonals block?"
				# If it is just one, we want to say that and name it, otherwise
				# just give a number based on the size of the answer set and
				# adjust for certainty

				# PREPROCESSING: --------------------------------------------------
				# first let's isolate the property that we're looking for, i.e.
				# "to the left of the Nvidia block" or "touch the McDonals block"
				des_prop = user_input_surface.split(type_surf)[1].strip()
				if des_prop.startswith("are") or des_prop.startswith("is"):
					des_prop = des_prop.split(surf_aux)[1].strip()
				# NOTE: consider using the query_object, much more reliable
				#       and consistant with the system

				# now, decide if we will ground the answer
				use_grounding = not user_input_surface.startswith("what is")
				# I think this is workable...  if they ask for what is the number
				# we simply want to give the number, if how many we should elaborate

				# it is helpful to know how the question was posed so that it can
				# be answered more naturally
				surf_aux = "*"
				if "is" in user_input_list:
					surf_aux = "is"
				elif "are" in user_input_list:
					surf_aux = "are"

				if len(answer_set) == 0:
				# say there are none
					if use_grounding:
					# say with grounding there are none
						if surf_aux == "is" or surf_aux == "are":
							return "There are no " + plural_type_surf + " that are " + des_prop + "."
						else:
							return "There are no " + plural_type_surf + " that " + des_prop + "."
					else:
					# say flatly there are none
						return "There are 0."

				ans_list = entities_to_english_list(answer_set, 'name')

				# This part is very much like the identification
				if len(answer_set) == 1:
				# identify the only answer
					if certainty[0] > threashold:
					# identify the only answer with certainty
						if use_grounding:
						# identify the only answer with certainty and grounding
							if surf_aux == "is" or surf_aux == "are": # !!!! are we active or passive voice !!!!
								return "Just " + ans_list + " is " + des_prop + "."
							else:
								return "Just " + ans_list + " " + des_prop + "."
						else:
						# identify the only answer with certainty and without grounding
							return "Only one, " + ans_list + "."
					else:
					# identify the only answer with uncertainty
						if use_grounding:
						# identify the only answer with uncertainty and grounding
							if surf_aux == "is" or surf_aux == "are":
								return "Probably only " + ans_list + " is " + des_prop + "."
							else:
								return "Probably only " + ans_list + " " + des_prop + "."
						else:
						# identify the only answer with uncertainty and without grounding
							return "Probably " + ans_list + " is the only one."

				# give the number AND list them out, also very much like identification
				elif len(answer_set) < 4:
				# identify the reasonably enumerable answers
					if certainty[0] > threashold:
					# identify the reasonably enumerable answers with certainty
						if use_grounding:
						# identify the reasonably enumerable answers with certainty and grounding
							if surf_aux == "is" or surf_aux == "are":
								return "There are " + str(len(ans_set)) + " that are " + des_prop + ": " + ans_list + "."
							else:
								return "There are " + str(len(ans_set)) + " that " + des_prop + ": " + ans_list + "."
						else:
						# identify the reasonably enumerable answers with certainty and without grounding
							return "There are " + str(len(ans_set)) + ": " + ans_list + "."
					else:
					# identify the reasonably enumerable answers with uncertainty
						if use_grounding:
						# identify the reasonably enumerable answers with uncertainty and grounding
							if surf_aux == "is" or surf_aux == "are":
								return "There are probably " + str(len(ans_set)) + " that are " + des_prop + ": " + ans_list + "."
							else:
								return "There are probably " + str(len(ans_set)) + " that " + des_prop + ": " + ans_list + "."
						else:
						# identify the reasonably enumerable answers with uncertainty and without grounding
							return "Probably " + ans_list + " is the only one."

				else:
				# give the number
					if all(cert > threashold for cert in certainty):
					# give the number, with certainty
						if use_grounding:
						# give the number certaintly with grounding
							if surf_aux == "is" or surf_aux == "are":
								return "There are " + str(len(ans_set)) + plural_type_surf + " that are " + des_prop + "."
							else:
								return "There are " + str(len(ans_set)) + plural_type_surf + " that " + des_prop + "."
						else:
						# give the number certaintly without grounding
							return "There are " + str(len(ans_set)) + "."
					else:
					# give the number, with uncertainty
						if use_grounding:
						# give the number uncertaintly with grounding
							if surf_aux == "is" or surf_aux == "are":
								return "There may be " + str(len(ans_set)) + plural_type_surf + " that are " + des_prop + "."
							else:
								return "There may be " + str(len(ans_set)) + plural_type_surf + " that " + des_prop + "."
						else:
						# give the number uncertaintly without grounding
							return "Perhaps there are " + str(len(ans_set)) + "."
			elif question_type == question_type.ERROR:
				return "There is no object that satisfies those parameters, please rephrase and ask again."
			elif question_type == question_type.DESCR:
				pass

		elif self.state == self.STATE.USER_BYE:
			pass

		elif self.state == self.STATE.END:
			pass


	# The following are functions used in generate_response -------------------------------------------

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

	# use this when we only want colors, without types or specifier
	def entities_to_color_list(ents):
		# similar to entities_to_english_list here
		types = map(lambda x: lower(x.type_structure[:-1][0]), ents)
		cols = map(operator.attrgetter('color'), ents)
		cols = list(dict.fromkeys(cols))
		uniform_type = all(x == type[0] for x in type)

		# there's only one answer
		if len(cols) == 1:
			return cols[0]

		if len(cols) == 2:
			return cols[0] + " and " + cols[1]

		else:
			out = ""
			for i in range(0, (len(cols) - 1)):
				out += cols[i] + ", "
			out += " and " + cols[-1]
			return out

	# returns two lists divided by the certainty about each entity
	# used in mixed certainty answers
	# assumes answers are already sorted by certainty
	def entities_split_by_certainty(ents, certainty, threashold):
		out = []
		for i in range(0, len(ents)):
			if certainty[i] < threashold:
				out.append(ents[:i])
				out.append(ents[i:])
				return out
		out.append(ents)
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

	# -------------------------------------------------------------------------------------------------

def main():
	manager = HCIManager(debug_mode=True)
	manager.load_as_text(["Test message 1", "Test message 2", "Test message 3", "Test message 4", "Test message 5"])
	manager.start()
