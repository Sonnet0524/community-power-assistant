#!/bin/bash
#
# KIMI图片识别快速测试脚本
# 用法: ./test-kimi-image.sh <图片路径>
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  KIMI图片识别能力快速测试"
echo "========================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到python3${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python3 已安装${NC}"

# 检查环境变量
if [ -z "$KIMI_API_KEY" ]; then
    echo -e "${YELLOW}警告: 未设置KIMI_API_KEY环境变量${NC}"
    echo "正在尝试从.env文件读取..."
    
    if [ -f "field-info-agent/.env" ]; then
        export $(grep -v '^#' field-info-agent/.env | xargs)
        echo -e "${GREEN}✓ 已从.env文件加载配置${NC}"
    else
        echo -e "${RED}错误: 未找到.env文件${NC}"
        echo "请设置环境变量: export KIMI_API_KEY=your_key_here"
        exit 1
    fi
fi

# 显示配置（隐藏部分API Key）
echo ""
echo "当前配置:"
echo "  API Key: ${KIMI_API_KEY:0:20}..."
echo "  Base URL: ${KIMI_BASE_URL:-https://api.kimi.com/coding/}"
echo ""

# 检查图片参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <图片路径>"
    echo ""
    echo "示例:"
    echo "  $0 /path/to/nameplate.jpg"
    echo "  $0 ./test-images/transformer-01.jpg"
    echo ""
    echo "请提供一张变压器铭牌或配电房的照片进行测试"
    exit 1
fi

IMAGE_PATH=$1

# 检查图片文件是否存在
if [ ! -f "$IMAGE_PATH" ]; then
    echo -e "${RED}错误: 图片文件不存在: $IMAGE_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 图片文件存在: $IMAGE_PATH${NC}"

# 获取文件大小
FILE_SIZE=$(du -h "$IMAGE_PATH" | cut -f1)
echo "  文件大小: $FILE_SIZE"

# 创建临时Python脚本
cat > /tmp/test_kimi_quick.py << 'PYTHON_SCRIPT'
import asyncio
import sys
import base64
import os
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'community-power-assistant'))

try:
    import aiohttp
except ImportError:
    print("❌ 错误: 缺少aiohttp依赖")
    print("请安装: pip3 install aiohttp")
    sys.exit(1)

async def test_with_base64(image_path: str):
    """使用base64编码测试图片"""
    
    api_key = os.getenv('KIMI_API_KEY')
    base_url = os.getenv('KIMI_BASE_URL', 'https://api.kimi.com/coding/')
    
    # 读取图片并转为base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"📤 正在发送图片到KIMI API...")
    print(f"   图片大小: {len(image_data)} bytes (base64)")
    
    # 构建请求
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': os.getenv('KIMI_MODEL', 'kimi-for-coding'),
        'messages': [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': '''分析这张电力设施照片。如果是变压器铭牌，提取以下信息：
- 型号
- 容量(kVA)
- 电压等级(kV)
- 制造商
- 生产日期

如果是配电房或设备照片，识别：
- 设备类型
- 运行状态
- 安全隐患
- 改进建议

以JSON格式返回结果。'''
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/jpeg;base64,{image_data}'
                        }
                    }
                ]
            }
        ],
        'temperature': 0.7,
        'max_tokens': 2000
    }
    
    import time
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{base_url}chat/completions',
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ API错误: {response.status}")
                    print(f"错误详情: {error_text[:500]}")
                    return False
                
                data = await response.json()
                duration = time.time() - start_time
                
                content = data['choices'][0]['message']['content']
                
                print(f"\n✅ 分析成功! (耗时: {duration:.2f}秒)")
                print("\n" + "="*60)
                print("识别结果:")
                print("="*60)
                print(content)
                print("="*60)
                
                # 检查是否包含JSON
                if '```json' in content or '{' in content:
                    print("\n✓ 返回结果包含结构化数据")
                
                return True
                
    except asyncio.TimeoutError:
        print("❌ 错误: 请求超时(60秒)")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 test_kimi_quick.py <图片路径>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    success = asyncio.run(test_with_base64(image_path))
    sys.exit(0 if success else 1)
PYTHON_SCRIPT

echo ""
echo "🚀 开始测试..."
echo ""

# 运行测试
python3 /tmp/test_kimi_quick.py "$IMAGE_PATH"

TEST_RESULT=$?

echo ""
echo "========================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ 测试通过${NC}"
    echo ""
    echo "下一步建议:"
    echo "1. 如果识别准确率满意 → 准备集成测试"
    echo "2. 如果有问题 → 调整Prompt或检查图片质量"
else
    echo -e "${RED}❌ 测试失败${NC}"
    echo ""
    echo "排查建议:"
    echo "1. 检查API Key是否正确"
    echo "2. 检查网络连接"
    echo "3. 检查图片文件是否损坏"
fi
echo "========================================"

exit $TEST_RESULT
