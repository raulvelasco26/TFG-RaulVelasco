' =============================================================================
' PEF AI Assistant - Lanzador
' Arranca Streamlit en segundo plano y abre el navegador automaticamente.
' Este archivo es al que apunta el acceso directo del escritorio.
' =============================================================================

Set objShell = CreateObject("WScript.Shell")
Set fso     = CreateObject("Scripting.FileSystemObject")

' Este .vbs esta en installation\, la raiz del proyecto es un nivel arriba
Dim vbsDir, appDir
vbsDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\") - 1)
appDir = Left(vbsDir, InStrRev(vbsDir, "\") - 1)

' Verificar que setup.bat se ejecuto antes
If Not fso.FileExists(appDir & "\venv\Scripts\python.exe") Then
    MsgBox "La aplicacion no esta instalada todavia." & Chr(13) & Chr(13) & _
           "Ejecuta primero:  installation\setup.bat", _
           vbCritical, "PEF AI Assistant"
    WScript.Quit
End If

' Comprobar si ya hay una instancia corriendo en el puerto 8501
Dim tmpFile
tmpFile = objShell.ExpandEnvironmentStrings("%TEMP%") & "\pef_port_check.txt"
objShell.Run "cmd /c netstat -an > """ & tmpFile & """", 0, True

Dim alreadyRunning
alreadyRunning = False
If fso.FileExists(tmpFile) Then
    Dim ts, contents
    Set ts = fso.OpenTextFile(tmpFile, 1)
    contents = ts.ReadAll
    ts.Close
    fso.DeleteFile tmpFile
    If InStr(contents, ":8501") > 0 Then alreadyRunning = True
End If

If alreadyRunning Then
    ' Ya esta corriendo: solo abrir el navegador
    objShell.Run "http://localhost:8501"
Else
    ' Lanzar Streamlit en una ventana minimizada
    Dim cmd
    cmd = "cmd /k call """ & appDir & "\venv\Scripts\activate.bat"" " & _
          "&& python -m streamlit run """ & appDir & "\src\app.py"" " & _
          "--browser.gatherUsageStats=false --server.headless=false"
    objShell.Run cmd, 2, False

    ' Esperar a que Streamlit arranque y abrir el navegador
    WScript.Sleep 4000
    objShell.Run "http://localhost:8501"
End If
