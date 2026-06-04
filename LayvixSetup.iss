[Setup]
AppName=Layvix
AppVersion=1.1.0
DefaultDirName={autopf}\Layvix
DefaultGroupName=Layvix
OutputDir=installer
OutputBaseFilename=Layvix_Setup
Compression=lzma2
SolidCompression=yes
SetupIconFile=layvix.ico
UninstallDisplayIcon={app}\Layvix.exe
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Run Layvix automatically when Windows starts"; GroupDescription: "Startup options"

[Files]
Source: "dist\Layvix\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "layvix.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Layvix"; Filename: "{app}\Layvix.exe"; IconFilename: "{app}\layvix.ico"
Name: "{commondesktop}\Layvix"; Filename: "{app}\Layvix.exe"; IconFilename: "{app}\layvix.ico"; Tasks: desktopicon
Name: "{userstartup}\Layvix"; Filename: "{app}\Layvix.exe"; Tasks: startup

[Run]
Filename: "{app}\Layvix.exe"; Description: "{cm:LaunchProgram,Layvix}"; Flags: nowait postinstall skipifsilent
