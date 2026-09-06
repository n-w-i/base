import subprocess


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def send_notification(title: str, message: str, subtitle: str | None = None) -> bool:
    script = f'display notification "{_escape(message)}" with title "{_escape(title)}"'
    if subtitle:
        script += f' subtitle "{_escape(subtitle)}"'
    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=10)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False
