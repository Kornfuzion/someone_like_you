from datetime import datetime
import requests
import config
import datetime
import pynder
import face_recognition
from match import loadImageFromFile
from urllib import request, error
from shutil import copyfile

requests.packages.urllib3.disable_warnings()  # Find way around this...

session = pynder.Session(config.FACEBOOK_AUTH_TOKEN)

swiped_dir = 'swiped'
liked_dir = 'liked'
disliked_dir = 'disliked'

target_face = face_recognition.load_image_file("ellen.jpg")
# We know our target image only has 1 face in it, so grab the first index
target_face_encoding = face_recognition.face_encodings(target_face)[0]

distance_thresh = 0.7
large_facial_distance = 10.0

def downloadImage(url, path):
    try:
        request.urlretrieve(url, path)
    except error.URLError:
        print("woops, tried to download a JPG when it was another file format. Eh.")
        print(url)
    except ConnectionResetError:
        print("Guess the connection died on this one...")

def log(msg):
    print('[' + str(datetime.datetime.now()) + ']' + ' ' + msg)

def like_user(user):
    profile_photo = user.photos[0]

    photo_path = swiped_dir + '/' + user.name + '.jpg'
    downloadImage(profile_photo, photo_path)
    try:
        img = face_recognition.load_image_file(photo_path)
    except FileNotFoundError:
        return False

    unknown_face_encoding = face_recognition.face_encodings(img)
    print('evaluating ' + user.name)
    facial_distance = large_facial_distance

    # If there's more than 1 face in the photo, compare all encodings against the target
    if len(unknown_face_encoding) > 1:
        for encoding in unknown_face_encoding:
            dist = face_recognition.face_distance(target_face_encoding, encoding)
            if dist < facial_distance:
                facial_distance = dist
    else:
        facial_distance = face_recognition.face_distance(target_face_encoding, unknown_face_encoding)
    
    print(facial_distance)
    
    if facial_distance <= distance_thresh:
        liked_path = liked_dir + '/' + str(facial_distance[0]) + '.jpg'
        copyfile(photo_path, liked_path)
        return True
    else:
        disliked_path = disliked_dir + '/' + str(facial_distance[0]) + '.jpg'
        copyfile(photo_path, disliked_path)
        return False

def remaining_swipes():
    return session.likes_remaining

def handle_likes():
    users = session.nearby_users()
    for u in users:
        try:
            if remaining_swipes() == 0:
                log('Out of swipes, exiting.')
                break
            else:
                try:
                    if like_user(u) == True:
                        u.like()
                        log('Liked ' + u.name)
                    else:
                        u.dislike()
                        log('Disliked ' + u.name)
                except ValueError:
                    break
                except pynder.errors.RequestError:
                    break
        except ValueError:
            break
        except pynder.errors.RequestError:
            break

while True:
    handle_likes()
