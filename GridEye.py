#!/usr/bin/env python
import smbus          # smbusライブラリ扱う(i2c通信）


class GridEye:        #クラス定義する
    __REG_FPSC = 0x02 #フレームレートレジスタ設定
    __REG_TOOL = 0x0E #サーミスタ出力値（下位）
    __REG_PIXL = 0x80 #画素出力値（下位）

    def __init__(self, address=0x68): #初期化メゾット,addressは引数 (def_init_(self.引数2,引数3,・・):
        self.i2c = smbus.SMBus(1)     #インスタンス変数を初期化する。self.変数名 = 初期値 
        self.address = address        #インスタンス変数を初期化する。self.変数名 = 初期値
        self.i2c.write_byte_data(self.address, self.__REG_FPSC, 0x00) #引数で受け取った値を代入する(フレームレートレジスタ設定を10FPS)

    def thermistorTemp(self):         #引数がなく,戻り値がある関数(サーミスタ温度）
        result = self.i2c.read_word_data(self.address, self.__REG_TOOL) #サーミスタ出力値を読み込む
        if(result > 2047):            #もし,2047より大きい場合は
            result = result - 2048    #2048を引く,(2057-2047=10)
            result = -result          #マイナス値になる（-10)
        return result * 0.0625        #0.0625(サーミスタ出力分解能) 例:-10*0.0625=-0.625℃,例2:2047*0.0625=127.9375℃

    def pixelOut(self):               #引数がなく,戻り値がある関数(ピクセル出力)
        out = []                      #outのリスト作成
        for x in range(0, 64):        #0〜63のピクセルを繰り返す
            temp = self.i2c.read_word_data(self.address, self.__REG_PIXL + (x * 2)) #0x80(画素出力）+(80,82,84,86,88,8a・・・・fe),画素64
            if(temp > 2047):          #もし温度が2047より大きい場合
                temp = temp - 4096    #4096を引く,(3596-4096=-500)
            out.append(temp * 0.25)   #0.25(温度分解能) 例:-500*0.25=-125℃,例2:500*0.25=125℃  
        return out                    #戻り値,outリストへ入力

    #サーミスタ温度(12bitで2バイトデータ,符号+絶対値)
    #温度データ(12bitで2バイトデータ,11ビット+サインの2の補数形式)
    #[1111,1111,1111]
    #[2048,1024,512,256,128,64,32,16,8,4,2,1] = 4095
    #[0111,1111,1111}
    #[     1024,512,256,128,64,32,16,8,4,2,1] = 2047
    
