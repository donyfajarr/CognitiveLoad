from datetime import datetime
from django.shortcuts import render
from firebase_admin import db
from firebase import firebase
import json
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import pandas as pd
from django.views.decorators import gzip
from django.http import StreamingHttpResponse
import cv2
import threading

firebase = firebase.FirebaseApplication('https://cognitive-load-default-rtdb.asia-southeast1.firebasedatabase.app/', authentication=None)


def emg(request):
    return render(request, 'emg.html',{

    })

def heartrate(request):
    return render(request, 'heartrate.html',{
    })


def temp(request):
    return render(request, 'temp.html',{

    })




#to capture video class
class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(1)
        (self.grabbed, self.frame) = self.video.read()
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.video.release()

    def get_frame(self):
        image = self.frame
        _, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def update(self):
        while True:
            (self.grabbed, self.frame) = self.video.read()

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@gzip.gzip_page
def video_feed(request):
    # Serve the video stream as a separate endpoint
    try:
        cam = VideoCamera()
        return StreamingHttpResponse(gen(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        pass

def dashboard(request):
    return render(request, 'dashboard.html')

# def datapenelitian(request):
#     data = firebase.get('/Data', None)
#     listdata = []
#     for key in data :
#         listkosong = []
#         value = data[key]
#         BPM = value["BPM"]
#         Temp = value["Temp"]
#         listkosong.append(key)
#         listkosong.append(BPM)
#         listkosong.append(Temp)
#         listdata.append(listkosong)

#     return render(request, 'tabeldata.html', {
#         'listdata': listdata,
#     })


# def tes_upload(request):
#     if request.method == 'POST':
#         # READ UPLOADED FILE
#         nama = request.POST['nama']
#         myxlsx = request.FILES['myxlsx']
#         myjson = request.FILES['myjson']
#         # READ AS A DATAFRAME
#         dfeeg = pd.read_excel(myxlsx, index_col='Waktu')
#         dfjson = pd.read_json(myjson, orient='index')
#         # SET INDEX FOR MERGING
#         dfjson.index = pd.to_datetime(dfjson.index, format='%A, %B %d %H:%M:%S')
#         dfeeg.index = dfeeg.index.strftime('%H:%M:%S')
#         dfjson.index = dfjson.index.strftime('%H:%M:%S')
#         # MERGE
#         result_df = pd.merge(dfeeg, dfjson, how='left', left_index=True, right_index=True)
#         # AUTOFILLED FUNCTION
#         result_df['BPM'] = result_df['BPM'].fillna(method='ffill')
#         result_df['Temp'] = result_df['Temp'].fillna(method='ffill')
#         result_df['BPM'] = result_df['BPM'].fillna(method='bfill')
#         result_df['Temp'] = result_df['Temp'].fillna(method='bfill')
#         # EXPORT CSV MERGE
#         file = nama + ".csv"
#         result_df.to_csv(file)


#         bpm = result_df['BPM'].values.tolist()
#         time = result_df['BPM'].index.tolist()
#         temp = result_df['Temp'].values.tolist()
#         delta = (result_df['Delta'].values.tolist())
#         theta = (result_df['Theta'].values.tolist())
#         lowalpha = (result_df['Low-Alpha'].values.tolist())
#         highalpha = (result_df['High-Alpha'].values.tolist())
#         lowbeta = (result_df['Low-Beta'].values.tolist())
#         highbeta = (result_df['High-Beta'].values.tolist())
#         lowgamma = (result_df['Low-Gamma'].values.tolist())
#         midgamma = (result_df['Mid-Gamma'].values.tolist())
#         attention = (result_df['Attention'].values.tolist())
#         relaxation = (result_df['Relaxation'].values.tolist())
    
#         return render(request, 'upload.html', {
#             'nama' : nama,
#             'bpm' : json.dumps(bpm),
#             'time' : json.dumps(time),
#             'temp' : json.dumps(temp),
#             'delta' : json.dumps(delta),
#             'theta' : json.dumps(theta),
#             'lowalpha' : json.dumps(lowalpha),
#             'highalpha' : json.dumps(highalpha),
#             'lowbeta' : json.dumps(lowbeta),
#             'highbeta' : json.dumps(highbeta),
#             'lowgamma' : json.dumps(lowgamma),
#             'midgamma' : json.dumps(midgamma),
#             'attention' : json.dumps(attention),
#             'relaxation' : json.dumps(relaxation),
#             'avgbpm' : round((sum(bpm)/len(bpm))),
#             'highbpm' : max(bpm),
#             'lowbpm' : min(bpm),
#             'avgtemp' : round((sum(temp)/len(temp))),
#             'hightemp' : max(temp),
#             'lowtemp' : min(temp),
#         })
#     else:
#         return render(request, 'upload.html')