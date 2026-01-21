'''
开发者: BackendAgent
当前版本: v1.0_text_splitter
创建时间: 2026年01月08日 15:45
更新时间: 2026年01月08日 15:45
更新记录:
    [2026年01月08日 15:45:v1.0_text_splitter:创建文本分割器，支持按长度和语义分割]
'''

import re
from typing import List


class TextSplitter:
    """文本分割器"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        """
        初始化文本分割器

        参数:
        - chunk_size: 每个块的最大长度
        - chunk_overlap: 块之间的重叠长度
        - separators: 分隔符列表，按优先级排序
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "! ", "? ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """
        分割文本

        参数:
        - text: 要分割的文本

        返回:
        - List[str]: 文本块列表
        """
        chunks = []

        # 如果文本本身小于chunk_size，直接返回
        if len(text) <= self.chunk_size:
            return [text]

        # 尝试使用不同的分隔符
        for separator in self.separators:
            if separator == "":
                # 最后一个选择：按字符分割
                chunks = self._split_by_character(text)
                break

            if separator in text:
                chunks = self._split_by_separator(text, separator)
                if self._is_valid_chunks(chunks):
                    break

        # 应用重叠
        if self.chunk_overlap > 0:
            chunks = self._apply_overlap(chunks)

        return chunks

    def _split_by_separator(self, text: str, separator: str) -> List[str]:
        """按分隔符分割文本"""
        splits = text.split(separator)
        chunks = []
        current_chunk = ""

        for split in splits:
            # 添加分隔符（除了最后一个）
            split_with_sep = split + separator if split != splits[-1] else split

            # 如果当前块加上新内容不超过限制，就添加
            if len(current_chunk) + len(split_with_sep) <= self.chunk_size:
                current_chunk += split_with_sep
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # 如果单个split就超过chunk_size，需要进一步分割
                if len(split_with_sep) > self.chunk_size:
                    # 递归使用更小的分隔符
                    sub_chunks = self._split_recursively(split_with_sep)
                    chunks.extend(sub_chunks[:-1])  # 除了最后一个都添加
                    current_chunk = sub_chunks[-1]  # 最后一个作为新的开始
                else:
                    current_chunk = split_with_sep

        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_character(self, text: str) -> List[str]:
        """按字符分割文本"""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            chunks.append(chunk)
        return chunks

    def _split_recursively(self, text: str) -> List[str]:
        """递归分割（用于处理超大块）"""
        # 找到当前分隔符的索引
        current_separator_index = 0

        for i, separator in enumerate(self.separators):
            if separator in text and separator != "":
                current_separator_index = i
                break

        # 如果还有更小的分隔符，使用它
        if current_separator_index + 1 < len(self.separators):
            next_separators = self.separators[current_separator_index + 1:]
            temp_splitter = TextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=next_separators
            )
            return temp_splitter.split_text(text)
        else:
            # 没有更小的分隔符了，按字符分割
            return self._split_by_character(text)

    def _is_valid_chunks(self, chunks: List[str]) -> bool:
        """检查分割结果是否有效"""
        if not chunks:
            return False

        # 检查是否有块超过限制
        for chunk in chunks:
            if len(chunk) > self.chunk_size * 1.2:  # 允许20%的溢出
                return False

        return True

    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """应用重叠"""
        if len(chunks) <= 1:
            return chunks

        result = [chunks[0]]  # 第一块不需要重叠

        for i in range(1, len(chunks)):
            # 从前一块的末尾取重叠部分
            prev_chunk = result[-1]
            overlap_text = prev_chunk[-self.chunk_overlap:]

            # 添加到当前块的开头
            new_chunk = overlap_text + chunks[i]
            result.append(new_chunk)

        return result

    def split_text_with_metadata(self, text: str) -> List[dict]:
        """
        分割文本并返回包含元数据的信息

        参数:
        - text: 要分割的文本

        返回:
        - List[dict]: 包含文本块和元数据的列表
        """
        chunks = self.split_text(text)

        result = []
        start_idx = 0

        for chunk in chunks:
            # 找到当前块在原文中的位置
            chunk_start = text.find(chunk, start_idx)
            chunk_end = chunk_start + len(chunk)

            result.append({
                "text": chunk,
                "start_index": chunk_start,
                "end_index": chunk_end,
                "length": len(chunk)
            })

            start_idx = chunk_end

        return result


class SemanticTextSplitter(TextSplitter):
    """语义文本分割器（基于句子边界）"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_sentence_length: int = 20
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.min_sentence_length = min_sentence_length
        # 句子结束标点
        self.sentence_endings = r'[.!?]+\s+'

    def split_text(self, text: str) -> List[str]:
        """
        按句子边界分割文本
        """
        # 先按句子分割
        sentences = re.split(self.sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # 如果句子太短，跳过
            if len(sentence) < self.min_sentence_length:
                continue

            # 添加句子结束符
            sentence_with_ending = sentence + ". "

            # 检查是否超过限制
            if len(current_chunk) + len(sentence_with_ending) <= self.chunk_size:
                current_chunk += sentence_with_ending
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # 如果单个句子就超过限制，需要进一步处理
                if len(sentence_with_ending) > self.chunk_size:
                    # 使用父类的方法进行字符级分割
                    sub_chunks = super()._split_by_character(sentence)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1]
                else:
                    current_chunk = sentence_with_ending

        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk.strip())

        # 应用重叠
        if self.chunk_overlap > 0:
            chunks = self._apply_overlap(chunks)

        return chunks