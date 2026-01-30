# -*- coding: utf-8 -*-
"""
詞庫資料庫 - 管理注音詞庫的存取
"""

import os
import sqlite3
from typing import List, Optional, Tuple
from contextlib import contextmanager
import xbmcaddon
import xbmcvfs


class PhraseDatabase:
    """詞庫資料庫管理"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化詞庫
        
        Args:
            db_path: 資料庫路徑，None 則使用預設路徑
        """
        if db_path is None:
            addon = xbmcaddon.Addon()
            addon_path = xbmcvfs.translatePath(addon.getAddonInfo('path'))
            db_path = os.path.join(addon_path, 'resources', 'data', 'phrases.db')
        
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """確保資料庫存在且結構正確"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 主詞庫表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS phrases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zhuyin TEXT NOT NULL,
                    phrase TEXT NOT NULL,
                    frequency INTEGER DEFAULT 100,
                    length INTEGER,
                    UNIQUE(zhuyin, phrase)
                )
            ''')
            
            # 索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_zhuyin ON phrases(zhuyin)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_zhuyin_prefix ON phrases(zhuyin COLLATE NOCASE)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_freq ON phrases(frequency DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_length ON phrases(length)')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """取得資料庫連線"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def search(self, zhuyin: str, limit: int = 50) -> List[Tuple[str, str, int]]:
        """
        搜尋符合的詞組
        
        Args:
            zhuyin: 注音（可含聲調）
            limit: 最大結果數
            
        Returns:
            [(phrase, zhuyin, frequency), ...]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 完全匹配優先
            cursor.execute('''
                SELECT phrase, zhuyin, frequency 
                FROM phrases 
                WHERE zhuyin = ?
                ORDER BY frequency DESC, length ASC
                LIMIT ?
            ''', (zhuyin, limit))
            
            results = [(row['phrase'], row['zhuyin'], row['frequency']) 
                      for row in cursor.fetchall()]
            
            return results
    
    def search_prefix(self, zhuyin_prefix: str, limit: int = 50) -> List[Tuple[str, str, int]]:
        """
        前綴搜尋
        
        Args:
            zhuyin_prefix: 注音前綴
            limit: 最大結果數
            
        Returns:
            [(phrase, zhuyin, frequency), ...]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT phrase, zhuyin, frequency 
                FROM phrases 
                WHERE zhuyin LIKE ?
                ORDER BY length ASC, frequency DESC
                LIMIT ?
            ''', (zhuyin_prefix + '%', limit))
            
            results = [(row['phrase'], row['zhuyin'], row['frequency']) 
                      for row in cursor.fetchall()]
            
            return results
    
    def search_without_tone(self, zhuyin_no_tone: str, limit: int = 50) -> List[Tuple[str, str, int]]:
        """
        不含聲調的模糊搜尋
        
        Args:
            zhuyin_no_tone: 不含聲調的注音
            limit: 最大結果數
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 使用 LIKE 匹配（聲調可為任意字符）
            pattern = self._create_toneless_pattern(zhuyin_no_tone)
            
            cursor.execute('''
                SELECT phrase, zhuyin, frequency 
                FROM phrases 
                WHERE zhuyin LIKE ?
                ORDER BY frequency DESC, length ASC
                LIMIT ?
            ''', (pattern, limit))
            
            results = [(row['phrase'], row['zhuyin'], row['frequency']) 
                      for row in cursor.fetchall()]
            
            return results
    
    def _create_toneless_pattern(self, zhuyin: str) -> str:
        """建立忽略聲調的搜尋模式"""
        # 在每個音節後加入通配符以匹配聲調
        # 簡化處理：假設輸入已經是單音節
        return zhuyin + '%'
    
    def get_single_char(self, zhuyin: str, limit: int = 20) -> List[Tuple[str, int]]:
        """
        取得單字候選
        
        Args:
            zhuyin: 完整注音（含聲調）
            limit: 最大結果數
            
        Returns:
            [(char, frequency), ...]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT phrase, frequency 
                FROM phrases 
                WHERE zhuyin = ? AND length = 1
                ORDER BY frequency DESC
                LIMIT ?
            ''', (zhuyin, limit))
            
            return [(row['phrase'], row['frequency']) for row in cursor.fetchall()]
    
    def add_phrase(self, zhuyin: str, phrase: str, frequency: int = 100):
        """新增詞組"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO phrases (zhuyin, phrase, frequency, length)
                VALUES (?, ?, ?, ?)
            ''', (zhuyin, phrase, frequency, len(phrase)))
            
            conn.commit()
    
    def update_frequency(self, zhuyin: str, phrase: str, increment: int = 1):
        """更新詞頻"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE phrases 
                SET frequency = frequency + ?
                WHERE zhuyin = ? AND phrase = ?
            ''', (increment, zhuyin, phrase))
            
            conn.commit()
    
    def get_associated_phrases(self, last_char: str, limit: int = 10) -> List[Tuple[str, str, int]]:
        """
        取得聯想詞
        
        Args:
            last_char: 上一個輸入的字
            limit: 最大結果數
            
        Returns:
            [(phrase, zhuyin, frequency), ...]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 搜尋以該字開頭的詞組
            cursor.execute('''
                SELECT phrase, zhuyin, frequency 
                FROM phrases 
                WHERE phrase LIKE ? AND length > 1
                ORDER BY frequency DESC
                LIMIT ?
            ''', (last_char + '%', limit))
            
            return [(row['phrase'], row['zhuyin'], row['frequency']) 
                   for row in cursor.fetchall()]
    
    def import_from_text(self, file_path: str):
        """
        從文字檔匯入詞庫
        
        格式：每行 "詞組\t注音\t詞頻"
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        phrase = parts[0]
                        zhuyin = parts[1]
                        frequency = int(parts[2]) if len(parts) > 2 else 100
                        
                        cursor.execute('''
                            INSERT OR IGNORE INTO phrases (zhuyin, phrase, frequency, length)
                            VALUES (?, ?, ?, ?)
                        ''', (zhuyin, phrase, frequency, len(phrase)))
                
                conn.commit()
    
    def get_stats(self) -> dict:
        """取得詞庫統計"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as total FROM phrases')
            total = cursor.fetchone()['total']
            
            cursor.execute('SELECT COUNT(*) as chars FROM phrases WHERE length = 1')
            chars = cursor.fetchone()['chars']
            
            cursor.execute('SELECT COUNT(*) as words FROM phrases WHERE length > 1')
            words = cursor.fetchone()['words']
            
            return {
                'total': total,
                'characters': chars,
                'words': words
            }


class UserPhraseDatabase(PhraseDatabase):
    """用戶詞庫 - 記錄用戶選字習慣"""
    
    def __init__(self):
        addon = xbmcaddon.Addon()
        profile_path = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
        
        # 確保目錄存在
        if not os.path.exists(profile_path):
            os.makedirs(profile_path)
        
        db_path = os.path.join(profile_path, 'user_phrases.db')
        super().__init__(db_path)
        
        self._ensure_user_tables()
    
    def _ensure_user_tables(self):
        """建立用戶詞庫專用表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 用戶選字歷史
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zhuyin TEXT NOT NULL,
                    phrase TEXT NOT NULL,
                    use_count INTEGER DEFAULT 1,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(zhuyin, phrase)
                )
            ''')
            
            # 用戶自訂詞組
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_custom (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zhuyin TEXT NOT NULL,
                    phrase TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(zhuyin, phrase)
                )
            ''')
            
            conn.commit()
    
    def record_selection(self, zhuyin: str, phrase: str):
        """記錄用戶選擇"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_history (zhuyin, phrase, use_count, last_used)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(zhuyin, phrase) DO UPDATE SET
                    use_count = use_count + 1,
                    last_used = CURRENT_TIMESTAMP
            ''', (zhuyin, phrase))
            
            conn.commit()
    
    def get_user_preference(self, zhuyin: str, limit: int = 5) -> List[Tuple[str, int]]:
        """取得用戶偏好的候選詞"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT phrase, use_count 
                FROM user_history 
                WHERE zhuyin = ?
                ORDER BY use_count DESC, last_used DESC
                LIMIT ?
            ''', (zhuyin, limit))
            
            return [(row['phrase'], row['use_count']) for row in cursor.fetchall()]
    
    def add_custom_phrase(self, zhuyin: str, phrase: str):
        """新增自訂詞組"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO user_custom (zhuyin, phrase)
                VALUES (?, ?)
            ''', (zhuyin, phrase))
            
            # 同時加入主詞庫
            cursor.execute('''
                INSERT OR IGNORE INTO phrases (zhuyin, phrase, frequency, length)
                VALUES (?, ?, 1000, ?)
            ''', (zhuyin, phrase, len(phrase)))
            
            conn.commit()
    
    def clear_history(self):
        """清除選字歷史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user_history')
            conn.commit()
