import speech_recognition as sr
from openai import OpenAI
import webbrowser
import sys
import threading
import time
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from youtubesearchpython import VideosSearch
import pyttsx3
import os

def create_image():
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((width//4, height//4, width*3//4, height*3//4), fill=(0, 255, 0))
    return image

def on_quit(icon, item):
    icon.stop()

spotify_client_id = 'CLIENT_ID'
spotify_client_secret = 'CLIENT_SECRET'
spotify_redirect_uri = 'http://localhost:8888/callback/'
spotify_scope = 'user-modify-playback-state,user-read-playback-state'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=spotify_client_id,
                                               client_secret=spotify_client_secret,
                                               redirect_uri=spotify_redirect_uri,
                                               scope=spotify_scope))
status = "on"
client = OpenAI(base_url="http://localhost:3333/v1", api_key="not-needed")
recognizer = sr.Recognizer()
language = "es-ES" # Set language, en-US / es-ES
with sr.Microphone() as source:
    os.system("cls")
    print("Adjusting settings...")
    recognizer.adjust_for_ambient_noise(source, duration=1)

def speak(text):
    print(text)
    pyttsx3.speak(text)

def speech_to_text():
    with sr.Microphone() as source:
        os.system("cls")
        print("Listening...")
        recorded_audio = recognizer.listen(source)
        try:
            #text = recognizer.recognize_google(recorded_audio, language=language)
            text = recognizer.recognize_assemblyai(recorded_audio, language=language)
            print(text)
            return text
        except sr.UnknownValueError:
            print("[-] Google Speech Recognition could not understand the audio.")
        except sr.RequestError:
            print("[-] Could not request results from Google Speech Recognition service.")
        except Exception as ex:
            print(f"[-] Error during recognition: {ex}")

def ai_resoomer_request(text):
    completion = client.chat.completions.create(
        model="local-model",
        messages=[
            {"role": "system", "content": "quiero que a partir de ahora me resumas lo máximo posible los siguientes mensajes, aquí va un ejemplo: 'Oye, me gustaría que me pongas una canción de ACDC, por ejemplo Thunderstrack.' este texto entre comillas, me gustaría que lo resumieses en: 'Play Thunderstrack ACDC', este es un ejemplo, no añadas más información de la que se te ha proporcionado en el mensaje, debes de resumir en distintos formatos dependiendo de la tarea que se quiera ejecutar, en caso de que el texto trate de buscar un video en youtube, tan solo tienes que resumirlo de la siguiente manera: 'Youtube <nombre del canal> <titulo del video>' en caso de no tener un video en especifico, solo inserta el nombre del canal, y en caso de no tener el nombre del canal, solo pon el titulo del video, en caso de que el mensaje trate sobre buscar información en internet, debes de resumirlo de la siguiente manera: 'Search <información a buscar>' donde en información a buscar vas a poner un resumen de lo que quieres que se busque utilizando palabras clave para encontrar el mejor resultado en google. Para cualquier otro tema del que no haya especificado, debes de realizarlo de la manera más similar posible a la estructura que te he proporcionado. En caso de que se solicite traducir algo debes de traducirlo por tu cuenta y devolver simplemente el texto en el idioma solicitado sin añadir nada más al prompt"},
            {"role": "user", "content": text}
        ],
        temperature=0.7,
    )
    return completion.choices[0].message.content

def ai_answer(text):
    completion = client.chat.completions.create(
        model="local-model",
        messages=[
            {"role": "system", "content": "Tu nombre es Jim. Me gustaría que a partir de ahora seas un asistente personal al estilo JARVIS de Iron Man, debes de responder de forma natural, con frases claras, sencillas y directas, como si fueses una persona que trabajase para mi, pero también como si fueses una persona de confianza que ha trabajado para mi durante décadas, literalmente un asistente personal, como su nombre indica, tienes conocimientos sobre prácticamente todos los temas que puedas hablar. No puedes preguntarme sobre si puedes hacer cosas físicas dado que no puedes olvidar que eres un asistente virtual. Recuerda que tienes que responder con oraciones claras y sencillas, si te pregunto si puedes ayudarme con un tema, debes de responder preguntándome sobre que tema me gustaría hablar, en cualquier otro caso, debes de seguir una norma similar, tienes que parecerte lo máximo posible a JARVIS, el cual responde de forma humana. Si se te pide reproducir una canción, tan solo di, reproduciendo <cancion> de <artista> y no preguntes nada más."},
            {"role": "user", "content": text}
        ],
        temperature=0.7,
    )
    return completion.choices[0].message.content

def search_and_open_video(query):
    videos_search = VideosSearch(query, limit=1)
    result = videos_search.result()

    if result['result']:
        video_url = result['result'][0]['link']
        print(video_url)
        webbrowser.open(video_url)
    else:
        speak("Could not find the video")

def play_spotify(query):
    # CREATE AN APP FROM THE Spotify Developers Website
    # NOTE: SPOTIFY PREMIUM IS REQUIRED
    # SET THE RedirectURI to http://localhost:8888/callback/
    track_results = sp.search(q=query, type='track', limit=1)
    playlist_results = sp.search(q=query, type='playlist', limit=1)

    track_items = track_results.get('tracks', {}).get('items', [])
    playlist_items = playlist_results.get('playlists', {}).get('items', [])

    if track_items:
        track_uri = track_items[0]['uri']
        print(f"Reproduciendo canción: {track_items[0]['name']} de {track_items[0]['artists'][0]['name']}")
        uris = [track_uri]
    elif playlist_items:
        playlist_uri = playlist_items[0]['uri']
        print(f"Reproduciendo lista de reproducción: {playlist_items[0]['name']}")
        uris = [playlist_uri]
    else:
        print("No se encontró ni una canción ni una lista de reproducción con ese nombre.")
        return
    
    devices = sp.devices()['devices']

    current_playback = sp.current_playback()
    
    if current_playback is None or not current_playback.get('is_playing'):
        device_id = devices[0]['id']
        sp.start_playback(device_id=device_id, uris=uris)

    device_id = current_playback['device']['id']

    sp.start_playback(device_id=device_id, uris=uris)

def task(request):
    request = request.split()
    if "Search" in request:
        request.pop(0)
        request = ' '.join(request)
        request = request.replace('"', '')
        request = request.replace("'", "")
        url = f"https://www.google.com/search?q={request.replace(' ', '+')}"
        speak("Opening Web browser")
        webbrowser.open(url)
    #elif "Youtube" or "youtube" in request: 
    #    search_and_open_video(request)
    elif "Play" in request and "Youtube" not in request or "spotify" in request or "Spotify" in request:
        play_spotify(request)

def main():
    try:
        while True:
            text = None

            while text == None or text == "" or text == " ":
                text = speech_to_text()
                try:
                    if not "Jim" or "jim" in text.split():
                        text = None
                except AttributeError as e:
                    print("")
            answer = ai_answer(text)
            request = ai_resoomer_request(text)
            speak(answer)
            task(request)

    except KeyboardInterrupt:
        status = "off"
        print("[!] Exiting...")

    if status == "off":
        exit()

def setup(icon):
    icon.visible = True
    task_thread = threading.Thread(target=main)
    task_thread.daemon = True
    task_thread.start()

if __name__ == '__main__':
    menu = Menu(
        MenuItem('Exit', on_quit)
    )

    icon = Icon("test", create_image(), "Jim Assistant", menu)

    icon.run(setup)