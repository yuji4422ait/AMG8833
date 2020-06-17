#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time                          # システムの時間を扱う
import datetime                     # 日付、時間を扱う
import numpy as np           # 配列,多次元配列を取り扱う
import cv2                   # CSVモジュールを扱う
from GridEye import GridEye  # GrideEyeモジュールを扱う

myeye = GridEye()            # 変数名

temp_min = 20.               # 最小温度
temp_max = 30.               # 最高温度

img_edge = 256               # 画素値(0〜255画素値,Pixcel value)

# np.zeros(任意の大きさと型で出来た画像のための配列をゼロで初期化する。
# 画素値256の値を2行3列の符号無し整数型で表示する。uint8(8ビット符号無し整数型)
img = np.zeros((img_edge, img_edge * 2, 3), np.uint8) 
print (img)
print ("-----------")

# np.set_printoptions(precision=1)
try: 	                                             # 例外が発生する可能性がある処理
	index = 1
	while index <= 30:                              # index 「1」「2」「3」...と1から順に番号が割り当て,繰り返し回数
		timestamp = datetime.datetime.now()   # 現在の日付、現在時刻の取得,スタンプ
		print(timestamp)                          # timestampを出力する
		# indexへ+１増やします
		index += 1
		print ('Thermistor Temp:', myeye.thermistorTemp())
		
		pixel = np.array(myeye.pixelOut())            # 多次元配列で,GridEyeモジュールのpixel out関数を扱う
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
		
		cv2.imshow('GridEyeView', img)  # 画面をウィンドウ上に表示する。cv2.imshow(第一引数:文字列型で指定するウィンドウ名,第二引数:表示したい画像)
		if cv2.waitKey(100) == 27:      # waitKeyではキーボードからの入力待受で引数のミリ秒だけ入力を待ち受ける。その後,次の処理に移る。(100)=0.1sec,chr(27):ESC
			break                       # 繰り返しを中断する
			
			cv2.destroyAllWindows()             # 指定された名前のウィンドウを破棄します。
			
			# cpuに0.85秒間while処理を停止させ、他の処理をさせる　これがないと計算処理に大半を費やす
			#time.sleep(0.75) 	 

except KeyboardInterrupt: # 例外を受けて実行する処理,keybordのctrl+c処理でこのブロックへ移る
    pass                  # 何もせずに、次に移るという意味   

    # ニアレストネイバー法:画像を拡大した際に最近傍にある画素をそのまま使う線形補間法です。
    # i=[100 200] i'=[100 200 200]
    # バイキュービック法:周囲16画素の画素値を利用します。そして、距離に応じて関数を使い分け、加重平均を求めます。
