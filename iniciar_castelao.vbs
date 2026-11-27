Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\escritorio\Desktop\castelao-promocoes"
WshShell.Run """C:\Users\escritorio\AppData\Local\Programs\Python\Python314\pythonw.exe"" ""C:\Users\escritorio\Desktop\castelao-promocoes\app.py""", 0, False
