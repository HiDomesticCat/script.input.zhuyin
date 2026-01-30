# -*- coding: utf-8 -*-
"""
候選字引擎 - 管理候選字詞的產生與排序
"""

from dataclasses import dataclass
from typing import List, Optional
from .zhuyin_parser import ZhuyinParser, ZhuyinSyllable
from .phrase_db import PhraseDatabase, UserPhraseDatabase


@dataclass
class Candidate:
    """候選詞結構"""
    phrase: str           # 詞組文字
    zhuyin: str           # 對應注音
    frequency: int        # 詞頻
    source: str           # 來源: 'system', 'user', 'learned'
    is_exact: bool        # 是否完全匹配
    
    def __str__(self) -> str:
        return self.phrase


class CandidateEngine:
    """候選字引擎"""
    
    def __init__(self, phrase_db: Optional[PhraseDatabase] = None,
                 user_db: Optional[UserPhraseDatabase] = None):
        """
        初始化候選字引擎
        
        Args:
            phrase_db: 系統詞庫
            user_db: 用戶詞庫
        """
        self.parser = ZhuyinParser()
        self.phrase_db = phrase_db or PhraseDatabase()
        self.user_db = user_db or UserPhraseDatabase()
        
        # 快取最近的查詢
        self._cache = {}
        self._cache_size = 100
    
    def get_candidates(self, zhuyin: str, context: str = "", 
                       limit: int = 50) -> List[Candidate]:
        """
        取得候選詞列表
        
        Args:
            zhuyin: 輸入的注音
            context: 上下文（前一個字）
            limit: 最大候選數
            
        Returns:
            排序後的候選詞列表
        """
        if not zhuyin:
            return []
        
        # 檢查快取
        cache_key = f"{zhuyin}:{context}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        candidates = []
        seen = set()  # 避免重複
        
        # 1. 用戶偏好（最高優先）
        user_prefs = self.user_db.get_user_preference(zhuyin, limit=10)
        for phrase, use_count in user_prefs:
            if phrase not in seen:
                candidates.append(Candidate(
                    phrase=phrase,
                    zhuyin=zhuyin,
                    frequency=10000 + use_count * 100,  # 給予高權重
                    source='learned',
                    is_exact=True
                ))
                seen.add(phrase)
        
        # 2. 完全匹配
        exact_matches = self.phrase_db.search(zhuyin, limit=limit)
        for phrase, zy, freq in exact_matches:
            if phrase not in seen:
                candidates.append(Candidate(
                    phrase=phrase,
                    zhuyin=zy,
                    frequency=freq,
                    source='system',
                    is_exact=True
                ))
                seen.add(phrase)
        
        # 3. 前綴匹配（部分輸入時）
        if len(candidates) < limit:
            prefix_matches = self.phrase_db.search_prefix(zhuyin, limit=limit)
            for phrase, zy, freq in prefix_matches:
                if phrase not in seen:
                    candidates.append(Candidate(
                        phrase=phrase,
                        zhuyin=zy,
                        frequency=freq // 2,  # 降低權重
                        source='system',
                        is_exact=False
                    ))
                    seen.add(phrase)
        
        # 4. 聯想詞（基於上下文）
        if context and len(candidates) < limit:
            associated = self.phrase_db.get_associated_phrases(context[-1], limit=10)
            for phrase, zy, freq in associated:
                if phrase not in seen and phrase.startswith(context[-1]):
                    candidates.append(Candidate(
                        phrase=phrase[1:],  # 去掉第一個字（已輸入）
                        zhuyin=zy,
                        frequency=freq // 3,
                        source='system',
                        is_exact=False
                    ))
                    seen.add(phrase)
        
        # 排序
        candidates = self._sort_candidates(candidates)
        candidates = candidates[:limit]
        
        # 更新快取
        self._update_cache(cache_key, candidates)
        
        return candidates
    
    def _sort_candidates(self, candidates: List[Candidate]) -> List[Candidate]:
        """
        排序候選詞
        
        排序規則：
        1. 完全匹配優先
        2. 詞組長度適中優先（2-4字）
        3. 詞頻高優先
        """
        def sort_key(c: Candidate):
            # 完全匹配加分
            exact_score = 10000 if c.is_exact else 0
            
            # 長度分數（2-4字最佳）
            length = len(c.phrase)
            if 2 <= length <= 4:
                length_score = 5000
            elif length == 1:
                length_score = 3000
            else:
                length_score = 1000
            
            # 來源分數
            source_score = {
                'learned': 8000,
                'user': 6000,
                'system': 4000
            }.get(c.source, 0)
            
            return -(exact_score + length_score + source_score + c.frequency)
        
        return sorted(candidates, key=sort_key)
    
    def _update_cache(self, key: str, value: List[Candidate]):
        """更新快取"""
        if len(self._cache) >= self._cache_size:
            # 移除最舊的項目
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = value
    
    def commit_selection(self, candidate: Candidate):
        """
        記錄用戶選擇，用於學習
        
        Args:
            candidate: 被選中的候選詞
        """
        self.user_db.record_selection(candidate.zhuyin, candidate.phrase)
        
        # 清除相關快取
        keys_to_remove = [k for k in self._cache if candidate.zhuyin in k]
        for k in keys_to_remove:
            del self._cache[k]
    
    def get_single_char_candidates(self, zhuyin: str) -> List[Candidate]:
        """取得單字候選"""
        results = self.phrase_db.get_single_char(zhuyin, limit=30)
        
        candidates = []
        for char, freq in results:
            candidates.append(Candidate(
                phrase=char,
                zhuyin=zhuyin,
                frequency=freq,
                source='system',
                is_exact=True
            ))
        
        # 加入用戶偏好
        user_prefs = self.user_db.get_user_preference(zhuyin, limit=5)
        for phrase, use_count in user_prefs:
            if len(phrase) == 1:
                # 將用戶偏好移到最前面
                for i, c in enumerate(candidates):
                    if c.phrase == phrase:
                        candidates.pop(i)
                        break
                candidates.insert(0, Candidate(
                    phrase=phrase,
                    zhuyin=zhuyin,
                    frequency=10000 + use_count * 100,
                    source='learned',
                    is_exact=True
                ))
        
        return candidates
    
    def get_phrase_candidates(self, syllables: List[str]) -> List[Candidate]:
        """
        根據多個音節取得詞組候選
        
        Args:
            syllables: 音節列表
            
        Returns:
            候選詞列表
        """
        if not syllables:
            return []
        
        # 組合注音（以空格分隔）
        zhuyin = ' '.join(syllables)
        
        return self.get_candidates(zhuyin)
    
    def clear_cache(self):
        """清除快取"""
        self._cache.clear()
    
    def add_user_phrase(self, zhuyin: str, phrase: str):
        """新增用戶自訂詞組"""
        self.user_db.add_custom_phrase(zhuyin, phrase)
        self.clear_cache()


