"""
KIMI图片识别能力验证脚本

在完整集成测试前，先单独验证KIMI Tool的图片分析功能
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.kimi_tool import KIMITool, KIMIConfig


# 测试图片URL（需要准备的真实图片）
# 请替换为实际的MinIO URL或公开可访问的图片URL
TEST_IMAGES = {
    "nameplate": [
        # 变压器铭牌照片URL（需要替换）
        # "http://minio:9000/field-documents/test/nameplate_01.jpg",
        # "http://minio:9000/field-documents/test/nameplate_02.jpg",
    ],
    "power_room": [
        # 配电房照片URL（需要替换）
        # "http://minio:9000/field-documents/test/power_room_01.jpg",
    ],
    "safety": [
        # 安全隐患照片URL（需要替换）
        # "http://minio:9000/field-documents/test/safety_issue_01.jpg",
    ]
}


async def test_kimi_connection():
    """测试KIMI API连接"""
    print("=" * 60)
    print("测试1: KIMI API连接测试")
    print("=" * 60)
    
    try:
        kimi = KIMITool()
        await kimi.connect()
        
        # 简单对话测试
        response = await kimi.chat([
            {"role": "user", "content": "你好，请回复'连接成功'"}
        ])
        
        print(f"✅ API连接成功")
        print(f"响应: {response[:50]}...")
        await kimi.close()
        return True
        
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False


async def test_image_analysis(image_url: str, analysis_type: str, description: str):
    """测试单张图片分析"""
    print(f"\n{'=' * 60}")
    print(f"测试图片分析: {description}")
    print(f"类型: {analysis_type}")
    print(f"URL: {image_url}")
    print("=" * 60)
    
    try:
        kimi = KIMITool()
        
        start_time = asyncio.get_event_loop().time()
        
        result = await kimi.analyze_image(
            image_url=image_url,
            analysis_type=analysis_type
        )
        
        duration = asyncio.get_event_loop().time() - start_time
        
        print(f"✅ 分析成功 (耗时: {duration:.2f}秒)")
        print(f"\n识别结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 验证结果结构
        if analysis_type == "nameplate":
            required_fields = ["model", "capacity", "voltage"]
            missing = [f for f in required_fields if f not in result]
            if missing:
                print(f"⚠️ 缺少字段: {missing}")
            else:
                print(f"✅ 所有关键字段已识别")
        
        await kimi.close()
        return True, result
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_batch_analysis(image_urls: list, analysis_type: str):
    """测试批量图片分析"""
    print(f"\n{'=' * 60}")
    print(f"测试批量分析: {len(image_urls)}张图片")
    print("=" * 60)
    
    try:
        kimi = KIMITool()
        
        start_time = asyncio.get_event_loop().time()
        
        results = await kimi.analyze_images_batch(
            image_urls=image_urls,
            prompt="分析这张电力设施照片",
            batch_size=3
        )
        
        duration = asyncio.get_event_loop().time() - start_time
        
        print(f"✅ 批量分析完成 (总耗时: {duration:.2f}秒)")
        print(f"平均每张: {duration/len(image_urls):.2f}秒")
        
        success_count = sum(1 for r in results if r.get("success"))
        print(f"成功: {success_count}/{len(image_urls)}")
        
        await kimi.close()
        return True
        
    except Exception as e:
        print(f"❌ 批量分析失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          KIMI图片识别能力验证测试                            ║
║                                                              ║
║  在完整集成测试前，先单独验证KIMI的图片分析功能              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # 检查环境变量
    if not os.getenv("KIMI_API_KEY"):
        print("❌ 错误: 未设置KIMI_API_KEY环境变量")
        print("请先配置: export KIMI_API_KEY=your_key_here")
        return
    
    print(f"API Key: {os.getenv('KIMI_API_KEY')[:20]}...")
    print(f"Base URL: {os.getenv('KIMI_BASE_URL', 'https://api.kimi.com/coding/')}")
    print(f"Model: {os.getenv('KIMI_MODEL', 'kimi-for-coding')}")
    
    # 测试1: API连接
    connection_ok = await test_kimi_connection()
    if not connection_ok:
        print("\n❌ API连接测试失败，停止后续测试")
        return
    
    # 检查是否有测试图片
    has_test_images = any(TEST_IMAGES.values())
    
    if not has_test_images:
        print("\n" + "=" * 60)
        print("⚠️  未配置测试图片")
        print("=" * 60)
        print("""
请准备测试图片并更新TEST_IMAGES配置：

1. 准备以下测试图片：
   - 变压器铭牌照片（清晰、光线良好）
   - 配电房环境照片
   - 设备细节照片

2. 上传到MinIO或任何可访问的存储：
   mc cp nameplate_01.jpg local/field-documents/test/

3. 更新本脚本中的TEST_IMAGES配置

4. 重新运行测试
        """)
        return
    
    # 测试2: 铭牌识别
    if TEST_IMAGES["nameplate"]:
        for url in TEST_IMAGES["nameplate"][:2]:  # 测试前2张
            success, result = await test_image_analysis(
                url, 
                "nameplate", 
                "变压器铭牌识别"
            )
            
            if success and result:
                # 验证准确率
                has_model = bool(result.get("model"))
                has_capacity = bool(result.get("capacity"))
                print(f"\n识别准确率检查:")
                print(f"  - 型号: {'✅' if has_model else '❌'}")
                print(f"  - 容量: {'✅' if has_capacity else '❌'}")
    
    # 测试3: 配电房分析
    if TEST_IMAGES["power_room"]:
        for url in TEST_IMAGES["power_room"][:1]:
            await test_image_analysis(
                url,
                "safety",
                "配电房安全分析"
            )
    
    # 测试4: 批量分析
    all_images = []
    for category in TEST_IMAGES.values():
        all_images.extend(category[:2])  # 每个类别最多2张
    
    if len(all_images) >= 2:
        await test_batch_analysis(all_images[:5], "general")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("""
下一步建议：
1. 如果所有测试通过 → 准备集成测试
2. 如果有失败项 → 检查API配置或图片质量
3. 记录识别准确率 → 评估是否满足业务需求

注意：本测试仅验证KIMI识别能力，完整的端到端流程
（企业微信→MinIO→KIMI→PostgreSQL）需要在集成测试中验证。
    """)


if __name__ == "__main__":
    import json
    asyncio.run(main())
