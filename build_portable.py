import os
import sys
import subprocess
import shutil

def run_command(cmd, cwd=None):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"Error executing: {cmd}")
        sys.exit(1)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(base_dir, "frontend")
    
    print("=== 0. Cleaning old builds ===")
    old_files = ["build_exe.py", "LayvixPro.spec", "LayvixProPortable.spec"]
    for f in old_files:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed old file: {f}")

    for d in ["build", "dist"]:
        path = os.path.join(base_dir, d)
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"Removed old directory: {d}")
    
    # 1. Build Frontend
    print("\n=== 1. Building React Frontend ===")
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        run_command("npm install", cwd=frontend_dir)
    run_command("npm run build", cwd=frontend_dir)
    
    # 2. PyInstaller Setup
    print("\n=== 2. Running PyInstaller (Portable Single-File) ===")
        
    hidden_imports = [
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "fastapi",
        "pydantic",
        "sklearn",
        "sklearn.linear_model",
        "sklearn.feature_extraction.text",
        "sklearn.utils._murmurhash",
        "sklearn.utils._weight_vector",
        "sklearn.neighbors._partition_nodes",
        "sklearn.tree._utils",
        "scipy.special.cython_special",
        "pynput.keyboard._win32",
        "pynput.mouse._win32",
        "webview.platforms.winforms",
        "webview.platforms.edgechromium"
    ]
    
    hidden_imports_str = " ".join([f"--hidden-import={m}" for m in hidden_imports])
    
    # We must explicitly add frontend/dist and data so they are included in the exe
    datas = [
        ("frontend/dist", "frontend/dist"),
        ("data", "data")
    ]
    
    # PyInstaller syntax for adding data on Windows is "src;dest"
    datas_str = " ".join([f'--add-data "{src};{dst}"' for src, dst in datas])
    
    # --onefile makes it portable, --windowed hides console
    pyinstaller_cmd = (
        f'pyinstaller --noconfirm --onefile --windowed --name "LayvixProPortable" '
        f'--icon="data/icon.ico" {hidden_imports_str} {datas_str} main.py'
    )
    
    run_command(pyinstaller_cmd, cwd=base_dir)
    
    print("\n=== Build Complete ===")
    exe_path = os.path.join(base_dir, 'dist', 'LayvixProPortable.exe')
    if os.path.exists(exe_path):
        print(f"SUCCESS! Portable executable is ready at: {exe_path}")
    else:
        print("FAILED to find executable.")

if __name__ == "__main__":
    main()
