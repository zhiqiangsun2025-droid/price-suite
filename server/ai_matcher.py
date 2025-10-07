#!/usr/bin/env python3
"""
AI智能商品匹配引擎
基于标题相似度 + 图片相似度 双重判断
"""

import requests
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import imagehash
from typing import List, Dict, Tuple

class ProductMatcher:
    """商品智能匹配"""
    
    def __init__(self):
        self.text_threshold = 0.6  # 文本相似度阈值
        self.image_threshold = 10   # 图片哈希距离阈值
    
    def match_products(self, source_product: Dict, candidate_products: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        匹配商品
        
        Args:
            source_product: 源商品（抖音）{'title': '', 'image_url': '', 'price': 0}
            candidate_products: 候选商品列表（拼多多）
        
        Returns:
            匹配结果列表 [(商品, 综合相似度得分), ...]
        """
        results = []
        
        for candidate in candidate_products:
            # 1. 文本相似度
            text_sim = self._calculate_text_similarity(
                source_product['title'],
                candidate['title']
            )
            
            # 2. 图片相似度
            image_sim = self._calculate_image_similarity(
                source_product.get('image_url'),
                candidate.get('image_url')
            )
            
            # 3. 综合得分（文本70% + 图片30%）
            total_score = text_sim * 0.7 + image_sim * 0.3
            
            # 过滤：文本相似度必须达标
            if text_sim >= self.text_threshold:
                results.append((candidate, total_score))
        
        # 按得分排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（基于TF-IDF + 余弦相似度）"""
        try:
            # 分词
            words1 = ' '.join(jieba.cut(text1))
            words2 = ' '.join(jieba.cut(text2))
            
            # TF-IDF向量化
            vectorizer = TfidfVectorizer()
            tfidf = vectorizer.fit_transform([words1, words2])
            
            # 余弦相似度
            similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            print(f"文本相似度计算失败: {e}")
            return 0.0
    
    def _calculate_image_similarity(self, url1: str, url2: str) -> float:
        """计算图片相似度（基于感知哈希）"""
        try:
            if not url1 or not url2:
                return 0.0
            
            # 下载图片
            img1 = self._download_image(url1)
            img2 = self._download_image(url2)
            
            if img1 is None or img2 is None:
                return 0.0
            
            # 计算感知哈希
            hash1 = imagehash.phash(img1)
            hash2 = imagehash.phash(img2)
            
            # 哈希距离（越小越相似）
            distance = hash1 - hash2
            
            # 转换为相似度（0-1）
            similarity = max(0, 1 - distance / 64)
            return similarity
        except Exception as e:
            print(f"图片相似度计算失败: {e}")
            return 0.0
    
    def _download_image(self, url: str) -> Image.Image:
        """下载图片"""
        try:
            response = requests.get(url, timeout=10)
            img = Image.open(BytesIO(response.content))
            return img
        except Exception as e:
            print(f"图片下载失败 {url}: {e}")
            return None
    
    def advanced_match_with_cv(self, source_product: Dict, candidate_products: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        高级匹配（使用OpenCV特征匹配）
        适用于需要更精确匹配的场景
        """
        results = []
        
        # 下载源图片
        source_img = self._download_image(source_product.get('image_url'))
        if source_img is None:
            return []
        
        source_cv = cv2.cvtColor(np.array(source_img), cv2.COLOR_RGB2BGR)
        
        # SIFT特征提取
        sift = cv2.SIFT_create()
        kp1, des1 = sift.detectAndCompute(source_cv, None)
        
        for candidate in candidate_products:
            candidate_img = self._download_image(candidate.get('image_url'))
            if candidate_img is None:
                continue
            
            candidate_cv = cv2.cvtColor(np.array(candidate_img), cv2.COLOR_RGB2BGR)
            kp2, des2 = sift.detectAndCompute(candidate_cv, None)
            
            if des1 is None or des2 is None:
                continue
            
            # 特征匹配
            bf = cv2.BFMatcher()
            matches = bf.knnMatch(des1, des2, k=2)
            
            # 应用ratio test
            good_matches = []
            for m, n in matches:
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)
            
            # 计算匹配度
            match_score = len(good_matches) / max(len(kp1), len(kp2))
            
            # 文本相似度
            text_sim = self._calculate_text_similarity(
                source_product['title'],
                candidate['title']
            )
            
            # 综合得分
            total_score = text_sim * 0.6 + match_score * 0.4
            results.append((candidate, total_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results


# ============ 百度AI / 阿里云 API 方案（推荐） ============

class BaiduAIMatcher:
    """百度AI商品匹配（更准确，但需要API密钥）"""
    
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.access_token = self._get_access_token()
    
    def _get_access_token(self) -> str:
        """获取百度AI access_token"""
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.api_key}&client_secret={self.secret_key}"
        response = requests.get(url)
        return response.json().get("access_token")
    
    def compare_images(self, image_url1: str, image_url2: str) -> float:
        """
        使用百度图像相似度API
        https://ai.baidu.com/ai-doc/IMAGESEARCH/
        """
        url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/similar_search"
        
        params = {
            "access_token": self.access_token
        }
        
        # 这里需要将图片转base64
        # ...具体实现省略
        
        response = requests.post(url, params=params, data={
            'image1': image_url1,
            'image2': image_url2
        })
        
        result = response.json()
        return result.get('score', 0) / 100  # 转换为0-1


# ============ 使用示例 ============

if __name__ == "__main__":
    matcher = ProductMatcher()
    
    # 抖音商品
    douyin_product = {
        'title': '夏季新款连衣裙女2024流行宽松显瘦气质长裙',
        'image_url': 'https://xxx.com/douyin_product.jpg',
        'price': 128.00
    }
    
    # 拼多多候选商品
    pdd_products = [
        {
            'title': '连衣裙女2024新款夏季显瘦气质长裙',
            'image_url': 'https://xxx.com/pdd1.jpg',
            'price': 59.00
        },
        {
            'title': '夏装女装新款连衣裙长裙宽松显瘦',
            'image_url': 'https://xxx.com/pdd2.jpg',
            'price': 79.00
        }
    ]
    
    # 匹配
    results = matcher.match_products(douyin_product, pdd_products)
    
    for product, score in results:
        print(f"商品: {product['title']}")
        print(f"价格: {product['price']}")
        print(f"匹配度: {score:.2%}")
        print("-" * 50)

