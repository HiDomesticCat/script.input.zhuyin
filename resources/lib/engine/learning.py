# -*- coding: utf-8 -*-
"""
學習模組 - 記錄並學習用戶輸入習慣
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import xbmcaddon
import xbmcvfs


class LearningEngine:
    """用戶習慣學習引擎"""
    
    def __init__(self):
        addon = xbmcaddon.Addon()
        self.profile_path = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
        
        if not os.path.exists(self.profile_path):
            os.makedirs(self.profile_path)
        
        self.stats_file = os.path.join(self.profile_path, 'learning_stats.json')
        
        # 統計資料
        self._phrase_usage: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._bigram_usage: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._session_data: List[Tuple[str, str]] = []
        
        self._load_stats()
    
    def _load_stats(self):
        """載入統計資料"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 還原 defaultdict
                    for zy, phrases in data.get('phrase_usage', {}).items():
                        for phrase, count in phrases.items():
                            self._phrase_usage[zy][phrase] = count
                    
                    for prev, nexts in data.get('bigram_usage', {}).items():
                        for next_char, count in nexts.items():
                            self._bigram_usage[prev][next_char] = count
                            
            except (json.JSONDecodeError, IOError):
                pass  # 使用預設值
    
    def _save_stats(self):
        """儲存統計資料"""
        data = {
            'phrase_usage': {k: dict(v) for k, v in self._phrase_usage.items()},
            'bigram_usage': {k: dict(v) for k, v in self._bigram_usage.items()},
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
    
    def record_selection(self, zhuyin: str, phrase: str, prev_char: str = ""):
        """
        記錄用戶選擇
        
        Args:
            zhuyin: 注音
            phrase: 選擇的詞組
            prev_char: 前一個字（用於 bigram）
        """
        # 記錄詞組使用
        self._phrase_usage[zhuyin][phrase] += 1
        
        # 記錄 bigram（字與字之間的關聯）
        if prev_char and phrase:
            self._bigram_usage[prev_char][phrase[0]] += 1
        
        # 記錄到 session
        self._session_data.append((zhuyin, phrase))
        
        # 定期儲存
        if len(self._session_data) % 10 == 0:
            self._save_stats()
    
    def get_preference_score(self, zhuyin: str, phrase: str) -> int:
        """
        取得用戶偏好分數
        
        Args:
            zhuyin: 注音
            phrase: 詞組
            
        Returns:
            偏好分數（使用次數）
        """
        return self._phrase_usage.get(zhuyin, {}).get(phrase, 0)
    
    def get_bigram_score(self, prev_char: str, next_char: str) -> int:
        """
        取得 bigram 分數
        
        Args:
            prev_char: 前一個字
            next_char: 下一個字
            
        Returns:
            關聯分數
        """
        return self._bigram_usage.get(prev_char, {}).get(next_char, 0)
    
    def get_preferred_phrase(self, zhuyin: str) -> Optional[str]:
        """取得最常用的詞組"""
        phrases = self._phrase_usage.get(zhuyin, {})
        if not phrases:
            return None
        return max(phrases.items(), key=lambda x: x[1])[0]
    
    def get_likely_next_chars(self, prev_char: str, limit: int = 5) -> List[Tuple[str, int]]:
        """
        取得可能的下一個字
        
        Args:
            prev_char: 前一個字
            limit: 最大數量
            
        Returns:
            [(字, 分數), ...]
        """
        nexts = self._bigram_usage.get(prev_char, {})
        if not nexts:
            return []
        
        sorted_nexts = sorted(nexts.items(), key=lambda x: x[1], reverse=True)
        return sorted_nexts[:limit]
    
    def adjust_candidate_scores(self, candidates: list, prev_char: str = "") -> list:
        """
        根據學習資料調整候選詞分數
        
        Args:
            candidates: 候選詞列表（需有 phrase, zhuyin, frequency 屬性）
            prev_char: 前一個字
            
        Returns:
            調整後的候選詞列表
        """
        for candidate in candidates:
            # 加入使用偏好分數
            pref_score = self.get_preference_score(candidate.zhuyin, candidate.phrase)
            candidate.frequency += pref_score * 100
            
            # 加入 bigram 分數
            if prev_char and candidate.phrase:
                bigram_score = self.get_bigram_score(prev_char, candidate.phrase[0])
                candidate.frequency += bigram_score * 50
        
        return candidates
    
    def end_session(self):
        """結束輸入 session，儲存資料"""
        # 這裡可以加入儲存用戶習慣的邏輯
        pass
    
    def clear_learning_data(self):
        """清除所有學習資料"""
        self._phrase_usage.clear()
        self._bigram_usage.clear()
        self._session_data.clear()
        
        if os.path.exists(self.stats_file):
            os.remove(self.stats_file)
    
    def export_data(self, file_path: str):
        """匯出學習資料"""
        data = {
            'phrase_usage': {k: dict(v) for k, v in self._phrase_usage.items()},
            'bigram_usage': {k: dict(v) for k, v in self._bigram_usage.items()},
            'exported_at': datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_data(self, file_path: str, merge: bool = True):
        """
        匯入學習資料
        
        Args:
            file_path: 檔案路徑
            merge: 是否合併（True）或覆蓋（False）
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not merge:
            self._phrase_usage.clear()
            self._bigram_usage.clear()
        
        for zy, phrases in data.get('phrase_usage', {}).items():
            for phrase, count in phrases.items():
                self._phrase_usage[zy][phrase] += count
        
        for prev, nexts in data.get('bigram_usage', {}).items():
            for next_char, count in nexts.items():
                self._bigram_usage[prev][next_char] += count
        
        self._save_stats()
    
    def get_statistics(self) -> dict:
        """取得學習統計"""
        total_phrases = sum(
            sum(phrases.values()) 
            for phrases in self._phrase_usage.values()
        )
        
        unique_phrases = sum(
            len(phrases) 
            for phrases in self._phrase_usage.values()
        )
        
        unique_zhuyin = len(self._phrase_usage)
        
        return {
            'total_selections': total_phrases,
            'unique_phrases': unique_phrases,
            'unique_zhuyin': unique_zhuyin,
            'session_count': len(self._session_data)
        }
