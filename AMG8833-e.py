#!/usr/bin/env python
# -*- coding: utf-8 -*-
import smbus                         # smbusライブラリ扱う(i2c通信）
import time                          # システムの時間を扱う
import numpy as np                  # 配列,多次元配列を取り扱う
import matplotlib.pyplot as plt   # グラフを作成する関数
import cv2                          # Cv2モジュールを扱う
import csv                          # CSVモジュールを扱う
import datetime                    # 日付、時間を扱う
from GridEye import GridEye       # GrideEyeモジュールを扱う

i2c = smbus.SMBus(2)                # Get I2C bus
addr=0x68                           # slave address:68 hex
REG_TOOL = 0x0E                     # サーミスタ出力値（下位）
REG_PIXL = 0x80                     # 画素出力値（下位）

myeye = GridEye()            # 変数名

temp_min = 20.               # 最小温度
temp_max = 30.               # 最高温度

img_edge = 256               # 画素値(0〜255画素値,Pixcel value)

#i2c.write_byte_data(addr,0x02,0x01) #フレームレート設定（0x00:10fps,0x01:1fps)

# np.zeros(任意の大きさと型で出来た画像のための配列をゼロで初期化する。
# 画素値256の値を2行3列の符号無し整数型で表示する。uint8(8ビット符号無し整数型)
img = np.zeros((img_edge, img_edge * 2, 3), np.uint8) 
print (img)
print ("-----------")

# np.set_printoptions(precision=1)
#リスト作成,timecount作成
Atemp_data=[]
interval=[]
pixelOut_data=[]
timecount=0

while(True):  # 繰り返し処理
    #print ('Thermistor Temp:', myeye.thermistorTemp())
    timestamp = datetime.datetime.now()   # 現在の日付、現在時刻の取得,スタンプ
    print(timestamp)                       # timestampを出力する
    Atemp = myeye.thermistorTemp()
    ObjectTemp_all = myeye.pixelOut()
    ObjectTemp_all =np.array(ObjectTemp_all).reshape(8,8)
    
    pixel = np.array(myeye.pixelOut())           # 多次元配列で,GridEyeモジュールのpixel out関数を扱う
    pixel.resize((8, 8))                          # pixelサイズは横8,縦8
    
    if pixel.max() - pixel.min() > 9.0:           # もし,pixel最高-最低の値が9.0より大きい場合
        print (pixel.max() - pixel.min())         # print出力

    temp_min = temp_min * 0.9 + pixel.min() * 0.1 # temp_min = 20*0.9+pixel.min*0.1
    temp_max = temp_max * 0.9 + pixel.max() * 0.1 # temp_max = 30*0.9+pixel.max*0.1
    if temp_max < 30:                             # もし、30以内ならば
        temp_max = 30                             # temp_max = 30にする
        
    #print ('Pixel Out(Temp):')
    #print (pixel)
        
    pixel = pixel.clip(temp_min, temp_max)        # pixclは,温度minと温度maxで分ける
    pixel = (pixel - temp_min) / (temp_max - temp_min) * 255.0  # 1〜64画素温度の読み込みをして,グレースケールに変換
    pixel = pixel.astype(np.uint8)                # 8ビット符号無しの整数型の型に変換する

    #print ('Pixel Out(0-255):')
    #print (pixel)
    
    # グレースケールをカラーに変換する(第1引数:pixcl,第2引数:cv2.COLORMAP_JET) jet:数種類のカラー変換の一部
    pixel = cv2.applyColorMap(pixel, cv2.COLORMAP_JET) 

    # 左側にコピー
    roi = img[:, :img_edge] # roi = Region  of intrset(領域補間,注目領域),画素値256の値を2行3列の符号無し整数型で表示する。
    cv2.resize(pixel, roi.shape[0:2], roi,      # cv2,resize(画像をリサイズする)
               interpolation=cv2.INTER_CUBIC)   # pixel入力画像を縦256*横256の倍率で,最近傍補間法(バイキュービック)にて拡大する    

    # 右側にコピー
    roi = img[:, img_edge:] # roi = Region  of intrset(領域補間,注目領域),画素値256の値を2行3列の符号無し整数型で表示する。
    cv2.resize(pixel, roi.shape[0:2], roi,      # cv2,resize(画像をリサイズする) 
               interpolation=cv2.INTER_NEAREST) # pixel入力画像を縦256*横256の倍率で,最近傍補間法(ニアレストネイバー)にて拡大する
               
    cv2.putText(img, str(temp_max), (10,30 ), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), thickness=2)
        
    cv2.imshow('GridEyeView', img)  # 画面をウィンドウ上に表示する。cv2.imshow(第一引数:文字列型で指定するウィンドウ名,第二引数:表示したい画像)
    if cv2.waitKey(100) == 27:      # waitKeyではキーボードからの入力待受で引数のミリ秒だけ入力を待ち受ける。その後,次の処理に移る。(100)=0.1sec,chr(27):ESC
        break                       # 繰り返しを中断する

cv2.destroyAllWindows()             # 指定された名前のウィンドウを破棄します。

timecount += 1                                # timecountを1増やす
# indexへAmbient_tempdata,interval,Object_tempdataを追加する
Atemp_data.append(round(Atemp,2 ))
interval.append(timecount)
pixelOut_data.append(ObjectTemp_all)
# dataへtimestamp,timecount,AmbientTemp,2,ObjectTemp1,2を入力する
data = [timestamp,timecount,Atemp_data,pixelOut_data]	
# data,("-----")を出力する
#print('data',data)		
#print('-----')
# hikaru.csvファイルへ改行し、行を詰めて書き込みます
# newlineはファイルの改行コードを指定する引数です
# dataへ書き込みます
writer = csv.writer(open('rion.csv','a',newline=''))
writer.writerow(data)	
# cpuに0.85秒間while処理を停止させ、他の処理をさせる　これがないと計算処理に大半を費やす
time.sleep(0.75) 	   

    # ニアレストネイバー法:画像を拡大した際に最近傍にある画素をそのまま使う線形補間法です。
    # i=[100 200] i'=[100 200 200]
    # バイキュービック法:周囲16画素の画素値を利用します。そして、距離に応じて関数を使い分け、加重平均を求めます。
