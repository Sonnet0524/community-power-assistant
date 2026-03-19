"""
Field Info Agent - 照片分析服务

基于 KIMI 多模态能力，提供照片智能分析服务：
- 配电房安全检查
- 变压器铭牌识别
- 规范合规检查
- 批量照片分析
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from src.tools.kimi_tool import KIMITool


@dataclass
class SafetyRisk:
    """安全风险"""
    type: str
    description: str
    severity: str  # high/medium/low
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class NameplateInfo:
    """铭牌信息"""
    model: Optional[str] = None
    capacity: Optional[str] = None  # kVA
    voltage: Optional[str] = None   # kV
    manufacturer: Optional[str] = None
    manufacture_date: Optional[str] = None
    raw_text: Optional[str] = None


@dataclass
class ComplianceReport:
    """合规报告"""
    compliant: bool
    score: int  # 0-100
    violations: List[str]
    recommendations: List[str]


@dataclass
class PhotoAnalysisResult:
    """照片分析结果"""
    photo_url: str
    analysis_type: str
    success: bool
    data: Dict[str, Any]
    timestamp: datetime
    error: Optional[str] = None


class PhotoAnalysisService:
    """照片智能分析服务"""
    
    def __init__(self, kimi_tool: Optional[KIMITool] = None):
        self.kimi = kimi_tool or KIMITool()
    
    async def analyze_power_room(
        self,
        photo_urls: List[str]
    ) -> Dict[str, Any]:
        """
        配电房照片分析
        
        Args:
            photo_urls: 照片URL列表
            
        Returns:
            分析结果汇总
        """
        results = []
        all_risks = []
        
        for url in photo_urls:
            try:
                result = await self.kimi.analyze_image(
                    url,
                    analysis_type="safety"
                )
                
                results.append(PhotoAnalysisResult(
                    photo_url=url,
                    analysis_type="safety",
                    success=True,
                    data=result,
                    timestamp=datetime.now()
                ))
                
                # 汇总风险
                if "risks" in result:
                    for risk in result["risks"]:
                        all_risks.append(SafetyRisk(
                            type=risk.get("type", "unknown"),
                            description=risk.get("description", ""),
                            severity=risk.get("severity", "medium"),
                            suggestion=risk.get("suggestion")
                        ))
                        
            except Exception as e:
                results.append(PhotoAnalysisResult(
                    photo_url=url,
                    analysis_type="safety",
                    success=False,
                    data={},
                    timestamp=datetime.now(),
                    error=str(e)
                ))
        
        # 生成汇总报告
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for risk in all_risks:
            severity_counts[risk.severity] = severity_counts.get(risk.severity, 0) + 1
        
        return {
            "total_photos": len(photo_urls),
            "successful_analysis": sum(1 for r in results if r.success),
            "failed_analysis": sum(1 for r in results if not r.success),
            "risks_summary": severity_counts,
            "risks": [
                {
                    "type": r.type,
                    "description": r.description,
                    "severity": r.severity,
                    "suggestion": r.suggestion
                }
                for r in all_risks
            ],
            "overall_status": "danger" if severity_counts["high"] > 0 else 
                             "warning" if severity_counts["medium"] > 0 else "safe",
            "details": results
        }
    
    async def analyze_nameplate(
        self,
        photo_url: str
    ) -> NameplateInfo:
        """
        变压器铭牌识别
        
        Args:
            photo_url: 铭牌照片URL
            
        Returns:
            铭牌信息
        """
        try:
            result = await self.kimi.analyze_image(
                photo_url,
                analysis_type="nameplate"
            )
            
            return NameplateInfo(
                model=result.get("model"),
                capacity=result.get("capacity"),
                voltage=result.get("voltage"),
                manufacturer=result.get("manufacturer"),
                manufacture_date=result.get("date"),
                raw_text=result.get("raw_response", "")
            )
        except Exception as e:
            return NameplateInfo(
                raw_text=f"识别失败: {e}"
            )
    
    async def check_compliance(
        self,
        photo_urls: List[str]
    ) -> ComplianceReport:
        """
        规范合规检查
        
        Args:
            photo_urls: 照片URL列表
            
        Returns:
            合规报告
        """
        all_violations = []
        total_score = 0
        
        for url in photo_urls:
            try:
                result = await self.kimi.analyze_image(
                    url,
                    analysis_type="compliance"
                )
                
                if "violations" in result:
                    all_violations.extend(result["violations"])
                
                if "score" in result:
                    total_score += result["score"]
                    
            except Exception:
                pass
        
        # 计算平均分
        avg_score = total_score // len(photo_urls) if photo_urls else 0
        
        # 生成建议
        recommendations = []
        if avg_score < 60:
            recommendations.append("立即整改安全隐患")
        elif avg_score < 80:
            recommendations.append("尽快完善安全设施")
        
        if all_violations:
            recommendations.append(f"重点关注: {', '.join(set(all_violations))}")
        
        return ComplianceReport(
            compliant=avg_score >= 80 and not all_violations,
            score=avg_score,
            violations=list(set(all_violations)),
            recommendations=recommendations
        )
    
    async def generate_analysis_report(
        self,
        task_id: str,
        photo_urls: List[str],
        report_type: str = "comprehensive"
    ) -> str:
        """
        生成分析报告
        
        Args:
            task_id: 任务ID
            photo_urls: 照片URL列表
            report_type: 报告类型 (comprehensive/safety/compliance)
            
        Returns:
            报告内容 (Markdown格式)
        """
        # 收集所有分析结果
        safety_result = await self.analyze_power_room(photo_urls)
        compliance_result = await self.check_compliance(photo_urls)
        
        # 构建报告数据
        data = {
            "task_id": task_id,
            "photo_count": len(photo_urls),
            "safety_summary": safety_result,
            "compliance": {
                "score": compliance_result.score,
                "compliant": compliance_result.compliant,
                "violations": compliance_result.violations
            }
        }
        
        # 使用KIMI生成报告
        return await self.kimi.generate_document(
            template_type="briefing",
            data=data,
            photos=photo_urls[:3]  # 最多3张示例图
        )


# 便捷函数
async def quick_analyze_photo(
    photo_url: str,
    analysis_type: str = "general"
) -> Dict[str, Any]:
    """快速分析单张照片"""
    service = PhotoAnalysisService()
    return await service.kimi.analyze_image(photo_url, analysis_type)