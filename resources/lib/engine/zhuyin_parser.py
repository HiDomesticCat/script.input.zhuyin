# -*- coding: utf-8 -*-
"""
注音解析器 - 處理注音符號的組合與驗證
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from ..utils.constants import INITIALS, MEDIALS, FINALS, TONES, TONE_MARKS


@dataclass
class ZhuyinSyllable:
    """注音音節結構"""
    initial: str = ""      # 聲母
    medial: str = ""       # 介音
    final: str = ""        # 韻母
    tone: str = ""         # 聲調
    raw: str = ""          # 原始輸入
    
    def __str__(self) -> str:
        return f"{self.initial}{self.medial}{self.final}{self.tone}"
    
    def is_complete(self) -> bool:
        """檢查是否為完整音節（有聲調表示完成）"""
        return bool(self.tone) or self._is_valid_standalone()
    
    def _is_valid_standalone(self) -> bool:
        """檢查是否為可獨立的音節"""
        # ㄓㄔㄕㄖㄗㄘㄙ 可單獨成音
        if self.initial in ['ㄓ', 'ㄔ', 'ㄕ', 'ㄖ', 'ㄗ', 'ㄘ', 'ㄙ'] and not self.medial and not self.final:
            return True
        # 有韻母即可成音
        return bool(self.final) or bool(self.medial)
    
    def is_empty(self) -> bool:
        return not (self.initial or self.medial or self.final or self.tone)
    
    def to_search_key(self) -> str:
        """轉換為資料庫搜尋鍵（不含聲調）"""
        return f"{self.initial}{self.medial}{self.final}"


class ZhuyinParser:
    """注音解析器"""
    
    def __init__(self):
        self.initials = set(INITIALS)
        self.medials = set(MEDIALS)
        self.finals = set(FINALS)
        self.tones = set(TONE_MARKS[1:])  # 不含一聲空白
        
        # 建立有效組合表
        self._build_valid_combinations()
    
    def _build_valid_combinations(self):
        """建立有效的注音組合"""
        # 這裡可以加入更複雜的規則
        # 例如：ㄐㄑㄒ 只能配 ㄧㄩ
        self.jqx_constraint = {'ㄐ', 'ㄑ', 'ㄒ'}
        self.jqx_medials = {'ㄧ', 'ㄩ'}
        
        # ㄓㄔㄕㄖㄗㄘㄙ 不能配 ㄩ
        self.zhi_group = {'ㄓ', 'ㄔ', 'ㄕ', 'ㄖ', 'ㄗ', 'ㄘ', 'ㄙ'}
    
    def parse(self, input_sequence: str) -> List[ZhuyinSyllable]:
        """
        解析輸入的注音符號序列
        
        Args:
            input_sequence: 注音符號字串
            
        Returns:
            解析後的音節列表
        """
        syllables = []
        current = ZhuyinSyllable()
        
        i = 0
        while i < len(input_sequence):
            char = input_sequence[i]
            
            # 空格作為分隔符
            if char == ' ':
                if not current.is_empty():
                    current.raw = str(current)
                    syllables.append(current)
                    current = ZhuyinSyllable()
                i += 1
                continue
            
            # 聲調 - 完成當前音節
            if char in self.tones:
                current.tone = char
                current.raw = str(current)
                syllables.append(current)
                current = ZhuyinSyllable()
                i += 1
                continue
            
            # 聲母
            if char in self.initials:
                # 如果當前已有聲母，開始新音節
                if current.initial:
                    current.raw = str(current)
                    syllables.append(current)
                    current = ZhuyinSyllable()
                current.initial = char
                i += 1
                continue
            
            # 介音
            if char in self.medials:
                # 檢查是否應該開始新音節
                if current.medial or current.final:
                    current.raw = str(current)
                    syllables.append(current)
                    current = ZhuyinSyllable()
                current.medial = char
                i += 1
                continue
            
            # 韻母
            if char in self.finals:
                if current.final:
                    current.raw = str(current)
                    syllables.append(current)
                    current = ZhuyinSyllable()
                current.final = char
                i += 1
                continue
            
            # 未知字符，跳過
            i += 1
        
        # 處理最後一個音節
        if not current.is_empty():
            current.raw = str(current)
            syllables.append(current)
        
        return syllables
    
    def parse_single(self, input_str: str) -> Optional[ZhuyinSyllable]:
        """解析單一音節"""
        syllables = self.parse(input_str)
        return syllables[0] if syllables else None
    
    def validate(self, syllable: ZhuyinSyllable) -> Tuple[bool, str]:
        """
        驗證音節是否有效
        
        Returns:
            (是否有效, 錯誤訊息)
        """
        # ㄐㄑㄒ 只能配 ㄧㄩ
        if syllable.initial in self.jqx_constraint:
            if syllable.medial and syllable.medial not in self.jqx_medials:
                return False, f"{syllable.initial} 不能與 {syllable.medial} 組合"
            if not syllable.medial and syllable.final:
                # ㄐㄑㄒ 必須有 ㄧ 或 ㄩ
                return False, f"{syllable.initial} 需要介音 ㄧ 或 ㄩ"
        
        # ㄓㄔㄕㄖㄗㄘㄙ 不能配 ㄩ
        if syllable.initial in self.zhi_group and syllable.medial == 'ㄩ':
            return False, f"{syllable.initial} 不能與 ㄩ 組合"
        
        return True, ""
    
    def get_possible_completions(self, partial: str) -> List[str]:
        """
        取得可能的補全選項
        
        Args:
            partial: 部分輸入的注音
            
        Returns:
            可能的下一個符號列表
        """
        syllable = self.parse_single(partial)
        if not syllable:
            # 空輸入，可以是聲母或介音
            return list(self.initials) + list(self.medials)
        
        completions = []
        
        # 根據當前狀態推薦
        if syllable.initial and not syllable.medial and not syllable.final:
            # 只有聲母
            if syllable.initial in self.jqx_constraint:
                completions.extend(['ㄧ', 'ㄩ'])
            elif syllable.initial in self.zhi_group:
                completions.extend(['ㄧ', 'ㄨ'])
                completions.extend(self.finals)
                completions.extend(self.tones)
            else:
                completions.extend(self.medials)
                completions.extend(self.finals)
                completions.extend(self.tones)
        
        elif syllable.medial and not syllable.final:
            # 有介音無韻母
            completions.extend(self.finals)
            completions.extend(self.tones)
        
        elif syllable.final:
            # 有韻母，只能加聲調
            completions.extend(self.tones)
        
        return completions
    
    def normalize(self, zhuyin: str) -> str:
        """正規化注音字串"""
        syllables = self.parse(zhuyin)
        return ' '.join(str(s) for s in syllables)
    
    def split_syllables(self, zhuyin: str) -> List[str]:
        """將注音字串分割為音節列表"""
        syllables = self.parse(zhuyin)
        return [str(s) for s in syllables]
    
    def get_tone(self, syllable_str: str) -> int:
        """取得音節的聲調數字 (1-5)"""
        if not syllable_str:
            return 1
        last_char = syllable_str[-1]
        return TONES.get(last_char, 1)
    
    def remove_tone(self, syllable_str: str) -> str:
        """移除聲調符號"""
        if syllable_str and syllable_str[-1] in self.tones:
            return syllable_str[:-1]
        return syllable_str
