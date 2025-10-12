"""
截图对比工具
"""
from PIL import Image, ImageChops
import math


class ScreenshotCompare:
    """截图对比工具类"""
    
    @staticmethod
    def compare_images(image1_path, image2_path):
        """
        对比两张图片的相似度
        
        Args:
            image1_path: 图片1路径
            image2_path: 图片2路径
        
        Returns:
            float: 相似度分数 (0-100)
        """
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)
        
        # 调整到相同尺寸
        if img1.size != img2.size:
            img2 = img2.resize(img1.size)
        
        # 计算差异
        diff = ImageChops.difference(img1, img2)
        
        # 计算均方根误差
        h = diff.histogram()
        sq = (value * (idx ** 2) for idx, value in enumerate(h))
        sum_of_squares = sum(sq)
        rms = math.sqrt(sum_of_squares / float(img1.size[0] * img1.size[1]))
        
        # 转换为相似度分数 (0-100)
        max_rms = 255 * math.sqrt(3)  # RGB最大差异
        similarity = 100 * (1 - (rms / max_rms))
        
        return similarity
    
    @staticmethod
    def images_are_similar(image1_path, image2_path, threshold=90.0):
        """
        判断两张图片是否相似
        
        Args:
            image1_path: 图片1路径
            image2_path: 图片2路径
            threshold: 相似度阈值（默认90%）
        
        Returns:
            bool: 是否相似
        """
        similarity = ScreenshotCompare.compare_images(image1_path, image2_path)
        return similarity >= threshold
    
    @staticmethod
    def crop_region(image_path, left, top, right, bottom, output_path):
        """
        裁剪图片区域
        
        Args:
            image_path: 原图路径
            left, top, right, bottom: 裁剪坐标
            output_path: 输出路径
        """
        img = Image.open(image_path)
        cropped = img.crop((left, top, right, bottom))
        cropped.save(output_path)
        
        return output_path

