import cv2
import mediapipe as mp
import numpy as np
import time
import json     #讓後端可以做資料庫
import pygame   #做音效
import math
#import serial   #可以跟Arduino做結合

pygame.init()         #音效初始化
pygame.mixer.init()

###############################影像來源設定###############################################
 


cam = cv2.VideoCapture(1)     #現在想用webcam的攝影機，所以外接 我這台電腦外接攝影機是在鏡頭1編號的位置
#cam = cv2.VideoCapture("POSE1.mp4")    #改用影片去測
#frame_counter = 0

\
mppose = mp.solutions.pose
mpdraw = mp.solutions.drawing_utils
poses = mppose.Pose()
h = 0          #鏡頭長
w = 0          #鏡頭寬

#Arduino Comport
#ser = serial.Serial("COM3", 9600)

start_time = 0
status = False

sport = {
    "name": "Squat", 
    "count": 0,
    "calories": 0
}


def logger(count, cals):        #紀錄執行的資訊
    f = open("log.txt", 'a')
    fs = f"{time.ctime()} count: {count} cals: {cals}\n"
    f.write(fs)
    f.close()

#角度計算要另外去寫
#計算角度函式
def calc_angles(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
              np.arctan2(a[1] - b[1], a[0] - b[0])

    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180:
        angle = 360 - angle

    return angle

#計算標記點的分量函式
def get_landmark(landmarks, part_name):
    return [
        landmarks[mppose.PoseLandmark[part_name].value].x,
        landmarks[mppose.PoseLandmark[part_name].value].y,
        landmarks[mppose.PoseLandmark[part_name].value].z,
    ]


def get_visibility(landmarks):
    if landmarks[mppose.PoseLandmark["RIGHT_HIP"].value].visibility < 0.8 or \
            landmarks[mppose.PoseLandmark["LEFT_HIP"].value].visibility < 0.8:
        return False
    else:
        return True

#計算身體比率函式
def get_body_ratio(landmarks):
    r_body = abs(landmarks[mppose.PoseLandmark["RIGHT_SHOULDER"].value].y     #右肩膀-右髋(ㄎㄨㄢ)
                 - landmarks[mppose.PoseLandmark["RIGHT_HIP"].value].y)
    l_body = abs(landmarks[mppose.PoseLandmark["LEFT_SHOULDER"].value].y
                 - landmarks[mppose.PoseLandmark["LEFT_HIP"].value].y)
    avg_body = (r_body + l_body) / 2
    r_leg = abs(landmarks[mppose.PoseLandmark["RIGHT_HIP"].value].y            #右髋-右腳踝
                - landmarks[mppose.PoseLandmark["RIGHT_ANKLE"].value].y)
    l_leg = abs(landmarks[mppose.PoseLandmark["LEFT_HIP"].value].y
                - landmarks[mppose.PoseLandmark["LEFT_ANKLE"].value].y)
    if r_leg > l_leg:
        return r_leg / avg_body
    else:
        return l_leg / avg_body

#計算左右腳的角度函式
def get_knee_angle(landmarks):
    r_hip = get_landmark(landmarks, "RIGHT_HIP")
    l_hip = get_landmark(landmarks, "LEFT_HIP")

    r_knee = get_landmark(landmarks, "RIGHT_KNEE")
    l_knee = get_landmark(landmarks, "LEFT_KNEE")

    r_ankle = get_landmark(landmarks, "RIGHT_ANKLE")
    l_ankle = get_landmark(landmarks, "LEFT_ANKLE")

    r_angle = calc_angles(r_hip, r_knee, r_ankle)
    l_angle = calc_angles(l_hip, l_knee, l_ankle)

    
    #print(r_hip)
    m_hip = (r_hip + l_hip)
    m_hip = [x / 2 for x in m_hip]
    m_knee = (r_knee + l_knee)
    m_knee = [x / 2 for x in m_knee]
    m_ankle = (r_ankle + l_ankle)
    m_ankle = [x / 2 for x in m_ankle]

    mid_angle = calc_angles(m_hip, m_knee, m_ankle)

    return [int(r_angle),int(l_angle) ,int(mid_angle)]

#標示深蹲次數之外框(左上角的count 計算次數)
def draw_fillrectangle(img):
    left_up = (240, 30)       #X座標
    right_down =  (5, 100)    #y座標
    color = (0, 0, 255) # red   B、G、R
    thickness = -1 # 寬度 (-1 表示填滿)
    cv2.rectangle(img, left_up, right_down, color, thickness) 

    #cv2.rectangle(img, (125, 20), (175, 40), (255, 0, 255), -1) 

    return img

def draw_rectangle(img):
    left_up = (240, 30)
    right_down =  (5, 100)
    color = (82, 169, 255) 
    thickness = 1 # 寬度 (-1 表示填滿)
    cv2.rectangle(img, left_up, right_down, color, thickness)


def main():
    global h, w, start_time, status
    flag = False
    if not cam.isOpened():
        print("Camera not open")
        exit()

    try:
        f = open("sport_recorder.json", "r")
        prevdata = json.load(f)
        if sport['name'] == prevdata['name']:
            sport['count'] = prevdata['count']
            sport['calories'] = prevdata['calories']
            print("Read Success!")
        f.close()
    except:
        print("Read Error...")
        pass

    tmp = f"a{sport['count']}\n"
    #ser.write(str.encode(tmp))
    tmp = f"b{sport['calories']}\n"
    #ser.write(str.encode(tmp))

    #cv2.namedWindow('frame', cv2.WINDOW_FREERATIO)
    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('frame',cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)    #開啟整個畫面程式，若不要這行 則會變成視窗化

    #旗標概念
    key_detect = 0

    run_flag = 0

    while not flag:
        ret, frame = cam.read()

        if not ret:
            print("Read Error")
            break
        #frame = cv2.flip(frame, 1)
        rgbframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        poseoutput = poses.process(rgbframe)
        h, w, _ = frame.shape
        preview = frame.copy()

        
        read_dir_key = cv2.waitKey(1)
        if (read_dir_key != -1):
            print(read_dir_key)

        # 按下"Enter"鍵，則遊戲開始
        if (read_dir_key == 13):
            sport['count'] = 0
            run_flag += 1

        # 再按一次"Enter"鍵，則畫面上會顯示"Press Enter To Start"
        if (run_flag == 2):
            run_flag = 0


        if (run_flag == 1): 
            if poseoutput.pose_landmarks:
                mpdraw.draw_landmarks(preview, poseoutput.pose_landmarks, mppose.POSE_CONNECTIONS)
                knee_angles = get_knee_angle(poseoutput.pose_landmarks.landmark)
                body_ratio = get_body_ratio(poseoutput.pose_landmarks.landmark)
                
                #左腳膝蓋彎曲角度之顏色顯示。小於120度綠色，介於120~130度黃色，大於130度紅色
                if knee_angles[0] < 120:
                    #外框
                    cv2.putText(preview, "Left Angle: {:d}".format(knee_angles[0]), (400, 360)    #座標
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (82, 169, 255), 4, cv2.LINE_AA   #顏色，粗度為4
                                )
                    #填滿外框裡面
                    cv2.putText(preview, "Left Angle: {:d}".format(knee_angles[0]), (400, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1, cv2.LINE_AA
                                )
                elif knee_angles[0] < 130:
                    cv2.putText(preview, "Left Angle: {:d}".format(knee_angles[0]), (400, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (82, 169, 255), 4, cv2.LINE_AA
                                )
                    cv2.putText(preview, "Left Angle: {:d}".format(knee_angles[0]), (400, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 1, cv2.LINE_AA
                                )
                else:
                    cv2.putText(preview, "Left Angle: {:d}".format(knee_angles[0]), (400, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (82, 169, 255), 4, cv2.LINE_AA
                                )
                    cv2.putText(preview, "Left Angle: {:d}".format(knee_angles[0]), (400, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA
                                )

                #右腳膝蓋彎曲角度之顏色顯示。小於120度綠色，介於120~130度黃色，大於130度紅色
                if knee_angles[1] < 120:
                    cv2.putText(preview, "Right Angle: {:d}".format(knee_angles[1]), (400, 400)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (82, 169, 255), 4, cv2.LINE_AA
                                )
                    cv2.putText(preview, "Right Angle: {:d} ".format(knee_angles[1]), (400, 400)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1, cv2.LINE_AA
                                )
                elif knee_angles[1] < 130:
                    cv2.putText(preview, "Right Angle: {:d}".format(knee_angles[1]), (400, 400)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (82, 169, 255), 4, cv2.LINE_AA
                                )
                    cv2.putText(preview, "Right Angle: {:d}".format(knee_angles[1]), (400, 400)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 1, cv2.LINE_AA
                                )
                else:
                    cv2.putText(preview, "Right Angle: {:d}".format(knee_angles[1]), (400, 400)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (82, 169, 255), 4, cv2.LINE_AA
                                )
                    cv2.putText(preview, "Right Angle: {:d}".format(knee_angles[1]), (400, 400)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA
                                )

                avg_angle =  int((knee_angles[0] + knee_angles[1]) // 2)
                

                # 決定深蹲的次數
                if status:
                    if avg_angle > 160:
                        status = False
                        pass_time = time.time() - start_time
                        start_time = 0

                        #從深蹲(小於120度)，到起立(大於160度)，若時間大於0.5秒，則次數加一
                        if 3000 > pass_time > 0.5:   #深蹲時間要大於0.5秒才算
                            sport['count'] = sport['count'] + 1
                            
                            #播放馬力歐得金幣音效
                            while (pygame.mixer.music.get_busy()!=1):   #用while 播完才能做下個音效
                                    pygame.mixer.music.load('coin05.mp3')
                                    pygame.mixer.music.play()
                            
                            #計算卡路里
                            sport['calories'] = sport['calories'] + int(0.66 * pass_time)
                            logger(sport['count'], sport['calories'])
                            tmp = f"a{sport['count']}\n"
                            #ser.write(str.encode(tmp))
                            tmp = f"b{sport['calories']}\n"
                            #ser.write(str.encode(tmp))
                            #print(pass_time)
                        

                else:
                    if avg_angle < 120 and body_ratio < 1.2:   #蹲下去符合條件 才開始算時間 (可以自己改角度)
                        start_time = time.time()
                        status = True
                

                # print(f"status:{status} {start_time}")

                #在螢幕上顯示深蹲狀態
                if status:
                    cv2.putText(preview, f"Pose: {status} ", (400, 440)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (82, 169, 255), 4, cv2.LINE_AA
                                )
                    cv2.putText(preview, f"Pose: {status} ", (400, 440)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1, cv2.LINE_AA
                                )
                else:
                    cv2.putText(preview, f"Pose: {status}", (400, 440)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (82, 169, 255), 4, cv2.LINE_AA
                                )
                    cv2.putText(preview, f"Pose: {status}", (400, 440)
                                , cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA
                                )
            else:
                start_time = 0

            draw_fillrectangle(preview)
            draw_rectangle(preview)

            #在螢幕上顯示深蹲次數
            cv2.putText(preview, f"count:{sport['count']}", (10, 80)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1.5, (82, 169, 255), 4, cv2.LINE_AA
                                )
            cv2.putText(preview, f"count:{sport['count']}", (10, 80)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 2, cv2.LINE_AA  
                            )

            
        ############################發出音效聲音##########################################
            if (sport['count'] == 5):                             #當做到第五下時的音效 (可以自己錄音放上去)
                while (pygame.mixer.music.get_busy()!=1):
                    pygame.mixer.music.load('./boss/shuii.mp3')   #聲音的路徑
                    pygame.mixer.music.play()                
            
            if (sport['count'] == 10):                             #當做到第十下時的音效
                while (pygame.mixer.music.get_busy()!=1):
                    pygame.mixer.music.load('./boss/10.mp3')
                    pygame.mixer.music.play()

            if (sport['count'] == 20):
                while (pygame.mixer.music.get_busy()!=1):
                    pygame.mixer.music.load('./boss/20.mp3')
                    pygame.mixer.music.play()
            
            if (sport['count'] == 30):
                while (pygame.mixer.music.get_busy()!=1):
                    pygame.mixer.music.load('./boss/30.mp3')
                    pygame.mixer.music.play()



            ############################在螢幕上顯示多少combo##########################################
            
            if (sport['count'] > 40):
                cv2.putText(preview, f"40 combo", (10, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1, (82, 169, 255), 4, cv2.LINE_AA)
                cv2.putText(preview, f"40 combo", (10, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)  
                #ser.write(b'command_4\n')                     #將字串傳給Arduino
            elif (sport['count'] > 30):
                cv2.putText(preview, f"30 combo", (10, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1, (82, 169, 255), 4, cv2.LINE_AA)
                cv2.putText(preview, f"30 combo", (10, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
                #ser.write(b'command_3\n')
            elif (sport['count'] > 20):
                cv2.putText(preview, f"20 combo", (10, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1, (82, 169, 255), 4, cv2.LINE_AA)
                cv2.putText(preview, f"20 combo", (10, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
                #ser.write(b'command_2\n')
            elif (sport['count'] > 10):
                cv2.putText(preview, f"10 combo", (10, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1, (82, 169, 255), 4, cv2.LINE_AA)
                cv2.putText(preview, f"10 combo", (10, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
                #ser.write(b'command_1\n')
            else:
                cv2.putText(preview, f"Zero combo", (10, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1, (82, 169, 255), 4, cv2.LINE_AA)
                cv2.putText(preview, f"Zero combo", (10, 360)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
                #ser.write(b'command_0\n')
            
        
        else:
            #在螢幕上顯示"Press Enter To Start"，以開始深蹲遊戲
            cv2.putText(preview, "Press Enter To Start", (10, 80)     #OpenCV函式
                                , cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 5, cv2.LINE_AA)

            cv2.putText(preview, "Press Enter To Start", (10, 80)
                                , cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2, cv2.LINE_AA)
        
        cv2.imshow('frame', preview)

        #按下鍵盤'q'，則結束程式
        if read_dir_key & 0xFF == ord('q'):
            sport['count'] = 0
            flag = True

    f = open("sport_recorder.json", "w+")    #寫入，且不做覆寫 用累加的動作
    f.write(json.dumps(sport))
    f.close()

    # 釋放攝影機資源
    cam.release()
    cv2.destroyAllWindows()   


if __name__ == '__main__':
    main()