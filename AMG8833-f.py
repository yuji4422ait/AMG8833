#!/usr/bin/env python
# -*- coding: utf-8 -*-
import smbus                         # smbusライブラリ扱う(i2c通信）
import time                          # システムの時間を扱う
import numpy as np                  # 配列,多次元配列を取り扱う
import cv2                           # Cv2モジュールを扱う
import csv                           # CSVモジュールを扱う
import datetime                     # 日付、時間を扱う
from time import sleep             # sleep関数を扱う
from GridEye import GridEye       # GrideEyeモジュールを扱う

addr=0x68                            # slave address:68 hex
REG_TOOL = 0x0E                     # サーミスタ出力値（下位）
REG_PIXL = 0x80                     # 画素出力値（下位）
myeye = GridEye()                   # 変数名

temp_min = 20.                      # 最小温度
temp_max = 30.                      # 最高温度
img_edge = 256                      # 画素値(0〜255画素値,Pixcel value)
i2c = smbus.SMBus(2)               # Get I2C bus

def read_AMG8833():               # AMG8833関数定義(引数が無く戻り値がある関数)
	ObjectTemp1 = i2c.read_word_data(addr, REG_PIXL) # 画像1の赤外線温度を読み込む	
	ObjectTemp1 = ObjectTemp1 * 0.25                     # 読んだ温度を部会能0.25で乗算する	　　　　　　　
	return (round(ObjectTemp1,2))         # 測定温度(赤外線温度1)の戻り値,小数点2迄	
    
def setup_st7032():              # st7032のLCDディスプレィ初期化処理関数
    trials = 5              
    for i in range(trials):     # trials　5回繰り返す
        try:      
            # contrast = 36(c5,c4,c3,c2,c1,c0の6bit) 
            # 36 = 00100100, 0xf  = 00001111, 00100100 & 00001111 = 00000100
            # 00000100(下位bitの0100を取り出す),マスクしたいbitの時に&=andする。c_lower = 00000100
            c_lower = (contrast & 0xf)
            # 36 = 00100100, 0x30 = 00110000, 00100100 & 00110000 = 00100000
            #  >>4, 右4シフトすると00000010 (下位bitの0010を取り出す), c_upper = 00000010
            c_upper = (contrast & 0x30)>>4
            # fuction set 0x38:２行モード設定,fuction set 0x39:コマンドグループ2を選択,
            # internal osc frequency (動作周波数設定) 0x14, contrast set(コントラスト設定コマンド) 0x70
            # power/icon contrast control(電源コントラスト設定コマンド) 0x54, flower control(内部電源回路設定コマンド) 0x6c            
            # 0x70|c_lower, (0x70=01110000,|=or, c_lower = 00000100)
            # 01110000 | 00000100 = 01110100, 0x74(下位4bit 0100=contrast=c3,c2,c1,c0),0x70から0x74に変更となる
            # 0x54|c_upper, (0x54=01010100,|=or, c_upper = 00000010)     
            # 01010100 | 00000010 = 01010110, 0x56(下位2bit 10=contrast=c5,c4),0x54から0x56に変更となる                
            bus.write_i2c_block_data(address_st7032, register_setting, [0x38, 0x39, 0x14, 0x70|c_lower, 0x54|c_upper, 0x6c])
            sleep(0.2)
            # fuction set 0x38:コマンドグループ1に戻す、display on/off controll 0x0d,clear display 0x01
            bus.write_i2c_block_data(address_st7032, register_setting, [0x38, 0x0d, 0x01])
            sleep(0.001)
            break       # ループを中断する
        except IOError: # 例外を受けて実行する処理,4回以内ならば,IOError発生させ抜ける
            if i==trials-1:
                sys.exit()
                
