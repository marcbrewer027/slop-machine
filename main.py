class SrtTimestamp:
    def __init__(self):
        self.minute = 0
        self.second = 0
        self.ms = 0
        self.totalms = 0
    
    def __repr__(self) -> str:
        minStr = f"{self.minute}"
        secStr = f"{self.second}"
        msStr = f"{self.ms}"
    
        if len(minStr) < 2:
            minStr = "0" + minStr
        
        if len(secStr) < 2:
            secStr = "0" + secStr
        
        if len(msStr) == 1:
            msStr = "00" + msStr
        elif len(msStr) == 2:
            msStr = "0" + msStr
        
        return f"00:{minStr}:{secStr}.{msStr}"
    
    def add(self, n):

        self.totalms += n 
    
        self.ms += n
        while self.ms > 999:
            self.ms -= 1000
            self.second += 1
            while self.second > 59:
                self.second -= 60
                self.minute += 1
            
        return self
    
class Subtitle:
    def __init__(self, filename, capN, text, startTime, endTime):
        self.filename = filename
        self.capN = capN
        self.text = text
        self.startTime = startTime
        self.endTime = endTime
    
    def __repr__(self):
        return f"{self.capN}\n{self.startTime} --> {self.endTime}\n{self.text}\n\n"
    
import copy
import subprocess
from gtts import gTTS
from mutagen.mp3 import MP3
from pydub import AudioSegment
import os
import praw
import random
from math import ceil
def text_to_speech(text, directory, prefix):
    """
    Converts the provided text to speech, saves it as an MP3 file, 
    and names the file after the playback duration in milliseconds.

    Parameters:
    text (str): The text to convert to speech.
    directory (str): The directory where the MP3 file will be saved.
    prefix (str): The prefix for the filename.
    """
    try:
        tts = gTTS(text)
    
        temp_file_location = os.path.join(directory, "temp.mp3")
    
        tts.save(temp_file_location)
    
        audio = MP3(temp_file_location)
        duration_milliseconds = ceil( int(audio.info.length * 1000) / 1.13 )
    
        audio = AudioSegment.from_mp3(temp_file_location)
    
        faster_audio = audio.speedup(playback_speed=1.15)
    
        new_file_location = os.path.join(directory, f"{prefix}_{duration_milliseconds}.mp3")
        faster_audio.export(new_file_location, format="mp3")
    
        os.remove(temp_file_location)
    
        print(f"Text to speech saved at {new_file_location}")
    
        audio_info = {
            'duration': duration_milliseconds,
            'filename': f"{prefix}_{duration_milliseconds}.mp3",
        }
    
        return audio_info
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
def get_random_hot_post():
    """
    Fetches a random hot post from the r/amitheasshole subreddit.

    Returns:
    dict: A dictionary containing the title, author, and body text of the post.
    """

    ### PUT REDDIT API INFO HERE

    reddit = praw.Reddit(client_id='[YOUR CLIENT ID]',
                         client_secret='[YOUR CLIENT SECRET]',
                         user_agent='[YOUR USER AGENT]')
                        
    subreddit = reddit.subreddit('amitheasshole')

    hot_posts = list(subreddit.hot(limit=50))

    random_post = random.choice(hot_posts)

    post_info = {
        'title': random_post.title,
        'author': random_post.author.name,
        'body': random_post.selftext
    }

    return post_info

if __name__ == "__main__":
    post = get_random_hot_post()
    bodySentences = post['body'].split(".")

    totalLength = SrtTimestamp()
    captions = []
    g = open("audio.txt", "x")

    current = text_to_speech(post['title'].replace("AITA", "am I the asshole"), ".", "0")

    captions.append(Subtitle(current['filename'], 1, post['title'], copy.copy(totalLength), copy.copy(totalLength.add(current['duration']))))
    g.write(f"file '{current['filename']}'\n")  

    current = text_to_speech(f"from {post['author']} on reddit", ".", "1")
    g.write(f"file '{current['filename']}'\n") 

    captions.append(Subtitle(current['filename'], 2, f"from {post['author']} on reddit", copy.copy(totalLength), copy.copy(totalLength.add(current['duration']))))

    n=2
    for sentence in bodySentences:
        sentence = sentence.replace("\n"," ")
        try:
            current = text_to_speech(sentence.replace("AITA", "am I the asshole"), ".", f"{n}")
            g.write(f"file '{current['filename']}'\n")
            captions.append(Subtitle(current['filename'], n+1, sentence+".", copy.copy(totalLength), copy.copy(totalLength.add(current['duration']))))
        
            n += 1
        except Exception as e:
            print(f"An error occurred: {e}")
    g.close()

    f = open("captions.srt", "x")
    for item in captions:
        f.write(str(item))
    f.close()

    command = [
        'ffmpeg',
        '-f',
        'concat',
        '-i',
        'audio.txt',
        '-acodec',
        'copy',
        'combined_audio.mp3'
    
    ]

    subprocess.run(command, check=True)

    for item in captions:
        os.remove(item.filename)
    os.remove("audio.txt")

    ### REPLACE THE FILES IN THIS LIST WITH THE FILES YOU WISH TO HAVE OVERLAYED WITH GAMEPLAY AND AUDIO

    clips = ['gameplay.mp4', 'gameplay1.mp4']

    command = [
        'ffmpeg',
        '-i', random.choice(clips),
        '-i', 'combined_audio.mp3',
        '-vf', "subtitles=captions.srt:force_style='Alignment=10'",
        '-c:v', 'libx264', '-crf', '23',
        '-c:a', 'aac', '-strict', 'experimental',
        '-map', '0:v:0', '-map', '1:a:0',
        '-t', str(captions[-1].endTime.add(1000)),
        f'{post["title"].replace("?","")}.mp4'
    ]

    subprocess.run(command, check=True)

    os.remove("captions.srt")
    os.remove("combined_audio.mp3")

    print(f'{post["title"].replace("?","")}.mp4 saved in folder.')
