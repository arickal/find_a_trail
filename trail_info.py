# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import gpxpy
import pandas as pd
import numpy as np
import os
import requests
import json
from geopy import distance as gdist
from geopy import Point

def send_with_attach(fromaddr, toaddr, password, subject, body, filename):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
    body = body
    msg.attach(MIMEText(body, 'plain'))
    attachment = open(filename, "rb")
    p = MIMEBase('application', 'octet-stream')
    p.set_payload((attachment).read())
    encoders.encode_base64(p)
    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    msg.attach(p)
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(fromaddr, password)
    text = msg.as_string()
    s.sendmail(fromaddr, toaddr, text)
    s.quit()

def getSlopeStats(gpx):
    try:
        points = []
        for seg in gpx.tracks[0].segments:
            points = points + seg.points
        gd_points = [ Point("%s %s"%(p.latitude, p.longitude)) for p in points ]
        start = gd_points[:-1]
        end = gd_points[1:]
        h_move = [ gdist.distance(s, e).meters for (s,e) in zip(start, end)]
        
        start_v = points[:-1]
        end_v = points[1:]
        v_move = [ e.elevation - s.elevation for (s,e) in zip(start_v, end_v)]
        
        hov = [ 1.0*v/(h+0.01) for (h,v) in zip(h_move, v_move) if v > 0]
        
        ahov = np.array(hov)
        
        return ahov.mean(), ahov.std()
    except:
        return None, None
    
def callGoogleMapsApi(origin, dest, api_key):
    url = os.environ['GOOGLE_MAP_API_URL']
    try:
        res = requests.get(url%(origin, dest, api_key))
        body = json.loads(res.content)
        duration = body['routes'][0]['legs'][0]['duration']['text']
        end_address = body['routes'][0]['legs'][0]['end_address']
        distance = body['routes'][0]['legs'][0]['distance']['text']
        with open( 'gmap_response/%s_%s'%(origin, dest),'w' ) as f:
            f.write( str(res.content) )
        return distance, duration, end_address
    except:
        return None, None, None

def read_gpx(path):
    
    from subprocess import Popen, PIPE

    if not os.path.exists(path):
        raise FileNotFoundError(path)
    p = Popen(['gpxinfo', path], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    dic = {}
    
    for line in str(output).split('\\n'):
        if ': ' not in line:
            continue
        dic[ line.split(': ')[0].strip() ] = line.split(': ')[1].strip()
        
    gpxf = open(path, 'r')
    
    try:
        gpx = gpxpy.parse(gpxf)
        
        firstp = gpx.tracks[0].segments[0].points[0]
        origin = os.environ['START_POINT'] # for example, P7
        dest = "%f,%f"%(firstp.latitude, firstp.longitude)
        
        distance, duration, dest_addr = callGoogleMapsApi(origin, dest, os.environ['MY_GCP_API_KEY'])
            
        dic['p7_distance'] = distance
        dic['p7_duration'] = duration
        dic['gmap_dest_address'] = dest_addr
        
        slope_mean, slope_std = getSlopeStats(gpx)
        
        dic['up_slope_mean'] = slope_mean
        dic['up_slope_std'] = slope_std
        
        dic['num_tracks'] = len(gpx.tracks)
        
        countp = 0
        for track in gpx.tracks:
            for seg in track.segments:
                countp = countp + len(seg.points)
                
        dic['num_points_0'] = len(gpx.tracks[0].segments[0].points)
        dic['num_points_total'] = countp
        
        return dic
    except:
        return dic

if __name__ == "__main__":

    scrapy_out = os.environ['GPX_FOLDER']
    password = os.environ['MY_GMAIL_PASSWORD']
    fromaddr = os.environ['MY_GMAIL_ADDRESS']
    toaddr = os.environ['MY_WORK_EMAIL']

    rows = []
    num_gpx = len(os.listdir(scrapy_out))
    for idx, file in enumerate(os.listdir(scrapy_out)):
        
        if not file.endswith('.gpx'):
            continue
        
        real_path = os.path.join( scrapy_out, file )
        print("%4d/%4d %s"%(idx, num_gpx, file))
        dic = read_gpx(real_path) 
        dic['Name'] = file
        rows = rows + [ dic ]

    pdf = pd.DataFrame(rows)
    trails_file = 'trails.csv'
    pdf.to_csv(trails_file, encoding='utf-8', index=False)
    send_with_attach(fromaddr, password, toaddr, 'trails info', 'email body', trails_file)
    print('complete sending trail info')