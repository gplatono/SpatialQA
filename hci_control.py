#!/usr/bin/env python

# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google Cloud Speech API sample application using the streaming API.
NOTE: This module requires the additional dependency `pyaudio`. To install
using pip:
    pip install pyaudio
Example usage:
    python transcribe_streaming_indefinite.py
"""

# [START speech_transcribe_infinite_streaming]
from __future__ import division

import time
import re
import sys
import requests
from threading import *

from google.cloud import speech

import pyaudio
from six.moves import queue

# Audio recording parameters
STREAMING_LIMIT = 55000
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms


phrases = {"Greeting": "Hello! Nice to meet you.",
            "Intro": "My name is David.",
            "Name": "It's David.",
            "About": "I'm an avatar for the blocks world.",
            "Bye": "Good bye!",
            "HowAreYou": "I'm good, thank you! How about you?",
            "RespYes": "Yes.",
            "RespNo": "No.",
            "Alright": "Alright.",
            "Missed": "Sorry, can you say it again?",
            "Ack1": "Understood.",
            "Ack2": "Ok."}

def get_current_time():
    return int(round(time.time() * 1000))


def duration_to_secs(duration):
    return duration.seconds + (duration.nanos / float(1e9))


class ResumableMicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk_size):
        self._rate = rate
        self._chunk_size = chunk_size
        self._num_channels = 1
        self._max_replay_secs = 5

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = get_current_time()

        # 2 bytes in 16 bit samples
        self._bytes_per_sample = 2 * self._num_channels
        self._bytes_per_second = self._rate * self._bytes_per_sample

        self._bytes_per_chunk = (self._chunk_size * self._bytes_per_sample)
        self._chunks_per_second = (
                self._bytes_per_second // self._bytes_per_chunk)

    def __enter__(self):
        self.closed = False

        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk_size,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, *args, **kwargs):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            if get_current_time() - self.start_time > STREAMING_LIMIT:
                self.start_time = get_current_time()
                break
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


def listen_print_loop(responses, stream):
    """Iterates through server responses and prints them.
    The responses passed is a generator that will block until a response
    is provided by the server.
    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.
    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    responses = (r for r in responses if (
            r.results and r.results[0].alternatives))

    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        top_alternative = result.alternatives[0]
        transcript = top_alternative.transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)
        else:
            #print("you said: " + transcript + overwrite_chars)

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                stream.closed = True
                break


            user_line = transcript.lower()
            print ("you said: " + user_line)
            NAME_FLAG = GREET_FLAG = HOW_ARE_YOU_FLAG = USER_INTRO_FLAG = THANK_FLAG = VOC_FLAG = END_FLAG = DAVID_FLAG = ABOUT_FLAG = NVM_FLAG = 0
            if "hello" in user_line or "hi" in user_line or "greetings" in user_line or "hey" in user_line:
                GREET_FLAG = 1
            if re.search("^.*how.*going.*$", user_line) is not None or re.search("^.*how.*doing.*$", user_line) is not None or re.search("^.*how.*you.*$", user_line) is not None \
             or re.search("^.*how.*do$", user_line) is not None or re.search("^.*how.*day$", user_line) is not None:                
                HOW_ARE_YOU_FLAG = 1
            if re.search("^I.*am.*", user_line) is not None or re.search("^my.*name.*", user_line) is not None:
                USER_INTRO_FLAG = 1            
            if "thank" in user_line:
                THANK_FLAG = 1
            if "david" == user_line:
                VOC_FLAG = 1
            elif "david" in user_line:
                DAVID_FLAG = 1
            if "bye" in user_line or "goodbye" in user_line or "see you" in user_line or "that's it" in user_line:
                END_FLAG = 1
            if re.search("^.*tell.*yourself.*$", user_line) is not None or re.search("^.*who.*you.*$", user_line) is not None or re.search("^.*what.*you.*do.*$", user_line) is not None:
                ABOUT_FLAG = 1
            if "nevermind" in user_line:
                NVM_FLAG = 1
            if re.search("^.*what.*name.*$", user_line):
                NAME_FLAG = 1
            response = ""
            if GREET_FLAG == 1:
                response += phrases["Greeting"]
                if DAVID_FLAG == 0:
                    response += " " + phrases["Intro"]
            elif END_FLAG == 1:
                response += phrases["Bye"]
            elif HOW_ARE_YOU_FLAG == 1:
                response += phrases["HowAreYou"]
            elif THANK_FLAG == 1:
                response += phrases["Alright"]
            elif ABOUT_FLAG == 1:
                response += phrases["About"]
            elif NVM_FLAG == 1:
                response += phrases["Ack2"]
            elif NAME_FLAG == 1:
                response += phrases["Name"]
            #else:
            #    response += phrases["Missed"]

            print ("Avatar's response: " + response)
            req = requests.get('http://ec2-35-162-37-211.us-west-2.compute.amazonaws.com:8080/avatar_control/?say=' + response)
            print ("STATUS: " + str(req.status_code))

            
            num_chars_printed = 0

def mic_loop():
    client = speech.SpeechClient()
    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code='en-US',
        max_alternatives=1,
        enable_word_time_offsets=True,
         enable_automatic_punctuation=True)
    streaming_config = speech.types.StreamingRecognitionConfig(config=config, interim_results=True)

    mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)

    with mic_manager as stream:
        while not stream.closed:
            audio_generator = stream.generator()
            requests = (speech.types.StreamingRecognizeRequest(audio_content=content)
                for content in audio_generator)

            responses = client.streaming_recognize(streaming_config, requests)
            # Now, put the transcription responses to use.
            listen_print_loop(responses, stream)

def main():
    

    print('Say "Quit" or "Exit" to terminate the program.')

    thread = Thread(target = mic_loop)
    thread.start()
    thread.join()
    #mic_loop()

if __name__ == '__main__':
    main()
# [END speech_transcribe_infinite_streaming]