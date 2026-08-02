"""Launch the real V2 desktop app headlessly and capture HIGH-QUALITY screenshots.

Improvements over a plain window.grab():
- The offscreen virtual screen is only ~796x796, so a maximized window gets
  squished and text becomes unreadable. Instead we resize the window to a real
  size (1280x800) and render each widget into a QPixmap at 2x supersampling,
  which is independent of the (tiny) virtual screen and produces crisp,
  full-size images.
- Uses a temp DB (CANTEEN_DB_OVERRIDE) so the real canteen.db is never touched.
"""
import os
import sys
import glob
import uuid

os.environ["QT_QPA_PLATFORM"] = "offscreen"

for f in glob.glob("canteen_run_tmp*.db*"):
    try:
        os.remove(f)
    except OSError:
        pass

TMP_DB = f"canteen_run_tmp_{uuid.uuid4().hex[:8]}.db"
os.environ["CANTEEN_DB_OVERRIDE"] = os.path.abspath(TMP_DB)

from PyQt6.QtWidgets import QApplication, QDialog, QWidget
from PyQt6.QtCore import QTimer, Qt, QRect, QPoint, QSize
from PyQt6.QtGui import QFont, QPainter, QPixmap, QRegion, QColor

from school_canteen.config import get_config
from school_canteen.data.database import initialize_database
from school_canteen.data.models import seed_default_data
from school_canteen.app import build_services
from school_canteen.ui.login_view import LoginDialog
from school_canteen.ui.main_window import MainWindow
from school_canteen.ui.styles import MAIN_STYLE
from school_canteen.core.session import Session

OUT_DIR = "verify_screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

WIN_W, WIN_H = 1280, 800
SCALE = 2  # supersampling for crisp text


def render_widget(w: QWidget, path: str, scale: int = SCALE):
    """Render a widget into a pixmap at (size*scale), independent of the
    virtual screen size. Returns the pixmap."""
    w.resize(w.width(), w.height())  # ensure layout is settled
    pw = max(1, w.width() * scale)
    ph = max(1, w.height() * scale)
    pix = QPixmap(pw, ph)
    pix.fill(QColor("#ffffff"))
    p = QPainter(pix)
    p.scale(scale, scale)
    w.render(p, QPoint(0, 0), QRegion(QRect(0, 0, w.width(), w.height())))
    p.end()
    ok = pix.save(path)
    print(f"  saved {path}  ({pw}x{ph}, ok={ok})")
    return pix


def main():
    print("== initializing database (temp) ==")
    initialize_database()
    seed_default_data()

    app = QApplication(sys.argv)
    app.setApplicationName(get_config().app_name)
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei", 10))
    app.setStyleSheet(MAIN_STYLE)

    print("== building services (real DI) ==")
    services = build_services()

    print("== real login dialog: admin/admin123 ==")
    login = LoginDialog(services["auth"])
    login.username_input.setText("admin")
    login.password_input.setText("admin123")
    login._on_login()
    assert login.current_user is not None, "login failed unexpectedly"
    current_user = login.current_user
    print(f"  logged in as {current_user.username} (role={current_user.role})")
    Session.current_user = current_user

    print("== constructing main window ==")
    window = MainWindow(services, current_user)
    # Resize to a real desktop size BEFORE rendering (offscreen screen is tiny).
    window.resize(WIN_W, WIN_H)
    window.setMinimumSize(0, 0)
    window.show()
    app.processEvents()
    # Re-apply size after show (some styles reset it on first paint).
    window.resize(WIN_W, WIN_H)
    app.processEvents()

    # Full main window at 2x.
    render_widget(window, os.path.join(OUT_DIR, "main_window.png"))

    # Login dialog standalone.
    login2 = LoginDialog(services["auth"])
    login2.resize(380, 340)
    login2.show()
    app.processEvents()
    render_widget(login2, os.path.join(OUT_DIR, "login_dialog.png"))
    login2.close()

    # Render every navigation page at full size.
    print("== rendering all navigation pages ==")
    n = window.nav_list.count()
    for i in range(n):
        window.nav_list.setCurrentRow(i)
        app.processEvents()
        # Make sure the page fills the content area at the window size.
        page = window.pages.get(window.nav_list.item(i).data(Qt.ItemDataRole.UserRole))
        if page is not None:
            # Force the page to the content-area size for a clean render.
            page.resize(window.stacked.width(), window.stacked.height())
            app.processEvents()
            label = window.nav_list.item(i).text()
            safe = label.replace(" ", "_")
            render_widget(page, os.path.join(OUT_DIR, f"page_{i:02d}_{safe}.png"))
            print(f"  [{i:02d}] {label}")

    QTimer.singleShot(400, app.quit)
    rc = app.exec()
    print(f"== app event loop exited cleanly (rc={rc}) ==")


if __name__ == "__main__":
    main()
