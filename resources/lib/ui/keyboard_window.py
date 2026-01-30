# -*- coding: utf-8 -*-
"""
鍵盤視窗控制 - 管理注音鍵盤的顯示與互動
"""

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
from typing import Callable, Optional, List

from ..utils.constants import (
    KEYBOARD_LAYOUT, KEYBOARD_ROWS, KEYBOARD_COLS,
    FUNC_KEYS, InputState, SYMBOLS_FULL, SYMBOLS_HALF,
    TONE_MARKS
)
from ..engine import ZhuyinParser, SmartCandidateEngine, Candidate


# 控制項 ID
CONTROL_INPUT_LABEL = 100
CONTROL_CANDIDATE_LIST = 200
CONTROL_KEYBOARD_GROUP = 300
CONTROL_KEY_BASE = 1000  # 按鍵從 1000 開始
CONTROL_STATUS_LABEL = 400


class ZhuyinKeyboardWindow(xbmcgui.WindowXMLDialog):
    """注音鍵盤視窗"""
    
    def __init__(self, *args, **kwargs):
        self.callback: Optional[Callable[[str], None]] = kwargs.pop('callback', None)
        self.initial_text: str = kwargs.pop('initial_text', '')
        
        super().__init__(*args, **kwargs)
        
        # 引擎
        self.parser = ZhuyinParser()
        self.engine = SmartCandidateEngine()
        
        # 狀態
        self.state = InputState.IDLE
        self.current_input = ""      # 當前注音輸入
        self.committed_text = ""     # 已確認的文字
        self.candidates: List[Candidate] = []
        self.selected_candidate_index = 0
        
        # 鍵盤位置
        self.key_row = 0
        self.key_col = 0
        
        # 符號模式
        self.symbol_mode = False
        self.symbol_full_width = True
    
    def onInit(self):
        """視窗初始化"""
        self.committed_text = self.initial_text
        self._update_display()
        self._focus_key(self.key_row, self.key_col)
    
    def onAction(self, action):
        """處理遙控器動作"""
        action_id = action.getId()
        
        # 返回/刪除
        if action_id in (xbmcgui.ACTION_PREVIOUS_MENU,
                          xbmcgui.ACTION_NAV_BACK):
            if self.current_input:
                self._delete_last()
            elif self.committed_text:
                self._delete_last_committed()
            else:
                self._cancel()
        
        # 數字鍵快選候選詞
        elif action_id >= xbmcgui.REMOTE_0 and action_id <= xbmcgui.REMOTE_9:
            num = action_id - xbmcgui.REMOTE_0
            if num > 0 and num <= len(self.candidates):
                self._select_candidate(num - 1)
        
        # 長按確認 - 送出文字
        elif action_id == xbmcgui.ACTION_SHOW_INFO:
            self._confirm_all()
    
    def onClick(self, control_id):
        """處理點擊事件"""
        if control_id >= CONTROL_KEY_BASE:
            key_index = control_id - CONTROL_KEY_BASE
            row = key_index // KEYBOARD_COLS
            col = key_index % KEYBOARD_COLS
            
            # 更新當前按鍵位置
            self.key_row = row
            self.key_col = col
            
            # 處理特殊按鍵 (ABC)
            if control_id == 1044:
                self._on_abc()
            else:
                self._on_key_press()
        
        elif control_id >= 200 and control_id < 300:
            # 候選詞點擊
            candidate_index = control_id - 200
            if candidate_index < len(self.candidates):
                self._select_candidate(candidate_index)
    
    def _move_focus(self, row_delta: int, col_delta: int):
        """移動焦點"""
        new_row = (self.key_row + row_delta) % KEYBOARD_ROWS
        new_col = (self.key_col + col_delta) % KEYBOARD_COLS
        
        # 跳過空按鍵
        while KEYBOARD_LAYOUT[new_row][new_col] == '':
            new_col = (new_col + col_delta) % KEYBOARD_COLS
            if new_col == self.key_col:
                break
        
        self.key_row = new_row
        self.key_col = new_col
        self._focus_key(new_row, new_col)
    
    def _focus_key(self, row: int, col: int):
        """設定焦點到指定按鍵"""
        control_id = CONTROL_KEY_BASE + row * KEYBOARD_COLS + col
        self.setFocusId(control_id)
    
    def _on_key_press(self):
        """處理按鍵按下"""
        # 確保索引在範圍內
        if self.key_row >= len(KEYBOARD_LAYOUT) or self.key_col >= len(KEYBOARD_LAYOUT[0]):
            return

        key = KEYBOARD_LAYOUT[self.key_row][self.key_col]
        
        if not key:
            return
        
        # 功能鍵處理
        if key == '符號':
            self._toggle_symbol_mode()
        elif key == '空格':
            self._on_space()
        elif key == '刪除':
            self._delete_last()
        elif key == '確認':
            self._confirm_all()
        elif key == 'ㄦ':
            self._input_zhuyin('ㄦ')
        else:
            # 注音符號或聲調
            self._input_zhuyin(key)

    def _on_abc(self):
        """切換到英文輸入 (呼叫原生鍵盤)"""
        # 呼叫原生鍵盤，傳入當前已確認的文字
        keyboard = xbmc.Keyboard(self.committed_text, "English Input")
        keyboard.doModal()
        
        if keyboard.isConfirmed():
            # 更新文字
            new_text = keyboard.getText()
            if new_text:
                self.committed_text = new_text
                self._update_display()
    
    def _input_zhuyin(self, char: str):
        """輸入注音符號"""
        if self.symbol_mode:
            # 符號模式
            self._input_symbol(char)
            return
        
        self.current_input += char
        self.state = InputState.COMPOSING
        
        # 如果是聲調，嘗試完成音節
        if char in TONE_MARKS[1:]:
            self._complete_syllable()
        else:
            self._update_candidates()
        
        self._update_display()
    
    def _complete_syllable(self):
        """完成當前音節，進入選字"""
        if self.candidates:
            self.state = InputState.SELECTING
            self.selected_candidate_index = 0
    
    def _on_space(self):
        """空格鍵處理"""
        if self.state == InputState.SELECTING and self.candidates:
            # 選字狀態：選擇第一個候選詞
            self._select_candidate(0)
        elif self.state == InputState.COMPOSING:
            # 組字狀態：嘗試完成音節（一聲）
            self._complete_syllable()
            if self.candidates:
                self._select_candidate(0)
        else:
            # 待機狀態：輸入空格
            self.committed_text += ' '
            self._update_display()
    
    def _select_candidate(self, index: int):
        """選擇候選詞"""
        if index < 0 or index >= len(self.candidates):
            return
        
        candidate = self.candidates[index]
        
        # 記錄選擇（學習）
        self.engine.commit_and_record(candidate)
        
        # 加入已確認文字
        self.committed_text += candidate.phrase
        
        # 清除當前輸入
        self.current_input = ""
        self.candidates = []
        self.state = InputState.IDLE
        
        self._update_display()
    
    def _update_candidates(self):
        """更新候選詞列表"""
        if not self.current_input:
            self.candidates = []
            return
        
        self.candidates = self.engine.get_candidates_smart(self.current_input)
    
    def _delete_last(self):
        """刪除最後一個輸入"""
        if self.current_input:
            self.current_input = self.current_input[:-1]
            if self.current_input:
                self._update_candidates()
            else:
                self.candidates = []
                self.state = InputState.IDLE
            self._update_display()
    
    def _delete_last_committed(self):
        """刪除最後一個已確認的字"""
        if self.committed_text:
            self.committed_text = self.committed_text[:-1]
            self._update_display()
    
    def _toggle_symbol_mode(self):
        """切換符號模式"""
        self.symbol_mode = not self.symbol_mode
        self._update_keyboard_display()
    
    def _input_symbol(self, key: str):
        """輸入符號"""
        # 在符號模式下，按鍵對應符號
        symbols = SYMBOLS_FULL if self.symbol_full_width else SYMBOLS_HALF
        
        # 簡單映射：使用位置對應
        key_index = self.key_row * KEYBOARD_COLS + self.key_col
        if key_index < len(symbols):
            self.committed_text += symbols[key_index]
            self._update_display()
    
    def _confirm_all(self):
        """確認所有輸入並關閉"""
        # 如果還有未確認的輸入
        if self.current_input and self.candidates:
            self._select_candidate(0)
        
        # 呼叫回調
        if self.callback:
            self.callback(self.committed_text)
        
        # 結束學習 session
        self.engine.engine.end_session() if hasattr(self.engine, 'engine') else None
        
        self.close()
    
    def _cancel(self):
        """取消輸入"""
        if self.callback:
            self.callback(None)
        self.close()
    
    def _update_display(self):
        """更新顯示"""
        # 更新輸入列
        input_label = self.getControl(CONTROL_INPUT_LABEL)
        if input_label:
            display_text = self.committed_text
            if self.current_input:
                display_text += f"[{self.current_input}]"
            input_label.setLabel(display_text)
        
        # 更新候選詞
        self._update_candidate_display()
        
        # 更新狀態
        status_label = self.getControl(CONTROL_STATUS_LABEL)
        if status_label:
            status_text = self._get_status_text()
            status_label.setLabel(status_text)
    
    def _update_candidate_display(self):
        """更新候選詞顯示"""
        for i in range(9):
            control_id = 200 + i
            try:
                control = self.getControl(control_id)
                if i < len(self.candidates):
                    control.setLabel(f"{i+1}.{self.candidates[i].phrase}")
                    control.setVisible(True)
                else:
                    control.setLabel("")
                    control.setVisible(False)
            except:
                pass
    
    def _update_keyboard_display(self):
        """更新鍵盤顯示（符號模式切換）"""
        symbols = SYMBOLS_FULL if self.symbol_full_width else SYMBOLS_HALF
        
        for row in range(KEYBOARD_ROWS):
            for col in range(KEYBOARD_COLS):
                # 跳過功能鍵列 (最後一列)
                if row == KEYBOARD_ROWS - 1:
                    continue
                    
                control_id = CONTROL_KEY_BASE + row * KEYBOARD_COLS + col
                try:
                    button = self.getControl(control_id)
                    if self.symbol_mode:
                        # 計算符號索引
                        index = row * KEYBOARD_COLS + col
                        if index < len(symbols):
                            button.setLabel(symbols[index])
                        else:
                            button.setLabel("")
                    else:
                        # 還原注音符號
                        char = KEYBOARD_LAYOUT[row][col]
                        button.setLabel(char)
                except:
                    pass
        
        # 更新功能鍵標籤
        try:
            symbol_btn = self.getControl(CONTROL_KEY_BASE + 40) # 符號鍵
            if self.symbol_mode:
                symbol_btn.setLabel("注音")
            else:
                symbol_btn.setLabel("符號")
        except:
            pass
    
    def _get_status_text(self) -> str:
        """取得狀態文字"""
        if self.symbol_mode:
            return "符號模式 | 按[符號]返回注音"
        elif self.state == InputState.SELECTING:
            return "選字中 | 數字鍵選字 | 空格選第一個"
        elif self.state == InputState.COMPOSING:
            return "輸入中 | 聲調完成音節"
        else:
            return "注音輸入法 | 方向鍵移動 | 確認鍵輸入"


def show_zhuyin_keyboard(callback: Callable[[str], None] = None,
                         initial_text: str = "") -> Optional[str]:
    """
    顯示注音鍵盤
    
    Args:
        callback: 輸入完成的回調函數
        initial_text: 初始文字
        
    Returns:
        輸入的文字（無回調時）
    """
    addon = xbmcaddon.Addon()
    addon_path = xbmcvfs.translatePath(addon.getAddonInfo('path'))
    
    result = [None]
    
    def _callback(text):
        result[0] = text
        if callback:
            callback(text)
    
    window = ZhuyinKeyboardWindow(
        'script-zhuyin-keyboard.xml',
        addon_path,
        'default',
        '1080i',
        callback=_callback,
        initial_text=initial_text
    )
    
    window.doModal()
    del window
    
    return result[0]
