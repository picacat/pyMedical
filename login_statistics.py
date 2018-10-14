#!/usr/bin/env python3
#coding: utf-8


from PyQt5 import QtWidgets, QtGui, QtCore
from libs import nhi_utils
from libs import statistics_utils


# 系統設定 2018.03.19
class LoginStatistics(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(LoginStatistics, self).__init__(parent)
        self.database = args[0]
        self.system_settings = args[1]
        self.parent = parent

        self.statistics_dicts = {
            '本月健保內科人數': 0,
            '本月健保針灸人數': 0,
            '本月健保傷科人數': 0,
            '本月健保首次人數': 0,
            '本月健保看診日數': 0,
            '本月健保針傷限量': 0,
            '本月健保針傷合計': 0,
            '本日健保內科人數': 0,
            '本日健保針灸人數': 0,
            '本日健保傷科人數': 0,
            '本日健保首次人數': 0,
        }

        self._set_ui()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def _set_ui(self):
        self.center()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def start_statistics(self):
        self._calc_general_count()

        self.close()

    def _calc_general_count(self):
        max_progress = 6
        progress_dialog = QtWidgets.QProgressDialog(
            '正在統計資料中, 請稍後...', '取消', 0, max_progress, self
        )

        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        self.statistics_dicts['本月健保內科人數'] = statistics_utils.get_count_by_treat_type(
            self.database, 'cases', '當月', ['內科', '一般'],
        )
        progress_dialog.setValue(1)
        self.statistics_dicts['本月健保針灸人數'] = statistics_utils.get_count_by_treat_type(
            self.database, 'cases', '當月', nhi_utils.ACUPUNCTURE_TREAT,
        )
        progress_dialog.setValue(2)
        self.statistics_dicts['本月健保傷科人數'] = statistics_utils.get_count_by_treat_type(
            self.database, 'cases', '當月', nhi_utils.MASSAGE_TREAT + nhi_utils.DISLOCATE_TREAT
        )
        progress_dialog.setValue(3)
        self.statistics_dicts['本月健保首次人數'] = statistics_utils.get_first_course(
            self.database, 'cases', '當月'
        )

        progress_dialog.setValue(4)
        self.statistics_dicts['本月健保看診日數'] = statistics_utils.get_diag_days(self.database)

        progress_dialog.setValue(5)
        self.statistics_dicts['本月健保針傷限量'] = statistics_utils.get_max_treat(self.database)

        progress_dialog.setValue(max_progress)
