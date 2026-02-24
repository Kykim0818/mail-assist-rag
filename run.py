"""
Mail Assistant — 원클릭 실행 스크립트

Usage:
    python run.py          # 백엔드(8000) + 프론트엔드(5173) 동시 실행
    python run.py --backend   # 백엔드만
    python run.py --frontend  # 프론트엔드만
"""

import subprocess
import sys
import os
import signal
import platform

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")

IS_WIN = platform.system() == "Windows"

# venv python 경로
if IS_WIN:
    VENV_PYTHON = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
else:
    VENV_PYTHON = os.path.join(BACKEND_DIR, ".venv", "bin", "python")


def find_npx():
    """npx 실행 가능한지 확인"""
    import shutil
    return shutil.which("npx") is not None


def start_backend():
    """백엔드 서버 시작 (uvicorn)"""
    if not os.path.exists(VENV_PYTHON):
        print(f"❌ venv을 찾을 수 없습니다: {VENV_PYTHON}")
        print("   먼저 backend/ 에서 python -m venv .venv && pip install -r requirements.txt 를 실행하세요.")
        sys.exit(1)

    print("🚀 백엔드 서버 시작 (http://localhost:8000)")
    return subprocess.Popen(
        [VENV_PYTHON, "-m", "uvicorn", "backend.main:app", "--port", "8000", "--reload"],
        cwd=ROOT,
    )


def start_frontend():
    """프론트엔드 서버 시작 (vite)"""
    if not find_npx():
        print("❌ npx를 찾을 수 없습니다. Node.js가 설치되어 있는지 확인하세요.")
        sys.exit(1)

    node_modules = os.path.join(FRONTEND_DIR, "node_modules")
    if not os.path.exists(node_modules):
        print("📦 frontend/node_modules 없음 — npm install 실행 중...")
        subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, check=True, shell=IS_WIN)

    print("🚀 프론트엔드 서버 시작 (http://localhost:5173)")
    return subprocess.Popen(
        ["npx", "vite", "--port", "5173"],
        cwd=FRONTEND_DIR,
        shell=IS_WIN,
    )


def main():
    args = set(sys.argv[1:])
    run_backend = "--frontend" not in args
    run_frontend = "--backend" not in args

    processes = []

    try:
        if run_backend:
            processes.append(("backend", start_backend()))
        if run_frontend:
            processes.append(("frontend", start_frontend()))

        if not processes:
            print("실행할 서버가 없습니다.")
            return

        print()
        print("=" * 50)
        print("  Mail Assistant 실행 중")
        print("  백엔드:      http://localhost:8000")
        print("  프론트엔드:  http://localhost:5173")
        print("  API 문서:    http://localhost:8000/docs")
        print("  종료: Ctrl+C")
        print("=" * 50)
        print()

        # 아무 프로세스라도 끝나면 감지
        for name, proc in processes:
            proc.wait()

    except KeyboardInterrupt:
        print("\n⏹ 서버 종료 중...")
    finally:
        for name, proc in processes:
            if proc.poll() is None:
                if IS_WIN:
                    proc.terminate()
                else:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait()
        print("✅ 모든 서버가 종료되었습니다.")


if __name__ == "__main__":
    main()