def clear():         # 液晶に書かれている文字を消し、カーソルを元に戻す関数
    global position # global変数宣言:関数の外側で定義した変数をグローバル変数と呼びます。global 変数名　position = 0
    global line     # global変数宣言:関数の外側で定義した変数をグローバル変数と呼びます。global 変数名  line = 0
    position = 0    # local変数:関数内でしか使用出来ない,カーソルを元に戻す
    line = 0         # local変数:関数内でしか使用出来ない,カーソルを元に戻す
    bus.write_byte_data(address_st7032, register_setting, 0x01)   # 0x01液晶を消すコマンド 
    sleep(0.001)
    
def newline():      # 改行する関数,カーソルを次の行の先頭へ移動させる
    
    if line == display_lines-1: # display_linesが１行ならば,clear関数を実行する
        clear()
    else:           # そうでなければ
        line += 1   # 1行増やす
        position = chars_per_line*line # 2行目の横16列へ移動
        bus.write_byte_data(address_st7032, register_setting, 0xc0) # 文字表示位置は2行の先頭へ
        sleep(0.001)

def write_string(s):       # 液晶へ複数の文字列からなるsを表示する関数
    for c in list(s):      # 文字を取り出す(for 変数 in データの集まり:)
        write_char(ord(c)) # write char関数の呼び出し(アスキーコードへ変換する)

def write_char(c):         # 液晶へ1文字ずつ表示する関数(アスキーコードから文字列へ変換する関数)
    global position        # global変数宣言:関数の外側で定義した変数をグローバル変数と呼びます。global 変数名　position = 0
    byte_data = check_writable(c) # check_writable(c)関数の呼び出し
    if position == display_chars: # もし,液晶画面の2行＊横16列が埋まっている場合は,画面を消去する
        clear()
    elif position == chars_per_line*(line+1): # 1行*横16列が埋まっていれば改行する。(elif=else if=もし,○○ならば)
        newline()                 # newline()関数を実行する
    bus.write_byte_data(address_st7032, register_display, byte_data) # 液晶画面へ表示させる
    position += 1                 # 1増やす

def check_writable(c):            # 文字cを表示させる関数
    if c >= 0x06 and c <= 0xff :  # キャラクタディスプレィの上位4bit(0110)〜下位4bit(1111)の間でcを表示させる
        return c                  # cを表示させる
    else:                         # そうでなければ
        return 0x20 # 空白文字     # キャラクタディスプレィの上位4bit(0010)〜下位4bit(0000)の空白文字を表示させる

bus = smbus.SMBus(2)              # smbus通信を使用する(i2c通信)

address_st7032 = 0x3e             # st7032 LCDアドレス 
                                   # 1byteの1bit目は読み書きbit用にて,addressは左1bitシフトする
                                   # 0x3e=00111110,左1bitシフトして,01111100となり,最初の1byteは0x7cに変更される
register_setting = 0x00           # 動作設定データ
register_display = 0x40           # 表示文字データ

contrast = 36                      # 0から63のコントラスト。30から40程度を推奨
chars_per_line = 16               # LCDの横方向の文字数
display_lines = 2                 # LCDの行数

display_chars = chars_per_line*display_lines # 2行＊横16列

position = 0
line = 0

setup_st7032()                    # st7032のLCDディスプレィ初期化処理

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

