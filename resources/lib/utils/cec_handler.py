# -*- coding: utf-8 -*-
"""
CEC 按鍵處理 - 處理 HDMI-CEC 遙控器按鍵
"""

import xbmc
import xbmcgui
from typing import Dict, Callable, Optional
from .constants import CEC_KEYS


class CECHandler:
    """CEC 按鍵處理器"""
    
    # Kodi 動作 ID 對照
    ACTION_MAP = {
        xbmcgui.ACTION_SELECT_ITEM: 'select',
        xbmcgui.ACTION_MOVE_UP: 'up',
        xbmcgui.ACTION_MOVE_DOWN: 'down',
        xbmcgui.ACTION_MOVE_LEFT: 'left',
        xbmcgui.ACTION_MOVE_RIGHT: 'right',
        xbmcgui.ACTION_PREVIOUS_MENU: 'back',
        xbmcgui.ACTION_NAV_BACK: 'back',
        xbmcgui.ACTION_PARENT_DIR: 'back',
        xbmcgui.ACTION_STOP: 'stop',
        xbmcgui.ACTION_PAUSE: 'pause',
        xbmcgui.ACTION_PLAYER_PLAY: 'play',
    }
    
    # 數字鍵對照
    NUMBER_ACTIONS = {
        xbmcgui.REMOTE_0: 0,
        xbmcgui.REMOTE_1: 1,
        xbmcgui.REMOTE_2: 2,
        xbmcgui.REMOTE_3: 3,
        xbmcgui.REMOTE_4: 4,
        xbmcgui.REMOTE_5: 5,
        xbmcgui.REMOTE_6: 6,
        xbmcgui.REMOTE_7: 7,
        xbmcgui.REMOTE_8: 8,
        xbmcgui.REMOTE_9: 9,
    }
    
    # 顏色鍵對照
    COLOR_ACTIONS = {
        xbmcgui.ACTION_TELETEXT_RED: 'red',
        xbmcgui.ACTION_TELETEXT_GREEN: 'green',
        xbmcgui.ACTION_TELETEXT_YELLOW: 'yellow',
        xbmcgui.ACTION_TELETEXT_BLUE: 'blue',
    }
    
    def __init__(self):
        """初始化 CEC 處理器"""
        self.callbacks: Dict[str, Callable] = {}
        self.number_callback: Optional[Callable[[int], None]] = None
        self.long_press_callback: Optional[Callable[[str], None]] = None
        
        # 長按檢測
        self._last_action = None
        self._press_count = 0
        self._long_press_threshold = 3
    
    def register_callback(self, key: str, callback: Callable):
        """
        註冊按鍵回調
        
        Args:
            key: 按鍵名稱 ('select', 'up', 'down', 等)
            callback: 回調函數
        """
        self.callbacks[key] = callback
    
    def register_number_callback(self, callback: Callable[[int], None]):
        """註冊數字鍵回調"""
        self.number_callback = callback
    
    def register_long_press_callback(self, callback: Callable[[str], None]):
        """註冊長按回調"""
        self.long_press_callback = callback
    
    def handle_action(self, action: xbmcgui.Action) -> bool:
        """
        處理動作
        
        Args:
            action: Kodi 動作
            
        Returns:
            是否已處理
        """
        action_id = action.getId()
        
        # 檢查長按
        if action_id == self._last_action:
            self._press_count += 1
            if self._press_count >= self._long_press_threshold:
                if self.long_press_callback:
                    key_name = self._get_key_name(action_id)
                    if key_name:
                        self.long_press_callback(key_name)
                        self._press_count = 0
                        return True
        else:
            self._last_action = action_id
            self._press_count = 1
        
        # 處理數字鍵
        if action_id in self.NUMBER_ACTIONS:
            num = self.NUMBER_ACTIONS[action_id]
            if self.number_callback:
                self.number_callback(num)
                return True
        
        # 處理一般按鍵
        key_name = self._get_key_name(action_id)
        if key_name and key_name in self.callbacks:
            self.callbacks[key_name]()
            return True
        
        # 處理顏色鍵
        if action_id in self.COLOR_ACTIONS:
            color = self.COLOR_ACTIONS[action_id]
            if color in self.callbacks:
                self.callbacks[color]()
                return True
        
        return False
    
    def _get_key_name(self, action_id: int) -> Optional[str]:
        """取得按鍵名稱"""
        return self.ACTION_MAP.get(action_id)
    
    def clear_callbacks(self):
        """清除所有回調"""
        self.callbacks.clear()
        self.number_callback = None
        self.long_press_callback = None


class KeyboardNavigation:
    """鍵盤導航助手"""
    
    def __init__(self, rows: int, cols: int, 
                 skip_cells: list = None):
        """
        初始化鍵盤導航
        
        Args:
            rows: 列數
            cols: 欄數
            skip_cells: 要跳過的格子 [(row, col), ...]
        """
        self.rows = rows
        self.cols = cols
        self.skip_cells = set(skip_cells or [])
        
        self.current_row = 0
        self.current_col = 0
    
    def move(self, row_delta: int, col_delta: int) -> tuple:
        """
        移動位置
        
        Args:
            row_delta: 列變化
            col_delta: 欄變化
            
        Returns:
            (new_row, new_col)
        """
        new_row = self.current_row
        new_col = self.current_col
        
        # 嘗試移動
        if row_delta != 0:
            new_row = (self.current_row + row_delta) % self.rows
        if col_delta != 0:
            new_col = (self.current_col + col_delta) % self.cols
        
        # 跳過無效格子
        attempts = 0
        while (new_row, new_col) in self.skip_cells:
            if col_delta != 0:
                new_col = (new_col + (1 if col_delta > 0 else -1)) % self.cols
            elif row_delta != 0:
                new_row = (new_row + (1 if row_delta > 0 else -1)) % self.rows
            
            attempts += 1
            if attempts > self.rows * self.cols:
                break
        
        self.current_row = new_row
        self.current_col = new_col
        
        return (new_row, new_col)
    
    def move_up(self) -> tuple:
        return self.move(-1, 0)
    
    def move_down(self) -> tuple:
        return self.move(1, 0)
    
    def move_left(self) -> tuple:
        return self.move(0, -1)
    
    def move_right(self) -> tuple:
        return self.move(0, 1)
    
    def set_position(self, row: int, col: int):
        """設定位置"""
        self.current_row = max(0, min(row, self.rows - 1))
        self.current_col = max(0, min(col, self.cols - 1))
    
    def get_position(self) -> tuple:
        """取得當前位置"""
        return (self.current_row, self.current_col)
    
    def get_linear_index(self) -> int:
        """取得線性索引"""
        return self.current_row * self.cols + self.current_col
