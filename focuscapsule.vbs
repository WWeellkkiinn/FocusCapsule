Dim fso, sh, f, pythonPath
Set fso = CreateObject("Scripting.FileSystemObject")
Dim dir : dir = fso.GetParentFolderName(WScript.ScriptFullName)
If Not fso.FileExists(dir & "\.python-path") Then
    MsgBox "Run 'python install.py' first to configure FocusCapsule.", 16, "FocusCapsule"
    WScript.Quit 1
End If
Set f = fso.OpenTextFile(dir & "\.python-path", 1)
pythonPath = Trim(f.ReadAll())
f.Close
If Not fso.FileExists(pythonPath) Then
    MsgBox "Python not found: " & pythonPath & Chr(10) & "Run 'python install.py' again.", 16, "FocusCapsule"
    WScript.Quit 1
End If
Set sh = CreateObject("WScript.Shell")
sh.Run """" & pythonPath & """ """ & dir & "\main.py""", 0, False
