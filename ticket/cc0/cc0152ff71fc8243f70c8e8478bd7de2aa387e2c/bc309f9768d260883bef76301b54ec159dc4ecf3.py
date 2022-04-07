
import time
import sys
import win32console

screenBuffer = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)

normal = (win32console.FOREGROUND_RED |
          win32console.FOREGROUND_GREEN |
          win32console.FOREGROUND_BLUE)

red = (win32console.FOREGROUND_RED |
       win32console.FOREGROUND_INTENSITY)

green = (win32console.FOREGROUND_GREEN |
         win32console.FOREGROUND_INTENSITY)

blue = (win32console.FOREGROUND_BLUE |
        win32console.FOREGROUND_INTENSITY)

yellow = (win32console.FOREGROUND_RED |
          win32console.FOREGROUND_GREEN |
          win32console.FOREGROUND_INTENSITY)

def write(x, color=normal):
    screenBuffer.SetConsoleTextAttribute(color)
    sys.stdout.write(x)
    sys.stdout.flush()
    if '\n' not in x:
        time.sleep(0.5)

write("testingTestsPass... ")
write("[OK]\n", green)
write("testingTestsFail... ")
write("[FAILED]\n", red)
write("testingTestsSucceed... ")
write("[SUCCESS!?!]\n", yellow)
write("testingTestsTodo... ")
write("[TODO]\n", blue)

write("Done.\n")