class SmartCandidateEngine(CandidateEngine):
    """智能候選字引擎 - 支援更多進階功能"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._recent_output = []  # 最近輸出的文字
        self._max_recent = 10
    
    def get_candidates_smart(self, zhuyin: str) -> List[Candidate]:
        """
        智能取得候選詞（考慮上下文）
        """
        context = ''.join(self._recent_output[-3:]) if self._recent_output else ""
        return self.get_candidates(zhuyin, context)
    
    def commit_and_record(self, candidate: Candidate) -> str:
        """
        提交選擇並記錄
        
        Returns:
            輸出的文字
        """
        self.commit_selection(candidate)
        
        # 記錄到最近輸出
        self._recent_output.append(candidate.phrase)
        if len(self._recent_output) > self._max_recent:
            self._recent_output.pop(0)
        
        return candidate.phrase
    
    def get_continuation_candidates(self) -> List[Candidate]:
        """取得續打候選詞（基於最近輸出）"""
        if not self._recent_output:
            return []
        
        last_char = self._recent_output[-1][-1] if self._recent_output[-1] else ""
        if not last_char:
            return []
        
        associated = self.phrase_db.get_associated_phrases(last_char, limit=10)
        
        candidates = []
        for phrase, zy, freq in associated:
            # 只要後續部分
            continuation = phrase[1:] if phrase.startswith(last_char) else phrase
            if continuation:
                candidates.append(Candidate(
                    phrase=continuation,
                    zhuyin=zy,
                    frequency=freq,
                    source='system',
                    is_exact=False
                ))
        
        return candidates
    
    def clear_context(self):
        """清除上下文"""
        self._recent_output.clear()
