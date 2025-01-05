
from machine import UART
from utime   import sleep_ms
from ustruct import unpack

class KT403A :

    # ============================================================================
    # ===( Constants )============================================================
    # ============================================================================

    DEVICE_U_DISK = 1
    DEVICE_SD     = 2
    DEVICE_AUX    = 3
    DEVICE_SLEEP  = 4
    DEVICE_FLASH  = 5

    EQ_NORMAL     = 0
    EQ_POP        = 1
    EQ_ROCK       = 2
    EQ_JAZZ       = 3
    EQ_CLASSIC    = 4
    EQ_BASS       = 5
    

    # ============================================================================
    # ===( Constructor )==========================================================
    # ============================================================================

    def __init__( self,
                  pin_TX,
                  pin_RX,
                  debug     = False,
                  device    = None,
                  volume    = 70,
                  eq        = None ) :
      
        self._uart = UART(1, 9600, tx=pin_TX, rx=pin_RX)
        self._debug = debug
        self.SetDevice(device if device else KT403A.DEVICE_SD)
        
        if not self.GetState() :
            raise Exception('KT403A could not be initialized.')
        self.SetVolume(volume)
        self.SetEqualizer(eq if eq else KT403A.EQ_NORMAL)

    # ============================================================================
    # ===( Utils )================================================================
    # ============================================================================

    def _txCmd(self, cmd, dataL=0, dataH=0) :
       
        
        command = bytearray([0x7E, 0xFF, 0x06, cmd, 0x00, dataH, dataL, 0xEF])
        if self._debug :
            print("Envoi commande:", [hex(x) for x in command])  # Debug
        self._uart.write(command)
        sleep_ms(500 if cmd == 0x09 else 1000 if cmd == 0x0C else 200)
        #sleep_ms(1000)  # Augmentons le délai pour le debug

    # ----------------------------------------------------------------------------

    def _rxCmd(self) :
        if self._uart.any() :
            buf = self._uart.read(10)
            if self._debug :
                print("Buffer reçu:", [hex(x) for x in buf])
            
            if buf is not None and \
               len(buf) == 10 and \
               buf[0] == 0x7E and \
               buf[1] == 0xFF and \
               buf[2] == 0x06 and \
               buf[9] == 0xEF :
               cmd = buf[3]
               # Les données d'état sont dans buf[5], buf[6] et buf[7]
               data = (buf[5] << 16) | (buf[6] << 8) | buf[7]
               
               if self._debug :
                   print("Commande:", hex(cmd), "Data:", hex(data))
               return (cmd, data)
        return None

    # ----------------------------------------------------------------------------

    def _readLastCmd(self) :
        res = None
        while True :
            r = self._rxCmd()
            
            if not r :
                return res
            res = r

    # ============================================================================
    # ===( Functions )============================================================
    # ============================================================================

    def PlayNext(self) :
        self._txCmd(0x01)

    # ----------------------------------------------------------------------------

    def PlayPrevious(self) :
        self._txCmd(0x02)

    # ----------------------------------------------------------------------------

    def PlaySpecific(self, trackIndex) :
        self._txCmd(0x03, int(trackIndex%256), int(trackIndex/256))

    # ----------------------------------------------------------------------------

    def VolumeUp(self) :
        self._txCmd(0x04)

    # ----------------------------------------------------------------------------

    def VolumeDown(self) :
        self._txCmd(0x05)

    # ----------------------------------------------------------------------------

    def SetVolume(self, percent) :
        if percent < 0 :
            percent = 0
        elif percent > 100 :
            percent = 100
        self._txCmd(0x06, int(percent*0x1E/100))

    # ----------------------------------------------------------------------------

    def SetEqualizer(self, eq) :
        if eq < 0 or eq > 5 :
            eq = 0
        self._txCmd(0x07, eq)

    # ----------------------------------------------------------------------------

    def RepeatCurrent(self) :
        self._txCmd(0x08)

    # ----------------------------------------------------------------------------

    def SetDevice(self, device) :
        self._device = device
        self._txCmd(0x09, device)

    # ----------------------------------------------------------------------------

    def SetLowPowerOn(self) :
        self._txCmd(0x0A)

    # ----------------------------------------------------------------------------

    def SetLowPowerOff(self) :
        self.SetDevice(self._device)

    # ----------------------------------------------------------------------------

    def ResetChip(self) :
        self._txCmd(0x0C)

    # ----------------------------------------------------------------------------

    def Play(self) :
        self._txCmd(0x0D)

    # ----------------------------------------------------------------------------

    def Pause(self) :
        self._txCmd(0x0E)

    # ----------------------------------------------------------------------------

    def PlaySpecificInFolder(self, folderIndex, trackIndex) :
        self._txCmd(0x0F, trackIndex, folderIndex)

    # ----------------------------------------------------------------------------

    def EnableLoopAll(self) :
        self._txCmd(0x11, 1)

    # ----------------------------------------------------------------------------

    def DisableLoopAll(self) :
        self._txCmd(0x11, 0)

    # ----------------------------------------------------------------------------

    def PlayFolder(self, folderIndex) :
        self._txCmd(0x12, folderIndex)

    # ----------------------------------------------------------------------------

    def Stop(self) :
        self._txCmd(0x16)

    # ----------------------------------------------------------------------------

    def LoopFolder(self, folderIndex) :
        self._txCmd(0x17, folderIndex)

    # ----------------------------------------------------------------------------

    def RandomAll(self) :
        self._txCmd(0x18)

    # ----------------------------------------------------------------------------

    def EnableLoop(self) :
        self._txCmd(0x19, 0)

    # ----------------------------------------------------------------------------

    def DisableLoop(self) :
        self._txCmd(0x19, 1)

    # ----------------------------------------------------------------------------

    def EnableDAC(self) :
        self._txCmd(0x1A, 0)

    # ----------------------------------------------------------------------------

    def DisableDAC(self) :
        self._txCmd(0x1A, 1)

    # ----------------------------------------------------------------------------

    def GetState(self) :
        self._txCmd(0x42)
        r = self._readLastCmd()
        return r[1] if r and r[0] == 0x42 else None

    # ----------------------------------------------------------------------------

    def GetVolume(self) :
        self._txCmd(0x43)
        r = self._readLastCmd()
        return int(r[1] / 0x1E *100) if r and r[0] == 0x43 else 0

    # ----------------------------------------------------------------------------

    def GetEqualizer(self) :
        self._txCmd(0x44)
        r = self._readLastCmd()
        return r[1] if r and r[0] == 0x44 else 0

    # ----------------------------------------------------------------------------

    def GetFilesCount(self, device=None) :
        if not device :
            device = self._device
        if device == KT403A.DEVICE_U_DISK :
            self._txCmd(0x47)
        elif device == KT403A.DEVICE_SD :
            self._txCmd(0x48)
        elif device == KT403A.DEVICE_FLASH :
            self._txCmd(0x49)
        else :
            return 0
        sleep_ms(200)
        r = self._readLastCmd()
        return r[1] if r and r[0] >= 0x47 and r[0] <= 0x49 else 0

    # ----------------------------------------------------------------------------

    def GetFolderFilesCount(self, folderIndex) :
        self._txCmd(0x4E, folderIndex)
        sleep_ms(200)
        r = self._readLastCmd()
        return r[1] if r and r[0] == 0x4E else 0

    # ----------------------------------------------------------------------------

    def IsStopped(self) :
        return self.GetState() == 0x0200

    # ----------------------------------------------------------------------------

    def IsPlaying(self) :
        return self.GetState() == 0x0201

    # ----------------------------------------------------------------------------

    def IsPaused(self) :
        return self.GetState() == 0x0202

    # ============================================================================
    # ============================================================================
    # ============================================================================