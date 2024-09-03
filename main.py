import speech_recognition as sr
from openai import OpenAI
import pyttsx3
import os

status = "on"
client = OpenAI(base_url="http://localhost:3333/v1", api_key="not-needed")
recognizer = sr.Recognizer()
language = "es-ES" # Set language, en-US / es-ES

def speak(text):
    print(text)
    pyttsx3.speak(text)

def speech_to_text():
    with sr.Microphone() as source:
        print("Adjusting settings...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        os.system("cls")
        print("Listening...")
        recorded_audio = recognizer.listen(source, timeout=5)
        try:
            text = recognizer.recognize_google(recorded_audio, language=language)
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

def task(request):
    if "search" in request:
        print("buscar")

while status == "on":
    try:
        text = speech_to_text()
        request = ai_resoomer_request(text)
        task(request)
    except KeyboardInterrupt:
        status = "off"
        print("[!] Exiting...")

if status == "off":
    exit()