try: 	                                         # 例外が発生する可能性がある処理
	index = 1
	while index <= 10:                        # index 「1」「2」「3」...と1から順に番号が割り当て,繰り返し回数
		inputValue = read_AMG8833()        # AMG8833赤外線温度データを読み込みます		
		try:
			clear()                           # 温度をLCDに表示する前に画面を消去します
			s = str(inputValue)             # AMG8833赤外線温度データを文字列に変換して液晶に表示させる
			write_string(s)                 # 液晶へ複数の文字列からなるsを表示する関数を呼びます
		except IOError:                     # 例外を受けて実行する処理,IOErrorが発生すれば,シェルへ"接続エラースキップ"を表示する
			print("接続エラースキップ") 
		timestamp = datetime.datetime.now()   # 現在の日付、現在時刻の取得,スタンプ
		print(timestamp)                         # timestampを出力する
		Atemp = myeye.thermistorTemp()         # GridEye関数のthermistorTemp()関数を扱う				
		ObjectTemp_all = myeye.pixelOut()     # すべての赤外線温度は、GridEye関数のpixelOut()関数を扱う
		pixel = np.array(myeye.pixelOut())     # 多次元配列で,GridEyeモジュールのpixel out()関数を扱う
		ObjectTemp_all = np.array(ObjectTemp_all).reshape(8,8) # 多次元配列で赤外線温度を8行8列にする  
				
		print ('Thermistor Temp:', myeye.thermistorTemp())
		pixel.resize((8, 8))                       # pixelサイズは横8,縦8
		
		if pixel.max() - pixel.min() > 9.0:         # もし,pixel最高-最低の値が9.0より大きい場合
			print (pixel.max() - pixel.min())      # print出力
			
		temp_min = temp_min * 0.9 + pixel.min() * 0.1  # temp_min = 20*0.9+pixel.min*0.1
		temp_max = temp_max * 0.9 + pixel.max() * 0.1  # temp_max = 30*0.9+pixel.max*0.1
		if temp_max < 30:                                # もし、30以内ならば
			temp_max = 30                                # temp_max = 30にする
		   
		print ('Pixel Out(Temp):')                      # Pixel Out(Temp)文字を出力する
		print (pixel)                                      # 赤外線温度を8行8列で出力する
		pixel = pixel.clip(temp_min, temp_max)        # pixclは,温度minと温度maxで分ける
		pixel = (pixel - temp_min) / (temp_max - temp_min) * 255.0  # 1〜64画素温度の読み込みをして,グレースケールに変換
		pixel = pixel.astype(np.uint8)                 # 8ビット符号無しの整数型の型に変換する		  
		   
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
		# 画像10,30位置へ赤文字で最高温度を表示する  
		cv2.putText(img, str(temp_max), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), thickness=2)
		   
		cv2.imshow('GridEyeView', img)  # 画面をウィンドウ上に表示する。cv2.imshow(第一引数:文字列型で指定するウィンドウ名,第二引数:表示したい画像)	
		if cv2.waitKey(100) == 27:        # waitKeyではキーボードからの入力待受で引数のミリ秒だけ入力を待ち受ける。その後,次の処理に移る。(100)=0.1sec,chr(27):ESC
			break                          # 繰り返しを中断する
			cv2.destroyAllWindows()    # 指定された名前のウィンドウを破棄します。
			   
		timecount += 1                    # timecountを1増やす
		# indexへAtemp_data,interval,pixelOut_dataを追加する
		Atemp_data.append(round(Atemp,2 ))
		interval.append(timecount)
		pixelOut_data.append(ObjectTemp_all)
		# dataへtimestamp,timecount,Atemp_data,pixelOut_dataを入力する
		data = [timestamp,timecount,Atemp_data,pixelOut_data]		
		# data,("-----")を出力する
		#print('data',data)		
		#print('-----')
		# rion.csvファイルへ改行し、行を詰めて書き込みます
		# newlineはファイルの改行コードを指定する引数です
		# dataへ書き込みます
		writer = csv.writer(open('rion.csv','a',newline=''))
		writer.writerow(data)
		# indexへ+１増やします
		index += 1
		# cpuに0.75秒間while処理を停止させ、他の処理をさせる　これがないと計算処理に大半を費やす
		time.sleep(0.75) 	   
       
except KeyboardInterrupt: # 例外を受けて実行する処理,keybordのctrl+c処理でこのブロックへ移る
    pass                  # 何もせずに、次に移るという意味  

        # ニアレストネイバー法:画像を拡大した際に最近傍にある画素をそのまま使う線形補間法です。
        # i=[100 200] i'=[100 200 200]
        # バイキュービック法:周囲16画素の画素値を利用します。そして、距離に応じて関数を使い分け、加重平均を求めます。
