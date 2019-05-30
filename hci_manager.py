import enum
from gcs_micstream import ResumableMicrophoneStream
from google.cloud import speech
import sys
import re
import requests
from threading import Thread, RLock
import time


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
		# Audio recording parameters
		sample_rate = 16000
		chunk_size = int(sample_rate / 10)  # 100ms

		client = speech.SpeechClient()
		config = speech.types.RecognitionConfig(
		    encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
		    sample_rate_hertz=sample_rate,
		    language_code='en-US',
		    max_alternatives=1,
		    enable_word_time_offsets=True,
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

manager = HCIManager()
manager.start()