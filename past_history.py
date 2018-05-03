
from PyQt5 import QtWidgets
import sys
from classes import system_settings, db
from libs import ui_settings
from libs import system


# 主畫面
class PastHistory(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, *args):
        super(PastHistory, self).__init__(*args)
        self.database = db.Database()
        if not self.database.connected():
            sys.exit(0)

        self.system_settings = system_settings.SystemSettings(self.database)
        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_PAST_HISTORY, self)
        system.set_css(self)
        system.set_theme(self.ui, self.system_settings)

    # 設定信號
    def _set_signal(self):
        pass
