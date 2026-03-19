"""
企业微信命令解析模块
解析用户输入的命令和自然语言
"""

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any


class CommandType(Enum):
    """命令类型枚举"""
    START = auto()           # /start {小区名} - 启动驻点工作
    COLLECT = auto()         # /collect {类型} - 开始采集
    GENERATE = auto()        # /generate {类型} - 生成文档
    EMERGENCY = auto()       # /emergency {类型} {地点} - 应急处置
    QUERY = auto()           # /query {内容} - 查询信息
    HELP = auto()            # /help - 查看帮助
    STATUS = auto()          # /status - 查看状态
    CANCEL = auto()          # /cancel - 取消任务
    UNKNOWN = auto()         # 未知命令


@dataclass
class ParsedCommand:
    """解析后的命令"""
    command_type: CommandType
    name: str
    args: List[str]
    raw: str
    confidence: float = 1.0  # 置信度，用于自然语言识别
    metadata: Dict[str, Any] = field(default_factory=dict)


class CommandParser:
    """命令解析器"""
    
    # 命令定义
    COMMANDS = {
        CommandType.START: {
            'patterns': [r'^/start(?:\s+(.+))?$', r'^开始.*驻点', r'^去.*社区', r'^去.*小区'],
            'description': '启动驻点工作',
            'example': '/start 阳光小区',
            'arg_count': 1
        },
        CommandType.COLLECT: {
            'patterns': [r'^/collect(?:\s+(.+))?$', r'^开始采集', r'^采集.*信息'],
            'description': '开始信息采集',
            'example': '/collect power-room',
            'arg_count': 1
        },
        CommandType.GENERATE: {
            'patterns': [r'^/generate(?:\s+(.+))?$', r'^生成.*报告', r'^生成.*文档', r'^出.*简报'],
            'description': '生成工作文档',
            'example': '/generate briefing',
            'arg_count': 1
        },
        CommandType.EMERGENCY: {
            'patterns': [r'^/emergency(?:\s+(\S+)(?:\s+(.+))?)?$', r'^应急', r'^紧急', r'^抢修'],
            'description': '启动应急处置',
            'example': '/emergency outage 阳光小区',
            'arg_count': 2
        },
        CommandType.QUERY: {
            'patterns': [r'^/query(?:\s+(.+))?$', r'^查询', r'^查看'],
            'description': '查询信息',
            'example': '/query 阳光小区配电房',
            'arg_count': 1
        },
        CommandType.HELP: {
            'patterns': [r'^/help$', r'^帮助', r'^怎么用'],
            'description': '查看帮助信息',
            'example': '/help',
            'arg_count': 0
        },
        CommandType.STATUS: {
            'patterns': [r'^/status$', r'^状态', r'^进度'],
            'description': '查看当前状态',
            'example': '/status',
            'arg_count': 0
        },
        CommandType.CANCEL: {
            'patterns': [r'^/cancel$', r'^取消', r'^停止'],
            'description': '取消当前任务',
            'example': '/cancel',
            'arg_count': 0
        }
    }
    
    def __init__(self):
        """初始化命令解析器"""
        self._compiled_patterns = {}
        for cmd_type, config in self.COMMANDS.items():
            self._compiled_patterns[cmd_type] = [
                re.compile(pattern, re.IGNORECASE | re.UNICODE)
                for pattern in config['patterns']
            ]
    
    def parse(self, input_text: str) -> ParsedCommand:
        """
        解析输入文本
        
        Args:
            input_text: 用户输入的文本
            
        Returns:
            ParsedCommand对象
        """
        if not input_text or not input_text.strip():
            return ParsedCommand(
                command_type=CommandType.UNKNOWN,
                name='unknown',
                args=[],
                raw='',
                confidence=0.0
            )
        
        text = input_text.strip()
        
        # 尝试匹配命令
        for cmd_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.match(text)
                if match:
                    args = [g for g in match.groups() if g is not None]
                    return ParsedCommand(
                        command_type=cmd_type,
                        name=cmd_type.name.lower(),
                        args=args,
                        raw=text,
                        confidence=1.0
                    )
        
        # 未匹配到命令，尝试自然语言识别
        return self._parse_natural_language(text)
    
    def _parse_natural_language(self, text: str) -> ParsedCommand:
        """
        自然语言意图识别
        
        Args:
            text: 用户输入
            
        Returns:
            ParsedCommand对象
        """
        # 简单的关键词匹配（实际项目中可以使用LLM进行更准确的识别）
        keywords = {
            CommandType.START: ['驻点', '去', '开始工作', '出发'],
            CommandType.COLLECT: ['采集', '拍照', '记录', '检查', '配电房', '走访'],
            CommandType.GENERATE: ['生成', '报告', '文档', '简报', '导出'],
            CommandType.EMERGENCY: ['停电', '故障', '抢修', '紧急', '危险'],
            CommandType.QUERY: ['查询', '查看', '搜索', '找一下'],
            CommandType.HELP: ['帮助', '怎么用', '不会用'],
            CommandType.STATUS: ['状态', '进度', '完成度'],
            CommandType.CANCEL: ['取消', '停止', '不做了']
        }
        
        best_match = CommandType.UNKNOWN
        max_score = 0.0
        
        for cmd_type, words in keywords.items():
            score = sum(1 for word in words if word in text)
            if score > max_score:
                max_score = score
                best_match = cmd_type
        
        # 计算置信度（简单规则：匹配到的关键词越多置信度越高）
        confidence = min(max_score * 0.3, 0.8) if max_score > 0 else 0.0
        
        # 提取可能的参数
        args = self._extract_args(text, best_match)
        
        return ParsedCommand(
            command_type=best_match if confidence > 0.3 else CommandType.UNKNOWN,
            name=best_match.name.lower() if best_match != CommandType.UNKNOWN else 'unknown',
            args=args,
            raw=text,
            confidence=confidence
        )
    
    def _extract_args(self, text: str, cmd_type: CommandType) -> List[str]:
        """
        从文本中提取参数
        
        Args:
            text: 用户输入
            cmd_type: 识别的命令类型
            
        Returns:
            参数列表
        """
        args = []
        
        if cmd_type == CommandType.START:
            # 提取小区/社区名称
            patterns = [
                r'去(\S+社区)',
                r'去(\S+小区)',
                r'去(\S+花园)',
                r'去(\S+苑)',
                r'开始(\S+社区)',
                r'开始(\S+小区)',
                r'驻点(\S+社区)',
                r'驻点(\S+小区)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    args.append(match.group(1))
                    break
        
        elif cmd_type == CommandType.EMERGENCY:
            # 提取故障类型和地点
            # 例如：阳光小区停电 -> args=['停电', '阳光小区']
            emergency_types = ['停电', '故障', '抢修', '跳闸', '起火']
            for etype in emergency_types:
                if etype in text:
                    args.append(etype)
                    break
            
            # 提取地点
            location_patterns = [r'(\S+社区)', r'(\S+小区)', r'(\S+花园)', r'(\S+苑)']
            for pattern in location_patterns:
                match = re.search(pattern, text)
                if match:
                    args.append(match.group(1))
                    break
        
        return args
    
    def get_help_text(self) -> str:
        """
        获取帮助文本
        
        Returns:
            帮助信息文本
        """
        lines = [
            "📋 可用命令列表：",
            ""
        ]
        
        for cmd_type, config in self.COMMANDS.items():
            lines.append(f"/{cmd_type.name.lower()} - {config['description']}")
            lines.append(f"  示例: {config['example']}")
            lines.append("")
        
        lines.extend([
            "💡 提示：",
            "• 可以直接输入自然语言，例如：'我要去阳光小区驻点'",
            "• 支持语音输入（语音会自动转为文字）",
            "• 发送图片可自动分析设备状态"
        ])
        
        return "\n".join(lines)
    
    def is_command(self, text: str) -> bool:
        """
        判断是否为命令
        
        Args:
            text: 用户输入
            
        Returns:
            是否为命令
        """
        parsed = self.parse(text)
        return parsed.command_type != CommandType.UNKNOWN and parsed.confidence >= 0.5


class IntentRecognizer:
    """意图识别器 - 基于LLM的高级意图识别"""
    
    # 意图类型定义
    INTENTS = {
        'start_station_work': '开始驻点工作',
        'collect_power_room': '配电房信息采集',
        'collect_customer': '客户走访',
        'collect_emergency': '应急通道采集',
        'complete_collection': '完成采集',
        'query_info': '查询信息',
        'general_chat': '一般对话'
    }
    
    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: LLM客户端（用于高级意图识别）
        """
        self.llm_client = llm_client
        self.command_parser = CommandParser()
    
    def recognize(self, text: str, session_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        识别用户意图
        
        Args:
            text: 用户输入
            session_context: 会话上下文
            
        Returns:
            识别结果，包含intent, confidence, entities等
        """
        # 首先尝试命令解析
        parsed = self.command_parser.parse(text)
        
        if parsed.confidence >= 0.9:
            # 高置信度命令匹配
            return {
                'intent': self._command_to_intent(parsed.command_type),
                'confidence': parsed.confidence,
                'entities': self._extract_entities(parsed),
                'command': parsed,
                'method': 'command_match'
            }
        
        # 如果有LLM客户端，使用LLM进行识别
        if self.llm_client:
            return self._recognize_with_llm(text, session_context)
        
        # 使用规则匹配
        return self._recognize_with_rules(text, session_context)
    
    def _command_to_intent(self, cmd_type: CommandType) -> str:
        """命令类型转意图"""
        mapping = {
            CommandType.START: 'start_station_work',
            CommandType.COLLECT: 'collect_power_room',
            CommandType.GENERATE: 'complete_collection',
            CommandType.EMERGENCY: 'collect_emergency',
            CommandType.QUERY: 'query_info',
            CommandType.HELP: 'general_chat',
            CommandType.STATUS: 'query_info',
            CommandType.CANCEL: 'general_chat'
        }
        return mapping.get(cmd_type, 'general_chat')
    
    def _extract_entities(self, parsed: ParsedCommand) -> Dict[str, Any]:
        """提取实体"""
        entities = {}
        
        if parsed.command_type == CommandType.START and parsed.args:
            entities['community_name'] = parsed.args[0]
        
        if parsed.command_type == CommandType.EMERGENCY:
            if len(parsed.args) >= 1:
                entities['emergency_type'] = parsed.args[0]
            if len(parsed.args) >= 2:
                entities['location'] = parsed.args[1]
        
        return entities
    
    def _recognize_with_llm(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用LLM进行意图识别"""
        # 实际实现需要调用LLM
        # 这里返回一个占位结果
        return {
            'intent': 'general_chat',
            'confidence': 0.5,
            'entities': {},
            'command': None,
            'method': 'llm'
        }
    
    def _recognize_with_rules(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用规则进行意图识别"""
        # 简单的关键词规则
        intent_keywords = {
            'start_station_work': ['驻点', '去.*社区', '去.*小区', '开始.*工作'],
            'collect_power_room': ['配电房', '变压器', '拍摄.*配电', '检查.*配电'],
            'collect_customer': ['走访', '客户', '用户', '居民'],
            'collect_emergency': ['应急', '通道', '位置', 'GPS'],
            'complete_collection': ['完成', '结束', '生成.*报告', '好了'],
            'query_info': ['查询', '查看', '搜索', '找']
        }
        
        best_intent = 'general_chat'
        max_score = 0
        
        for intent, patterns in intent_keywords.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    score = len(pattern)
                    if score > max_score:
                        max_score = score
                        best_intent = intent
        
        confidence = min(max_score / 10, 0.7)
        
        return {
            'intent': best_intent,
            'confidence': confidence,
            'entities': {},
            'command': None,
            'method': 'rule'
        }
