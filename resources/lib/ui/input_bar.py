# -*- coding: utf-8 -*-
"""
輸入狀態列 - 顯示當前輸入狀態
"""

import xbmcgui
from typing import Optional
from ..utils.constants import InputState


class InputBar:
    """輸入狀態列"""
    
    def __init__(self, window: xbmcgui.Window, 
                 text_control_id: int,
                 zhuyin_control_id: int,
                 status_control_id: int):
        """
        初始化輸入狀態列
        
        Args:
            window: 父視窗
            text_control_id: 已確認文字標籤 ID
            zhuyin_control_id: 注音輸入標籤 ID
            status_control_id: 狀態標籤 ID
        """
        self.window = window
        self.text_control_id = text_control_id
        self.zhuyin_control_id = zhuyin_control_id
        self.status_control_id = status_control_id
        
        self.committed_text = ""
        self.current_zhuyin = ""
        self.state = InputState.IDLE
    
    def _get_control(self, control_id: int) -> Optional[xbmcgui.ControlLabel]:
        """取得控制項"""
        try:
            return self.window.getControl(control_id)
        except:
            return None
    
    def set_committed_text(self, text: str):
        """設定已確認的文字"""
        self.committed_text = text
        self._update_text_display()
    
    def append_text(self, text: str):
        """附加文字"""
        self.committed_text += text
        self._update_text_display()
    
    def delete_last_char(self) -> bool:
        """
        刪除最後一個字
        
        Returns:
            是否有刪除
        """
        if self.committed_text:
            self.committed_text = self.committed_text[:-1]
            self._update_text_display()
            return True
        return False
    
    def set_current_zhuyin(self, zhuyin: str):
        """設定當前注音"""
        self.current_zhuyin = zhuyin
        self._update_zhuyin_display()
    
    def append_zhuyin(self, char: str):
        """附加注音符號"""
        self.current_zhuyin += char
        self._update_zhuyin_display()
    
    def delete_last_zhuyin(self) -> bool:
        """
        刪除最後一個注音符號
        
        Returns:
            是否有刪除
        """
        if self.current_zhuyin:
            self.current_zhuyin = self.current_zhuyin[:-1]
            self._update_zhuyin_display()
            return True
        return False
    
    def clear_zhuyin(self):
        """清除注音"""
        self.current_zhuyin = ""
        self._update_zhuyin_display()
    
    def set_state(self, state: InputState):
        """設定輸入狀態"""
        self.state = state
        self._update_status_display()
    
    def _update_text_display(self):
        """更新已確認文字顯示"""
        control = self._get_control(self.text_control_id)
        if control:
            # 顯示文字，若過長則只顯示後面部分
            display_text = self.committed_text
            if len(display_text) > 30:
                display_text = "..." + display_text[-27:]
            control.setLabel(display_text)
    
    def _update_zhuyin_display(self):
        """更新注音顯示"""
        control = self._get_control(self.zhuyin_control_id)
        if control:
            if self.current_zhuyin:
                control.setLabel(f"[{self.current_zhuyin}]")
            else:
                control.setLabel("")
    
    def _update_status_display(self):
        """更新狀態顯示"""
        control = self._get_control(self.status_control_id)
        if control:
            status_text = self._get_status_text()
            control.setLabel(status_text)
    
    def _get_status_text(self) -> str:
        """取得狀態文字"""
        status_map = {
            InputState.IDLE: "待機",
            InputState.COMPOSING: "組字中",
            InputState.SELECTING: "選字中",
        }
        return status_map.get(self.state, "")
    
    def get_full_text(self) -> str:
        """取得完整文字（已確認 + 當前）"""
        return self.committed_text
    
    def get_display_text(self) -> str:
        """取得顯示用文字"""
        if self.current_zhuyin:
            return f"{self.committed_text}[{self.current_zhuyin}]"
        return self.committed_text
    
    def clear_all(self):
        """清除所有"""
        self.committed_text = ""
        self.current_zhuyin = ""
        self.state = InputState.IDLE
        self._update_text_display()
        self._update_zhuyin_display()
        self._update_status_display()
    
    def update_all(self):
        """更新所有顯示"""
        self._update_text_display()
        self._update_zhuyin_display()
        self._update_status_display()


class CompactInputBar:
    """精簡輸入狀態列（單一標籤）"""
    
    def __init__(self, window: xbmcgui.Window, control_id: int):
        """
        初始化精簡輸入狀態列
        
        Args:
            window: 父視窗
            control_id: 控制項 ID
        """
        self.window = window
        self.control_id = control_id
        
        self.committed_text = ""
        self.current_zhuyin = ""
    
    def _get_control(self) -> Optional[xbmcgui.ControlLabel]:
        """取得控制項"""
        try:
            return self.window.getControl(self.control_id)
        except:
            return None
    
    def update(self, committed: str = None, zhuyin: str = None):
        """
        更新顯示
        
        Args:
            committed: 已確認文字（None 表示不變）
            zhuyin: 當前注音（None 表示不變）
        """
        if committed is not None:
            self.committed_text = committed
        if zhuyin is not None:
            self.current_zhuyin = zhuyin
        
        self._refresh_display()
    
    def _refresh_display(self):
        """刷新顯示"""
        control = self._get_control()
        if not control:
            return
        
        display_text = self.committed_text
        if self.current_zhuyin:
            display_text += f" [{self.current_zhuyin}]"
        
        # 處理過長文字
        max_len = 40
        if len(display_text) > max_len:
            # 保留後面的文字
            cut_pos = len(display_text) - max_len + 3
            display_text = "..." + display_text[cut_pos:]
        
        control.setLabel(display_text)
    
    def clear(self):
        """清除"""
        self.committed_text = ""
        self.current_zhuyin = ""
        self._refresh_display()
