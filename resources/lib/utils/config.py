# -*- coding: utf-8 -*-
"""
設定管理 - 管理插件設定
"""

import xbmcaddon
from typing import Any, Optional


class Config:
    """設定管理"""
    
    # 設定鍵名
    KEY_CANDIDATE_COUNT = 'candidate_count'
    KEY_LEARNING_ENABLED = 'learning_enabled'
    KEY_FUZZY_TONE = 'fuzzy_tone'
    KEY_FULL_WIDTH_SYMBOL = 'full_width_symbol'
    KEY_AUTO_COMMIT = 'auto_commit'
    KEY_SHOW_FREQUENCY = 'show_frequency'
    KEY_KEYBOARD_LAYOUT = 'keyboard_layout'
    KEY_HOTKEY = 'hotkey'
    
    # 預設值
    DEFAULTS = {
        KEY_CANDIDATE_COUNT: 9,
        KEY_LEARNING_ENABLED: True,
        KEY_FUZZY_TONE: False,
        KEY_FULL_WIDTH_SYMBOL: True,
        KEY_AUTO_COMMIT: False,
        KEY_SHOW_FREQUENCY: False,
        KEY_KEYBOARD_LAYOUT: 'standard',
        KEY_HOTKEY: 'info',
    }
    
    def __init__(self):
        """初始化設定管理"""
        self._addon = xbmcaddon.Addon()
        self._cache = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        取得設定值
        
        Args:
            key: 設定鍵
            default: 預設值
            
        Returns:
            設定值
        """
        if key in self._cache:
            return self._cache[key]
        
        try:
            value = self._addon.getSetting(key)
            
            # 類型轉換
            default_value = default or self.DEFAULTS.get(key)
            if isinstance(default_value, bool):
                value = value.lower() == 'true'
            elif isinstance(default_value, int):
                value = int(value) if value else default_value
            
            self._cache[key] = value
            return value
            
        except:
            return default or self.DEFAULTS.get(key)
    
    def set(self, key: str, value: Any):
        """
        設定值
        
        Args:
            key: 設定鍵
            value: 設定值
        """
        if isinstance(value, bool):
            str_value = 'true' if value else 'false'
        else:
            str_value = str(value)
        
        self._addon.setSetting(key, str_value)
        self._cache[key] = value
    
    def get_int(self, key: str, default: int = 0) -> int:
        """取得整數設定"""
        return int(self.get(key, default))
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """取得布林設定"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() == 'true'
    
    def get_str(self, key: str, default: str = "") -> str:
        """取得字串設定"""
        return str(self.get(key, default))
    
    # 便捷屬性
    @property
    def candidate_count(self) -> int:
        """候選詞數量"""
        return self.get_int(self.KEY_CANDIDATE_COUNT, 9)
    
    @property
    def learning_enabled(self) -> bool:
        """是否啟用學習"""
        return self.get_bool(self.KEY_LEARNING_ENABLED, True)
    
    @property
    def fuzzy_tone(self) -> bool:
        """是否啟用模糊音"""
        return self.get_bool(self.KEY_FUZZY_TONE, False)
    
    @property
    def full_width_symbol(self) -> bool:
        """是否使用全形符號"""
        return self.get_bool(self.KEY_FULL_WIDTH_SYMBOL, True)
    
    @property
    def auto_commit(self) -> bool:
        """是否自動送出"""
        return self.get_bool(self.KEY_AUTO_COMMIT, False)
    
    @property
    def keyboard_layout(self) -> str:
        """鍵盤佈局"""
        return self.get_str(self.KEY_KEYBOARD_LAYOUT, 'standard')
    
    @property
    def hotkey(self) -> str:
        """快捷鍵"""
        return self.get_str(self.KEY_HOTKEY, 'info')
    
    def clear_cache(self):
        """清除快取"""
        self._cache.clear()
    
    def open_settings(self):
        """開啟設定畫面"""
        self._addon.openSettings()


# 全域設定實例
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """取得全域設定實例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
