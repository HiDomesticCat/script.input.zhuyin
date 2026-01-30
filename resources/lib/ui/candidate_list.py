# -*- coding: utf-8 -*-
"""
候選字列表 - 管理候選詞的顯示
"""

import xbmcgui
from typing import List, Optional
from ..engine import Candidate


class CandidateListControl:
    """候選詞列表控制"""
    
    def __init__(self, window: xbmcgui.Window, control_id: int):
        """
        初始化候選詞列表
        
        Args:
            window: 父視窗
            control_id: 控制項 ID
        """
        self.window = window
        self.control_id = control_id
        self.candidates: List[Candidate] = []
        self.selected_index = 0
        self.page = 0
        self.page_size = 9
    
    @property
    def control(self) -> Optional[xbmcgui.ControlList]:
        """取得控制項"""
        try:
            return self.window.getControl(self.control_id)
        except:
            return None
    
    def set_candidates(self, candidates: List[Candidate]):
        """設定候選詞列表"""
        self.candidates = candidates
        self.selected_index = 0
        self.page = 0
        self._refresh_display()
    
    def clear(self):
        """清除候選詞"""
        self.candidates = []
        self.selected_index = 0
        self.page = 0
        self._refresh_display()
    
    def _refresh_display(self):
        """更新顯示"""
        control = self.control
        if not control:
            return
        
        control.reset()
        
        # 計算當前頁的候選詞
        start = self.page * self.page_size
        end = min(start + self.page_size, len(self.candidates))
        page_candidates = self.candidates[start:end]
        
        for i, candidate in enumerate(page_candidates):
            display_num = i + 1
            item = xbmcgui.ListItem(f"{display_num}. {candidate.phrase}")
            item.setProperty('zhuyin', candidate.zhuyin)
            item.setProperty('frequency', str(candidate.frequency))
            control.addItem(item)
        
        # 選中當前項
        if page_candidates:
            control.selectItem(self.selected_index % self.page_size)
    
    def select_next(self):
        """選擇下一個"""
        if not self.candidates:
            return
        
        self.selected_index = (self.selected_index + 1) % len(self.candidates)
        
        # 檢查是否需要翻頁
        if self.selected_index // self.page_size != self.page:
            self.page = self.selected_index // self.page_size
            self._refresh_display()
        else:
            control = self.control
            if control:
                control.selectItem(self.selected_index % self.page_size)
    
    def select_previous(self):
        """選擇上一個"""
        if not self.candidates:
            return
        
        self.selected_index = (self.selected_index - 1) % len(self.candidates)
        
        # 檢查是否需要翻頁
        if self.selected_index // self.page_size != self.page:
            self.page = self.selected_index // self.page_size
            self._refresh_display()
        else:
            control = self.control
            if control:
                control.selectItem(self.selected_index % self.page_size)
    
    def select_by_number(self, num: int) -> Optional[Candidate]:
        """
        通過數字選擇候選詞
        
        Args:
            num: 數字 1-9
            
        Returns:
            選中的候選詞，或 None
        """
        if num < 1 or num > self.page_size:
            return None
        
        index = self.page * self.page_size + (num - 1)
        if index >= len(self.candidates):
            return None
        
        self.selected_index = index
        return self.candidates[index]
    
    def get_selected(self) -> Optional[Candidate]:
        """取得當前選中的候選詞"""
        if not self.candidates or self.selected_index >= len(self.candidates):
            return None
        return self.candidates[self.selected_index]
    
    def next_page(self):
        """下一頁"""
        max_page = (len(self.candidates) - 1) // self.page_size
        if self.page < max_page:
            self.page += 1
            self.selected_index = self.page * self.page_size
            self._refresh_display()
    
    def previous_page(self):
        """上一頁"""
        if self.page > 0:
            self.page -= 1
            self.selected_index = self.page * self.page_size
            self._refresh_display()
    
    @property
    def total_pages(self) -> int:
        """總頁數"""
        if not self.candidates:
            return 0
        return (len(self.candidates) - 1) // self.page_size + 1
    
    @property
    def current_page(self) -> int:
        """當前頁碼（從 1 開始）"""
        return self.page + 1
    
    def get_page_info(self) -> str:
        """取得分頁資訊"""
        if not self.candidates:
            return ""
        return f"第 {self.current_page}/{self.total_pages} 頁"


class CandidateBar:
    """候選詞橫條（簡化版本，用於按鍵上方）"""
    
    def __init__(self, window: xbmcgui.Window, control_ids: List[int]):
        """
        初始化候選詞橫條
        
        Args:
            window: 父視窗
            control_ids: 候選詞標籤的控制項 ID 列表
        """
        self.window = window
        self.control_ids = control_ids
        self.candidates: List[Candidate] = []
    
    def set_candidates(self, candidates: List[Candidate]):
        """設定候選詞"""
        self.candidates = candidates[:len(self.control_ids)]
        self._refresh_display()
    
    def clear(self):
        """清除候選詞"""
        self.candidates = []
        self._refresh_display()
    
    def _refresh_display(self):
        """更新顯示"""
        for i, control_id in enumerate(self.control_ids):
            try:
                control = self.window.getControl(control_id)
                if i < len(self.candidates):
                    control.setLabel(f"{i+1}.{self.candidates[i].phrase}")
                    control.setVisible(True)
                else:
                    control.setLabel("")
                    control.setVisible(False)
            except:
                pass
    
    def select(self, num: int) -> Optional[Candidate]:
        """選擇候選詞"""
        if num < 1 or num > len(self.candidates):
            return None
        return self.candidates[num - 1]
