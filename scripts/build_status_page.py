import csv
import datetime as dt
import html
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()


STATUS_META = {
    "⚪": {"label": "待投稿", "order": 0, "color": "#64748b", "bg": "#f2f2f2"},
    "💖": {"label": "需修订", "order": 1, "color": "#f43f5e", "bg": "#ffd9ec"},
    "🟡": {"label": "内审中", "order": 2, "color": "#f59e0b", "bg": "#fff8d9"},
    "🟢": {"label": "外审中", "order": 3, "color": "#22c55e", "bg": "#e8f9ee"},
    "✅": {"label": "已接受", "order": 4, "color": "#2563eb", "bg": "#dbeafe", "excludeFromStats": True},
}
SUMMARY_STATUS_META = {
    dot: meta for dot, meta in STATUS_META.items() if not meta.get("excludeFromStats")
}


ALIASES = {
    "APPLIED SCIENCES": "APPLIED SCIENCES-BASEL",
    "JOURNAL OF SUPERCOMPUTING": "JOURNAL OF SUPERCOMPUTING",
    "THE JOURNAL OF SUPERCOMPUTING": "JOURNAL OF SUPERCOMPUTING",
    "IEEE TRANS. AUTOMATION SCIENCE AND ENGINEERING": "IEEE TRANSACTIONS ON AUTOMATION SCIENCE AND ENGINEERING",
    "IEEE TNSRE": "IEEE TRANSACTIONS ON NEURAL SYSTEMS AND REHABILITATION ENGINEERING",
    "JOURNAL OF MATERIALS RESEARCH AND TECHNOLOGY": "Journal of Materials Research and Technology-JMR&T",
    "JOURNAL OF MATERIALS RESEARCH AND TECHNOLOGY-JMR&T": "Journal of Materials Research and Technology-JMR&T",
    "JOURNAL OF MATERIALS RESEARCH AND TECHNOLOGY-JMR&amp;T": "Journal of Materials Research and Technology-JMR&T",
    "FRONTIERS OF ARCHITECTURAL RESEARCH (FOAR)": "FRONTIERS OF ARCHITECTURAL RESEARCH",
    "SOCIAL SCIENCE & MEDICINE(SSM-S-26-05321)": "SOCIAL SCIENCE & MEDICINE",
    "SOCIAL SCIENCE AND MEDICINE": "SOCIAL SCIENCE & MEDICINE",
    "BMC MEDICAL RESEARCH METHODOLOGY": "BMC MEDICAL RESEARCH METHODOLOGY",
    "JOURNAL OF THERMAL ANALYSIS AND CALORIMETRY": "JOURNAL OF THERMAL ANALYSIS AND CALORIMETRY",
    "HUMANITIES AND SOCIAL SCIENCES COMMUNICATIONS": "HUMANITIES & SOCIAL SCIENCES COMMUNICATIONS",
    "IEEE TRANS AUTOMATION SCIENCE AND ENGINEERING": "IEEE TRANSACTIONS ON AUTOMATION SCIENCE AND ENGINEERING",
}


JCR_MANUAL = {
    "APPLIED SCIENCES": ("2.5", "Q2"),
    "APPLIED SCIENCES-BASEL": ("2.5", "Q2"),
    "ARCHIVES OF PUBLIC HEALTH": ("3.0", "Q2"),
    "AUTOMATION IN CONSTRUCTION": ("9.6", "Q1"),
    "BMC GERIATRICS": ("3.8", "Q1"),
    "BMC MEDICINE": ("8.7", "Q1"),
    "BMC MEDICAL RESEARCH METHODOLOGY": ("3.7", "Q1"),
    "BMC PUBLIC HEALTH": ("3.5", "Q1"),
    "BIOMEDICAL SIGNAL PROCESSING AND CONTROL": ("4.9", "Q1"),
    "BUILDINGS": ("3.1", "Q2"),
    "COMPUTERS IN BIOLOGY AND MEDICINE": ("7.0", "Q1"),
    "CONSTRUCTION AND BUILDING MATERIALS": ("7.4", "Q1"),
    "EGYPTIAN INFORMATICS JOURNAL": ("5.0", "Q1"),
    "ELECTRONICS": ("2.6", "Q2"),
    "ENERGY": ("9.0", "Q1"),
    "ENERGY AND BUILDINGS": ("6.6", "Q1"),
    "ENERGY REPORTS": ("4.7", "Q2"),
    "ENVIRONMENT DEVELOPMENT AND SUSTAINABILITY": ("4.2", "Q2"),
    "ENVIRONMENT, DEVELOPMENT AND SUSTAINABILITY": ("4.2", "Q2"),
    "FRONTIERS IN PUBLIC HEALTH": ("3.4", "Q1"),
    "FRONTIERS IN PSYCHOLOGY": ("2.9", "Q1"),
    "HUMANITIES & SOCIAL SCIENCES COMMUNICATIONS": ("3.6", "Q1"),
    "IEEE ACCESS": ("3.6", "Q2"),
    "IEEE TRANSACTIONS ON INSTRUMENTATION AND MEASUREMENT": ("5.6", "Q1"),
    "IMAGE AND VISION COMPUTING": ("4.7", "Q2"),
    "INTERNATIONAL JOURNAL FOR EQUITY IN HEALTH": ("4.0", "Q1"),
    "JOURNAL OF BIG DATA": ("8.1", "Q1"),
    "JOURNAL OF BUILDING ENGINEERING": ("6.7", "Q1"),
    "JOURNAL OF CLEANER PRODUCTION": ("9.7", "Q1"),
    "JOURNAL OF HEALTH, POPULATION AND NUTRITION": ("3.6", "Q2"),
    "JOURNAL OF VISUALIZED EXPERIMENTS": ("1.2", "Q3"),
    "JOVE": ("1.2", "Q3"),
    "JOURNAL OF MATERIALS RESEARCH AND TECHNOLOGY": ("6.2", "Q1"),
    "JOURNAL OF MATERIALS RESEARCH AND TECHNOLOGY-JMR&T": ("6.2", "Q1"),
    "JOURNAL OF THERMAL ANALYSIS AND CALORIMETRY": ("4.4", "Q1"),
    "JOURNAL OF SUPERCOMPUTING": ("2.7", "Q2"),
    "LAND": ("3.2", "Q2"),
    "NEURAL NETWORKS": ("6.0", "Q1"),
    "NEUROCOMPUTING": ("5.5", "Q1"),
    "PHYSICS OF FLUIDS": ("4.1", "Q1"),
    "PLOS ONE": ("2.9", "Q1"),
    "SCIENTIFIC REPORTS": ("3.9", "Q1"),
    "SENSORS": ("3.4", "Q2"),
    "SUSTAINABILITY": ("3.3", "Q2"),
    "SOCIAL SCIENCE & MEDICINE": ("5.0", "Q1"),
    "SUSTAINABLE CITIES AND SOCIETY": ("10.5", "Q1"),
    "SOFTWARE TESTING, VERIFICATION AND RELIABILITY": ("2.4", "Q2"),
    "SOFTWARE: PRACTICE AND EXPERIENCE": ("3.5", "Q2"),
    "UNIVERSAL ACCESS IN THE INFORMATION SOCIETY": ("2.4", "Q3"),
    "VIRTUAL REALITY": ("5.3", "Q1"),
}


AUTHOR_MAP = {
    "用于老年住宅活动分区功能分类的空间图神经网络": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "基于线性调度法的适老改造模块制造多目标优化": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "AgeFriendlyDiff：基于条件扩散的适老住宅改造三维可视化": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "社区老年日间照料中心多模态热舒适的时空深度学习评估与预测": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "GridMamba-Risk：基于网格状态空间模型的整屋三维点云跌倒风险空间预测": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "AccessGeometry：面向老年住宅无障碍合规评估的点云自动参数化建模": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Wanbao Ge；Yanting Wu",
    "AccessPath：面向老年居家环境自动无障碍评估的拓扑图式无障碍通行分析": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "基于相变材料的多层粮仓自适应多温区温度控制": "Ruili Liu；Quan Wen；Mazran Ismail",
    "基于多模态特征学习的依赖感知三维场景图生成：用于自动化居家适老环境评估": "Peng Chao",
    "基于条件 GAN 与随机森林的多源数据融合社区韧性评估：来自中国河南的证据": "Peng Chao",
    "老年游客对遗产建筑增强现实解说的接受度：扩展技术接受模型": "Xuejia Zhu；Suebsiri Saelee",
    "历史社区智慧适老化改造策略的居民支持：整合地方依恋与技术接受": "Xuejia Zhu；Suebsiri Saelee",
    "AccessStairNet：面向老年居家环境无障碍评估的台阶与门槛深度学习检测": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "室内适老环境多维韧性评估框架：基于 Google Gemini Pro 的大模型指标构建": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "粮食储藏设施制冷系统的真实世界能效：来自中国河南的大规模实地研究": "Quan Wen；Ruili Liu；Mazran Ismail",
    "基于注意力机制与跨模态特征融合的痴呆早期检测多模态情绪分析": "Peng Chao",
    "用于粮仓全年能源管理的双模式辐射制冷与太阳能供热屋面板系统": "Ruili Liu；Quan Wen；Mazran Ismail",
    "面向居家适老环境评估的室内点云语义分割可迁移深度学习网络": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Nooriati Binti Taib；Jestin Bin Nordin",
    "面向居家适老环境评估的扩散模型点云合成": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Nooriati Binti Taib；Jestin Bin Nordin",
    "老龄化夹缝：面向中国老旧居住社区低收入独居老人的智能安全韧性评估框架": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Nooriati Binti Taib；Jestin Bin Nordin",
    "FRSGraph：面向老年居家环境的语义图 Transformer 跌倒风险空间预测": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Nooriati Binti Taib；Jestin Bin Nordin",
    "使用基于深度学习的情绪分析评估并优化老年照护政策实施：一项多源研究": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Nooriati Binti Taib；Jestin Bin Nordin",
    "城市老年住宅空间热舒适的多模态感知与物理信息神经网络评估": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Nooriati Binti Taib；Jestin Bin Nordin",
    "适老建成环境专业人员对 AI-BIM 评估工具的接受度": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "面向多层粮仓全年能源优化的双模式辐射制冷与太阳能供热": "Ruili Liu；Quan Wen；Mazran Ismail",
    "相变材料赋能的多层粮仓自适应多温区控制：实验与数值结合研究": "Ruili Liu；Quan Wen；Mazran Ismail",
    "面向多层粮仓围护结构的梯度纳米结构气凝胶复合保温材料": "Ruili Liu；Quan Wen；Mazran Ismail",
    "生成式 AI 驱动的适老室内改造可视化": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "cGAN 辅助的适老住宅改造多目标优化": "Peng Chao",
    "元学习增强的少样本居家安全等级分类框架": "Quan Wen",
    "代码漏洞检测深度学习模型的系统评估：具有多种表示策略的模块化框架": "Xueping Han",
    "基于图神经网络与注意力机制的养老社区社会情感网络分析与孤独预防": "Quan Wen",
    "中国 HIV 老年人适老居住环境因素因果模型：文本挖掘、模糊 DEMATEL 与区域比较": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "老年用户对居家养老智能家居传感器系统的接受度：整合技术接受模型、隐私计算理论与空间自主性": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "基于三维点云特征与 SHAP 可解释集成学习的老年住宅环境跌倒风险空间预测": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Nooriati Binti Taib；Jestin Bin Nordin",
    "适老住宅改造的混合现实与条件 GAN 集成框架：两阶段修复与 360 度全景可视化": "Quan Wen",
    "通过基于扩散的生成式设计提升适老住宅改造：面向安全与视觉舒适的双目标框架": "Quan Wen",
    "对比学习增强的 RGB-D 居家安全区域分割知识蒸馏": "Quan Wen",
    "智慧养老系统中智能情绪监测与干预的双通道注意力机制": "Quan Wen；Yanting Wu；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "灵活半监督元学习少样本居家安全评估网络": "Peng Chao",
    "VLM 驱动的适老住宅缺陷自动评估与报告生成": "Quan Wen",
    "住宅环境设计特征对老年人生理心理福祉影响的 VR 实验": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "LLM 生成测试用例优化：AI 辅助软件测试中的质量缺陷表征与缓解": "Xueping Han",
    "用于自动代码审查评论生成的上下文与结构特征融合混合 Transformer-MLP 模型": "Xueping Han",
    "轻量级 Transformer：面向资源受限老年智能家居边缘 IoT 入侵检测的知识蒸馏与区块链协同": "Peng Chao",
    "基于大语言模型苏格拉底式推理的可解释自动代码审查": "Xueping Han",
    "DHA-BiGRU：用于自动代码审查评论分类的双注意力层次门控 BiGRU": "Xueping Han",
    "从空间符号到社会实践：适老文化主题建筑空间意义建构的动态框架": "Xuejia Zhu；Suebsiri Saelee",
    "遗产街区中老年人的意义建构与地方依恋：结构方程模型框架": "Xuejia Zhu；Suebsiri Saelee",
    "面向文化主题公共建筑老年用户的空间意义感知量表开发：因子分析研究设计": "Xuejia Zhu；Suebsiri Saelee",
    "养老照护中公众对使用 AI 的照护提供者的信任：基于能力、仁爱与诚信视角的概念综述": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Qi Liu；Wanbao Ge；Wenjing Xu；Jing Zhang；Yana Zhang；Jiasheng Zhou",
    "后疫情时代中国适老社区韧性建设（由 JHPN 转投）": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "FRSPTNet：老年居家点云环境跌倒风险区域分割的多尺度超补丁 Transformer": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "健康老龄化评估的元学习框架：具有人群泛化能力的注意力神经过程": "Quan Wen；Yanting Wu；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "Digital-social connectedness and healthy ageing transitions in a multiple cohort study": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "粮食储藏仓制冷系统真实世界能效评估：来自中国河南 65 个设施的证据": "Quan Wen；Ruili Liu；Mazran Ismail",
    "中国老龄化背景下农村学校改造养老设施的公平导向服务就绪框架": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "双层级注意力增强迁移学习用于居家适老环境评估中的点云语义分割": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "基于三维点云语义分析的适老住宅合规自动评估": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "面向适老韧性评估的 BIM 集成空间世界模型：概念框架与研究议程": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "被遗忘之外：中国农村独居老人的低成本智能安全韧性框架": "Quan Wen",
    "适老社区时序评估的贝叶斯元学习框架": "Quan Wen；Mazran Ismail；Yanting Wu；Muhammad Hafeez Abdul Nasir",
    "中国老年 HIV 感染者适老居住环境评估的个体中心框架": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "面向老年人的15分钟城市：健康与适老城市化的操作框架": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "后疫情时代中国适老社区韧性建设：循证多准则评估框架": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir；Yanting Wu",
    "香港高层社区老年居民火灾韧性的循证评估框架": "Quan Wen",
    "挖掘马来西亚商业建筑能源灵活性的基于 LSTM 的模型预测控制方法": "Quan Wen；Mazran Ismail；Muhammad Hafeez Abdul Nasir",
    "多模态情绪特征可视化映射与智能交互设计": "Zhenhu Liu；Wanbao Ge；Zhenhua Yang；Qi Liu；Quan Wen",
}

CORRESPONDING_AUTHOR_MAP = {
    "用于老年住宅活动分区功能分类的空间图神经网络": ["Quan Wen", "Mazran Ismail"],
    "基于线性调度法的适老改造模块制造多目标优化": ["Quan Wen"],
    "AgeFriendlyDiff：基于条件扩散的适老住宅改造三维可视化": ["Quan Wen"],
    "GridMamba-Risk：基于网格状态空间模型的整屋三维点云跌倒风险空间预测": ["Quan Wen", "Mazran Ismail"],
    "社区老年日间照料中心多模态热舒适的时空深度学习评估与预测": ["Quan Wen", "Mazran Ismail"],
    "面向居家适老环境评估的室内点云语义分割可迁移深度学习网络": ["Quan Wen", "Mazran Ismail"],
    "AccessGeometry：面向老年住宅无障碍合规评估的点云自动参数化建模": ["Quan Wen", "Mazran Ismail"],
    "AccessPath：面向老年居家环境自动无障碍评估的拓扑图式无障碍通行分析": ["Quan Wen"],
    "基于相变材料的多层粮仓自适应多温区温度控制": ["Quan Wen"],
    "基于多模态特征学习的依赖感知三维场景图生成：用于自动化居家适老环境评估": ["Peng Chao"],
    "基于条件 GAN 与随机森林的多源数据融合社区韧性评估：来自中国河南的证据": ["Peng Chao"],
    "老年游客对遗产建筑增强现实解说的接受度：扩展技术接受模型": ["Suebsiri Saelee"],
    "历史社区智慧适老化改造策略的居民支持：整合地方依恋与技术接受": ["Suebsiri Saelee"],
    "AccessStairNet：面向老年居家环境无障碍评估的台阶与门槛深度学习检测": ["Quan Wen"],
    "室内适老环境多维韧性评估框架：基于 Google Gemini Pro 的大模型指标构建": ["Quan Wen"],
    "粮食储藏设施制冷系统的真实世界能效：来自中国河南的大规模实地研究": ["Quan Wen"],
    "基于注意力机制与跨模态特征融合的痴呆早期检测多模态情绪分析": ["Peng Chao"],
    "用于粮仓全年能源管理的双模式辐射制冷与太阳能供热屋面板系统": ["Quan Wen"],
    "面向居家适老环境评估的扩散模型点云合成": ["Quan Wen", "Mazran Ismail"],
    "老龄化夹缝：面向中国老旧居住社区低收入独居老人的智能安全韧性评估框架": ["Quan Wen", "Mazran Ismail"],
    "FRSGraph：面向老年居家环境的语义图 Transformer 跌倒风险空间预测": ["Quan Wen", "Mazran Ismail"],
    "使用基于深度学习的情绪分析评估并优化老年照护政策实施：一项多源研究": ["Quan Wen", "Mazran Ismail"],
    "城市老年住宅空间热舒适的多模态感知与物理信息神经网络评估": ["Quan Wen", "Mazran Ismail"],
    "适老建成环境专业人员对 AI-BIM 评估工具的接受度": ["Quan Wen"],
    "面向多层粮仓全年能源优化的双模式辐射制冷与太阳能供热": ["Quan Wen"],
    "相变材料赋能的多层粮仓自适应多温区控制：实验与数值结合研究": ["Quan Wen"],
    "面向多层粮仓围护结构的梯度纳米结构气凝胶复合保温材料": ["Quan Wen"],
    "生成式 AI 驱动的适老室内改造可视化": ["Quan Wen"],
    "cGAN 辅助的适老住宅改造多目标优化": ["Peng Chao"],
    "元学习增强的少样本居家安全等级分类框架": ["Quan Wen"],
    "代码漏洞检测深度学习模型的系统评估：具有多种表示策略的模块化框架": ["Xueping Han"],
    "基于图神经网络与注意力机制的养老社区社会情感网络分析与孤独预防": ["Quan Wen"],
    "中国 HIV 老年人适老居住环境因素因果模型：文本挖掘、模糊 DEMATEL 与区域比较": ["Quan Wen"],
    "老年用户对居家养老智能家居传感器系统的接受度：整合技术接受模型、隐私计算理论与空间自主性": ["Quan Wen"],
    "基于三维点云特征与 SHAP 可解释集成学习的老年住宅环境跌倒风险空间预测": ["Quan Wen", "Mazran Ismail"],
    "适老住宅改造的混合现实与条件 GAN 集成框架：两阶段修复与 360 度全景可视化": ["Quan Wen"],
    "通过基于扩散的生成式设计提升适老住宅改造：面向安全与视觉舒适的双目标框架": ["Quan Wen"],
    "对比学习增强的 RGB-D 居家安全区域分割知识蒸馏": ["Quan Wen"],
    "智慧养老系统中智能情绪监测与干预的双通道注意力机制": ["Quan Wen"],
    "灵活半监督元学习少样本居家安全评估网络": ["Peng Chao"],
    "VLM 驱动的适老住宅缺陷自动评估与报告生成": ["Quan Wen"],
    "住宅环境设计特征对老年人生理心理福祉影响的 VR 实验": ["Quan Wen"],
    "LLM 生成测试用例优化：AI 辅助软件测试中的质量缺陷表征与缓解": ["Xueping Han"],
    "用于自动代码审查评论生成的上下文与结构特征融合混合 Transformer-MLP 模型": ["Xueping Han"],
    "轻量级 Transformer：面向资源受限老年智能家居边缘 IoT 入侵检测的知识蒸馏与区块链协同": ["Peng Chao"],
    "基于大语言模型苏格拉底式推理的可解释自动代码审查": ["Xueping Han"],
    "DHA-BiGRU：用于自动代码审查评论分类的双注意力层次门控 BiGRU": ["Xueping Han"],
    "从空间符号到社会实践：适老文化主题建筑空间意义建构的动态框架": ["Suebsiri Saelee"],
    "遗产街区中老年人的意义建构与地方依恋：结构方程模型框架": ["Suebsiri Saelee"],
    "面向文化主题公共建筑老年用户的空间意义感知量表开发：因子分析研究设计": ["Suebsiri Saelee"],
    "养老照护中公众对使用 AI 的照护提供者的信任：基于能力、仁爱与诚信视角的概念综述": ["Quan Wen"],
    "后疫情时代中国适老社区韧性建设（由 JHPN 转投）": ["Quan Wen"],
    "FRSPTNet：老年居家点云环境跌倒风险区域分割的多尺度超补丁 Transformer": ["Quan Wen"],
    "健康老龄化评估的元学习框架：具有人群泛化能力的注意力神经过程": ["Quan Wen", "Mazran Ismail"],
    "Digital-social connectedness and healthy ageing transitions in a multiple cohort study": ["Quan Wen"],
    "粮食储藏仓制冷系统真实世界能效评估：来自中国河南 65 个设施的证据": ["Quan Wen"],
    "中国老龄化背景下农村学校改造养老设施的公平导向服务就绪框架": ["Quan Wen"],
    "双层级注意力增强迁移学习用于居家适老环境评估中的点云语义分割": ["Quan Wen", "Mazran Ismail"],
    "基于三维点云语义分析的适老住宅合规自动评估": ["Quan Wen"],
    "面向适老韧性评估的 BIM 集成空间世界模型：概念框架与研究议程": ["Quan Wen"],
    "被遗忘之外：中国农村独居老人的低成本智能安全韧性框架": ["Quan Wen"],
    "适老社区时序评估的贝叶斯元学习框架": ["Quan Wen", "Mazran Ismail"],
    "中国老年 HIV 感染者适老居住环境评估的个体中心框架": ["Quan Wen"],
    "面向老年人的15分钟城市：健康与适老城市化的操作框架": ["Quan Wen"],
    "后疫情时代中国适老社区韧性建设：循证多准则评估框架": ["Quan Wen"],
    "香港高层社区老年居民火灾韧性的循证评估框架": ["Quan Wen"],
    "挖掘马来西亚商业建筑能源灵活性的基于 LSTM 的模型预测控制方法": ["Quan Wen", "Mazran Ismail"],
    "多模态情绪特征可视化映射与智能交互设计": ["Zhenhu Liu"],
}


RECOMMEND_MAP = {
    "基于条件 GAN 与随机森林的多源数据融合社区韧性评估：来自中国河南的证据": "Frontiers in Environmental Science；International Journal of Disaster Risk Reduction；Sustainable Cities and Society",
    "基于注意力机制与跨模态特征融合的痴呆早期检测多模态情绪分析": "Frontiers in Neurology；IEEE Journal of Biomedical and Health Informatics；Biomedical Signal Processing and Control；Computers in Biology and Medicine",
    "基于多模态特征学习的依赖感知三维场景图生成：用于自动化居家适老环境评估": "Applied Sciences；Pattern Recognition；Image and Vision Computing；IEEE Access",
    "灵活半监督元学习少样本居家安全评估网络": "IEEE Access；Engineering Applications of Artificial Intelligence；Sensors",
    "面向多层粮仓围护结构的梯度纳米结构气凝胶复合保温材料": "Applied Thermal Engineering；Journal of Materials Research and Technology；Construction and Building Materials",
    "基于线性调度法的适老改造模块制造多目标优化": "Computers & Industrial Engineering",
    "适老社区时序评估的贝叶斯元学习框架": "Neurocomputing；Energy；BMC Medical Research Methodology",
    "适老建成环境专业人员对 AI-BIM 评估工具的接受度": "Cities；Buildings",
    "AgeFriendlyDiff：基于条件扩散的适老住宅改造三维可视化": "Multimedia Tools and Applications；The Visual Computer；Image and Vision Computing；Soft Computing",
    "用于粮仓全年能源管理的双模式辐射制冷与太阳能供热屋面板系统": "Solar Energy；Journal of Building Engineering；Energy；Energy and Buildings",
    "用于老年住宅活动分区功能分类的空间图神经网络": "Neurocomputing；Engineering Applications of Artificial Intelligence",
    "社区老年日间照料中心多模态热舒适的时空深度学习评估与预测": "Energy and Buildings；Energy",
    "cGAN 辅助的适老住宅改造多目标优化": "Buildings；Energy and Buildings",
    "住宅环境设计特征对老年人生理心理福祉影响的 VR 实验": "Journal of Building Engineering；PLOS ONE",
    "生成式 AI 驱动的适老室内改造可视化": "Journal of Building Engineering；Applied Sciences",
    "GridMamba-Risk：基于网格状态空间模型的整屋三维点云跌倒风险空间预测": "The Journal of Supercomputing；Cluster Computing；Multimedia Tools and Applications；Soft Computing",
    "面向居家适老环境评估的室内点云语义分割可迁移深度学习网络": "Multimedia Tools and Applications；Soft Computing；Image and Vision Computing；The Journal of Supercomputing",
    "AccessGeometry：面向老年住宅无障碍合规评估的点云自动参数化建模": "Environment, Development and Sustainability；International Journal of Human-Computer Interaction；Journal of Building Engineering",
    "AccessPath：面向老年居家环境自动无障碍评估的拓扑图式无障碍通行分析": "Environment, Development and Sustainability；International Journal of Human-Computer Interaction；Disability and Rehabilitation",
    "AccessStairNet：面向老年居家环境无障碍评估的台阶与门槛深度学习检测": "Environment, Development and Sustainability；International Journal of Human-Computer Interaction；Multimedia Tools and Applications",
    "面向居家适老环境评估的扩散模型点云合成": "Multimedia Tools and Applications；Soft Computing；The Visual Computer；Image and Vision Computing",
    "老龄化夹缝：面向中国老旧居住社区低收入独居老人的智能安全韧性评估框架": "Environment, Development and Sustainability；International Journal for Equity in Health；BMC Geriatrics",
    "FRSGraph：面向老年居家环境的语义图 Transformer 跌倒风险空间预测": "The Journal of Supercomputing；Cluster Computing；Multimedia Tools and Applications",
    "使用基于深度学习的情绪分析评估并优化老年照护政策实施：一项多源研究": "Social Science & Medicine；Health Research Policy and Systems；BMC Health Services Research",
    "城市老年住宅空间热舒适的多模态感知与物理信息神经网络评估": "Environment, Development and Sustainability；Journal of Thermal Analysis and Calorimetry；Building and Environment",
}


def norm_name(value):
    value = html.unescape(value or "")
    value = re.sub(r"\([^)]*\)", "", value)
    value = value.replace("&", " AND ")
    value = re.sub(r"[^A-Za-z0-9]+", " ", value.upper()).strip()
    value = re.sub(r"^THE ", "", value)
    return value


def display_norm(value):
    raw = html.unescape(value or "").strip()
    raw = re.sub(r"\s+", " ", raw)
    key = raw.upper()
    return ALIASES.get(key, raw)


def clean_cell(value):
    value = re.sub(r"<br\s*/?>", "；", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def load_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def first_existing(*paths):
    for path in paths:
        if path.exists():
            return path
    return paths[0]


def zone_num(text):
    m = re.search(r"([1-4])", text or "")
    return m.group(1) if m else ""


def build_cas_index():
    rows = load_csv(first_existing(ROOT / "journals" / "cas2025.csv", HOME / "cas2025.csv"))
    out = {}
    for row in rows:
        key = norm_name(row.get("刊名"))
        out.setdefault(key, []).append(row)
    return out


def build_xr_index():
    rows = load_csv(first_existing(ROOT / "journals" / "xr2026.csv", HOME / "xr2026.csv"))
    out = {}
    for row in rows:
        key = norm_name(row.get("刊名"))
        out.setdefault(key, []).append(row)
    return out


def build_ei_set():
    path = first_existing(ROOT / "journals" / "ei_journals_raw.csv", HOME / "EIlist" / "ei_journals_raw.csv")
    rows = load_csv(path)
    return {norm_name(r.get("Journal_Name") or r.get("Journal") or r.get("Source title")) for r in rows}


def build_jcr_index():
    out = {}
    for path in [
        ROOT / "journals" / "ssci_top100.csv",
        HOME / "ssci-top100-journals" / "sscitop100.csv",
        HOME / "ssci_top100.csv",
    ]:
        for row in load_csv(path):
            name = row.get("期刊名称") or row.get("journal_name_standard") or row.get("journal_name_raw")
            jif = row.get("JCR_2024JIF") or row.get("jcr_2024_jif")
            q = row.get("JCR_Quartile") or row.get("jcr_2024_quartile")
            cat = row.get("JCR_Category") or row.get("cas_2025_minor_category_reference")
            if name and (jif or q):
                out[norm_name(name)] = {"if": jif or "", "jcr": q or "", "category": cat or ""}
    for name, (jif, q) in JCR_MANUAL.items():
        out.setdefault(norm_name(name), {"if": jif, "jcr": q, "category": ""})
    return out


def cas_info(name, cas_index):
    rows = cas_index.get(norm_name(name), [])
    if not rows:
        return ""
    major = zone_num(rows[0].get("大类分区"))
    minors = sorted({zone_num(r.get("小类分区")) for r in rows if zone_num(r.get("小类分区"))})
    return f"CAS大{major}小{'/'.join(minors)}"


def xr_info(name, xr_index):
    rows = xr_index.get(norm_name(name), [])
    if not rows:
        return ""
    major = zone_num(rows[0].get("大类学科新锐分区"))
    minors = sorted({zone_num(r.get("小类学科新锐分区")) for r in rows if zone_num(r.get("小类学科新锐分区"))})
    return f"XR大{major}小{'/'.join(minors)}"


def cas_xr_info(name, cas_index, xr_index):
    parts = []
    cas = cas_info(name, cas_index)
    xr = xr_info(name, xr_index)
    if cas:
        parts.append(cas)
    if xr:
        parts.append(xr)
    return "；".join(parts)


def index_type(name, cas_index, xr_index, ei_set):
    cas_rows = cas_index.get(norm_name(name), [])
    xr_rows = xr_index.get(norm_name(name), [])
    tags = set()
    for row in cas_rows:
        ws = row.get("web_science", "")
        if "SCIE" in ws:
            tags.add("SCIE")
        if "SSCI" in ws:
            tags.add("SSCI")
    for row in xr_rows:
        db = row.get("数据库", "")
        if "SCIE" in db:
            tags.add("SCIE")
        if "SSCI" in db:
            tags.add("SSCI")
        if "ESCI" in db:
            tags.add("ESCI")
    if norm_name(name) in ei_set:
        tags.add("EI")
    if "SCIE" in tags and "SSCI" in tags:
        base = "SCIE&SSCI"
    elif "SCIE" in tags:
        base = "SCIE"
    elif "SSCI" in tags:
        base = "SSCI"
    else:
        base = "ESCI" if "ESCI" in tags else ""
    if "EI" in tags:
        return f"{base}+EI" if base else "EI"
    return base


def metric_info(name, jcr_index):
    info = jcr_index.get(norm_name(name), {})
    return info.get("jcr", ""), info.get("if", "")


def parse_rows():
    data_path = ROOT / "status_data.json"
    force_index = os.environ.get("WEN_STATUS_FROM_INDEX") == "1"
    if data_path.exists() and not force_index:
        existing = json.loads(data_path.read_text(encoding="utf-8"))
        if existing:
            rows = []
            for row in existing:
                dot = row.get("statusDot", "⚪")
                if dot not in STATUS_META:
                    dot = "⚪"
                rows.append({
                    "statusDot": dot,
                    "status": row.get("status") or STATUS_META[dot]["label"],
                    "statusOrder": STATUS_META[dot]["order"],
                    "title": row.get("title", ""),
                    "journalTrack": row.get("journalTrack", ""),
                    "submissionSystemInfo": row.get("submissionSystemInfo", ""),
                    "bg": row.get("bg") or STATUS_META[dot]["bg"],
                    "updatedAt": row.get("updatedAt", ""),
                })
            return rows

    source = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<table class="paper-status-table"[\s\S]*?</table>', source, flags=re.I)
    if not m:
        raise RuntimeError("paper-status-table not found")
    table = m.group(0)
    rows = []
    for tr in re.findall(r"<tr[^>]*>[\s\S]*?</tr>", table, flags=re.I):
        cells = re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr, flags=re.I)
        if len(cells) < 3:
            continue
        bgcolor = re.search(r'background-color:\s*(#[0-9A-Fa-f]{6})', tr)
        status = clean_cell(cells[0])
        title = clean_cell(cells[1])
        track = clean_cell(cells[2])
        submission_system_info = clean_cell(cells[3]) if len(cells) >= 4 else ""
        dot = status[0] if status else "⚪"
        if dot not in STATUS_META:
            dot = "⚪"
        rows.append({
            "statusDot": dot,
            "status": STATUS_META[dot]["label"],
            "statusOrder": STATUS_META[dot]["order"],
            "title": title,
            "journalTrack": track,
            "submissionSystemInfo": submission_system_info,
            "bg": bgcolor.group(1) if bgcolor else STATUS_META[dot]["bg"],
            "updatedAt": "",
        })
    return rows


def parse_submission_system_info():
    path = ROOT / "submission_system_overrides.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_similarity_info():
    path = ROOT / "similarity_overrides.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_row_overrides():
    path = ROOT / "row_overrides.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_situation_from_readme():
    out = {}
    path = ROOT / "README.md"
    if not path.exists():
        path = HOME / "wenallpapersstatus" / "README.md"
    if not path.exists():
        path = None
    if path:
        text = path.read_text(encoding="utf-8")
        for tr in re.findall(r"<tr[^>]*>[\s\S]*?</tr>", text, flags=re.I):
            cells = re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr, flags=re.I)
            if len(cells) >= 5:
                title = clean_cell(cells[2])
                situation = clean_cell(cells[4])
                if title and situation:
                    out[title] = situation

    override_path = ROOT / "situation_overrides.json"
    if override_path.exists():
        out.update(json.loads(override_path.read_text(encoding="utf-8")))
    return out


def is_rejected_track_segment(value):
    return bool(re.search(r"(?i)\b(rejected|declined|reject|withdrawn|withdrawal)\b|拒稿|拒绝|退稿|撤稿", value or ""))


def journal_name_from_track_segment(value):
    value = re.sub(r"（.*?）", "", value or "").strip()
    value = re.sub(r"\(.*?\)", "", value).strip()
    return display_norm(value)


def latest_rejected_journal(track):
    parts = [part.strip() for part in re.split(r"\s*→\s*", track or "") if part.strip()]
    for part in reversed(parts):
        if is_rejected_track_segment(part):
            return journal_name_from_track_segment(part)
    return ""


def has_rejected_track(track):
    return any(is_rejected_track_segment(part) for part in re.split(r"\s*→\s*", track or ""))


def current_journal(row):
    track = row["journalTrack"]
    if not track:
        return ""
    last = re.split(r"\s*→\s*", track)[-1].strip()
    if row["status"] == "待投稿":
        if has_rejected_track(track):
            return ""
        return journal_name_from_track_segment(last)
    return journal_name_from_track_segment(last)


def enrich_rows(rows):
    cas_index = build_cas_index()
    xr_index = build_xr_index()
    ei_set = build_ei_set()
    jcr_index = build_jcr_index()
    situation_by_title = parse_situation_from_readme()
    submission_system_by_title = parse_submission_system_info()
    similarity_by_title = parse_similarity_info()
    row_overrides_by_title = parse_row_overrides()
    today = dt.date.today().isoformat()
    for row in rows:
        row_override = row_overrides_by_title.get(row["title"], {})
        if row_override:
            dot = row_override.get("statusDot")
            if dot in STATUS_META:
                row["statusDot"] = dot
                row["status"] = row_override.get("status") or STATUS_META[dot]["label"]
                row["statusOrder"] = STATUS_META[dot]["order"]
                row["bg"] = STATUS_META[dot]["bg"]
            for key in ("journalTrack", "submissionSystemInfo", "updatedAt"):
                if key in row_override:
                    row[key] = row_override[key]
        journal = current_journal(row)
        row["currentJournal"] = journal
        row["similarity"] = similarity_by_title.get(row["title"], "")
        row["casXr"] = cas_xr_info(journal, cas_index, xr_index) if journal else ""
        row["cas"] = ""
        row["xr"] = ""
        row["jcr"], row["impactFactor"] = metric_info(journal, jcr_index) if journal else ("", "")
        row["indexType"] = index_type(journal, cas_index, xr_index, ei_set) if journal else ""
        row["recommendedJournals"] = RECOMMEND_MAP.get(row["title"], "")
        row["authors"] = row_override.get("authors", AUTHOR_MAP.get(row["title"], ""))
        row["correspondingAuthors"] = row_override.get(
            "correspondingAuthors",
            CORRESPONDING_AUTHOR_MAP.get(row["title"], []),
        )
        row["updatedAt"] = row.get("updatedAt") or today
        row["submissionSystemInfo"] = submission_system_by_title.get(row["title"], row.get("submissionSystemInfo", ""))
        row["situation"] = situation_by_title.get(row["title"], "")
        row["impactSort"] = float(row["impactFactor"]) if re.fullmatch(r"\d+(\.\d+)?", row["impactFactor"] or "") else -1
    return rows


def render(rows):
    counts = {meta["label"]: 0 for meta in STATUS_META.values()}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    today = dt.date.today().isoformat()
    rows_json = json.dumps(rows, ensure_ascii=False)
    legend_rows = "\n".join(
        f'<tr><td>{dot}</td><td>{meta["label"]}</td><td>{counts.get(meta["label"], 0)}</td></tr>'
        for dot, meta in SUMMARY_STATUS_META.items()
    )
    summary_cards = "\n      ".join(
        f'<article class="stat-card" style="--accent:{meta["color"]}"><span class="dot">{dot}</span><div><strong>{counts.get(meta["label"], 0)}</strong><span>{meta["label"]}</span></div></article>'
        for dot, meta in SUMMARY_STATUS_META.items()
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>全部论文投稿状态</title>
  <style>
    :root {{ color-scheme: light; --bg:#f8fafc; --panel:#fff; --text:#111827; --muted:#64748b; --line:#e5e7eb; --title-width:360px; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: Arial, "Microsoft YaHei", sans-serif; color:var(--text); background:var(--bg); }}
    main {{ max-width: 1680px; margin:0 auto; padding:24px; }}
    header {{ display:flex; align-items:end; justify-content:space-between; gap:16px; margin-bottom:18px; }}
    h1 {{ margin:0; font-size:28px; letter-spacing:0; }}
    .updated {{ color:var(--muted); font-size:13px; white-space:nowrap; }}
    .header-actions {{ display:flex; flex-direction:column; align-items:flex-end; gap:8px; }}
    .nc-link {{ display:inline-block; border:1px solid var(--line); border-radius:6px; padding:8px 10px; background:#fff; color:#1d4ed8; font-size:13px; font-weight:700; text-decoration:none; }}
    .nc-link:hover {{ border-color:#93c5fd; background:#eff6ff; }}
    .summary {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; margin-bottom:16px; }}
    .stat-card {{ display:flex; align-items:center; gap:12px; min-height:72px; padding:12px 14px; border:1px solid var(--line); border-left:8px solid var(--accent); border-radius:8px; background:var(--panel); }}
    .dot {{ font-size:22px; line-height:1; }}
    .stat-card strong {{ display:block; font-size:24px; line-height:1.1; }}
    .stat-card span:last-child {{ display:block; margin-top:4px; color:var(--muted); font-size:13px; }}
    .dashboard {{ display:grid; grid-template-columns:minmax(320px,2fr) minmax(220px,.8fr); gap:14px; align-items:stretch; margin-bottom:18px; }}
    .panel {{ border:1px solid var(--line); border-radius:8px; background:var(--panel); overflow:hidden; }}
    .chart-panel {{ padding:12px; }}
    .chart-panel img {{ display:block; width:100%; height:auto; }}
    .legend-panel {{ padding:18px; }}
    .legend-panel h2, .table-panel h2 {{ margin:0 0 12px; font-size:22px; font-weight:800; }}
    .legend-panel table {{ width:100%; border-collapse:collapse; font-size:18px; font-weight:700; }}
    .legend-panel td {{ padding:12px 8px; border-bottom:1px solid var(--line); }}
    .legend-panel td:first-child {{ width:42px; font-size:24px; line-height:1; }}
    .legend-panel td:last-child {{ text-align:right; font-size:20px; font-weight:800; }}
    .controls {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:0 0 12px; }}
    .controls button {{ border:1px solid var(--line); background:#fff; color:var(--text); border-radius:6px; padding:8px 10px; cursor:pointer; font-weight:700; }}
    .controls button.active {{ border-color:#2563eb; color:#1d4ed8; background:#eff6ff; }}
    .column-panel {{ display:flex; flex-wrap:wrap; gap:8px 14px; padding:10px; margin-bottom:12px; border:1px solid var(--line); border-radius:8px; background:#fff; }}
    .column-panel label {{ font-size:13px; color:#334155; white-space:nowrap; }}
    .table-panel {{ padding:14px; overflow-x:auto; }}
    table.paper-status-table {{ width:100%; min-width:1900px; border-collapse:collapse; table-layout:auto; font-size:13px; }}
    table.paper-status-table th, table.paper-status-table td {{ padding:9px 10px; border:1px solid var(--line); vertical-align:top; }}
    table.paper-status-table th {{ background:#f8fafc; position:sticky; top:0; z-index:2; text-align:left; }}
    table.paper-status-table th[data-key="status"], table.paper-status-table td[data-key="status"] {{ min-width:48px; width:54px; text-align:center; white-space:nowrap; position:sticky; left:0; z-index:3; }}
    table.paper-status-table th[data-key="title"], table.paper-status-table td[data-key="title"] {{ min-width:var(--title-width); width:var(--title-width); position:sticky; left:54px; z-index:3; }}
    table.paper-status-table th[data-key="title"] {{ z-index:4; }}
    table.paper-status-table td[data-key="similarity"] {{ min-width:82px; white-space:nowrap; text-align:center; }}
    table.paper-status-table td.similarity-low {{ color:#15803d; }}
    table.paper-status-table td.similarity-mid {{ color:#d97706; }}
    table.paper-status-table td.similarity-high {{ color:#dc2626; font-weight:800; }}
    table.paper-status-table td[data-key="currentJournal"] {{ min-width:230px; }}
    table.paper-status-table td[data-key="journalTrack"], table.paper-status-table td[data-key="recommendedJournals"], table.paper-status-table td[data-key="situation"], table.paper-status-table td[data-key="submissionSystemInfo"] {{ min-width:320px; }}
    table.paper-status-table td[data-key="casXr"] {{ min-width:180px; }}
    table.paper-status-table td[data-key="authors"] {{ min-width:260px; }}
    .corresponding-author {{ color:#dc2626; font-weight:800; }}
    .empty {{ color:#94a3b8; }}
    @media (max-width:900px) {{ main{{padding:16px;}} header{{display:block;}} .header-actions{{align-items:flex-start;margin-top:8px;}} .updated{{display:block;}} .dashboard{{grid-template-columns:1fr;}} }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>全部论文投稿状态</h1>
      <div class="header-actions">
        <a class="nc-link" href="nc.html">NC 写作方向进度面板</a>
        <span class="updated">最后更新：{today}</span>
      </div>
    </header>
    <section class="summary">
      {summary_cards}
    </section>
    <section class="dashboard">
      <div class="panel chart-panel"><img src="status_bar_chart.svg" alt="论文状态统计饼图"></div>
      <aside class="panel legend-panel"><h2>颜色图例</h2><table><tbody>{legend_rows}</tbody></table></aside>
    </section>
    <section class="panel table-panel">
      <h2>全部论文状态总表</h2>
      <div class="controls">
        <button type="button" data-sort="status" class="active">按照投稿状态</button>
        <button type="button" data-sort="impact">按照影响因子</button>
        <button type="button" data-sort="updated">按照最近稿件更新时间</button>
        <button type="button" data-title-width="260px">标题列窄</button>
        <button type="button" data-title-width="360px" class="title-width-active">标题列标准</button>
        <button type="button" data-title-width="520px">标题列宽</button>
        <button type="button" id="showAllColumns">全部显示各列</button>
      </div>
      <div id="columnToggles" class="column-panel" aria-label="选择显示列"></div>
      <table class="paper-status-table">
        <thead><tr id="tableHead"></tr></thead>
        <tbody id="tableBody"></tbody>
      </table>
    </section>
  </main>
  <script>
    const rows = {rows_json};
    const fixedKeys = new Set(["status", "title"]);
    const columns = [
      ["status", "状态"],
      ["title", "论文标题"],
      ["similarity", "重复率"],
      ["currentJournal", "当前所在期刊名称"],
      ["submissionSystemInfo", "投稿系统信息"],
      ["casXr", "CAS/XR分区"],
      ["jcr", "JCR分区"],
      ["impactFactor", "IF"],
      ["indexType", "收录类型"],
      ["recommendedJournals", "推荐期刊"],
      ["authors", "论文作者"],
      ["updatedAt", "状态更新时间"],
      ["journalTrack", "Journal Track"],
      ["situation", "情况说明"]
    ];
    const hidden = new Set(JSON.parse(localStorage.getItem("paperStatusHiddenColumns") || "[]"));
    let currentSort = "status";
    let titleWidth = localStorage.getItem("paperStatusTitleWidth") || "360px";

    function applyTitleWidth() {{
      document.documentElement.style.setProperty("--title-width", titleWidth);
      document.querySelectorAll(".controls button[data-title-width]").forEach(button => {{
        button.classList.toggle("title-width-active", button.dataset.titleWidth === titleWidth);
        button.classList.toggle("active", button.dataset.titleWidth === titleWidth);
      }});
    }}

    function shownColumns() {{
      return columns.filter(([key]) => fixedKeys.has(key) || !hidden.has(key));
    }}

    function cell(value) {{
      if (!value) return '<span class="empty"></span>';
      return String(value).replace(/[&<>"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch]));
    }}

    function formatAuthors(row) {{
      if (!row.authors) return '<span class="empty"></span>';
      const normalizeAuthorName = name => String(name).replace(/^(Dr\\.?|Professor|Prof\\.?)\\s+/i, "").trim();
      const corresponding = new Set((row.correspondingAuthors || []).map(name => normalizeAuthorName(name)));
      return String(row.authors).split("；").map(name => {{
        const clean = name.trim();
        const escaped = cell(clean);
        return corresponding.has(normalizeAuthorName(clean)) ? `<span class="corresponding-author">${{escaped}}</span>` : escaped;
      }}).join("；");
    }}

    function similarityClass(value) {{
      const match = String(value || "").match(/\\d+(?:\\.\\d+)?/);
      if (!match) return "";
      const score = Number(match[0]);
      if (!Number.isFinite(score)) return "";
      if (score < 10) return "similarity-low";
      if (score <= 15) return "similarity-mid";
      return "similarity-high";
    }}

    function sortedRows() {{
      const data = [...rows];
      if (currentSort === "impact") {{
        data.sort((a, b) => (b.impactSort - a.impactSort) || (a.statusOrder - b.statusOrder) || a.title.localeCompare(b.title, "zh-CN"));
      }} else if (currentSort === "updated") {{
        data.sort((a, b) => String(b.updatedAt).localeCompare(String(a.updatedAt)) || (a.statusOrder - b.statusOrder));
      }} else {{
        data.sort((a, b) => (a.statusOrder - b.statusOrder) || a.title.localeCompare(b.title, "zh-CN"));
      }}
      return data;
    }}

    function renderToggles() {{
      const el = document.getElementById("columnToggles");
      el.innerHTML = columns.filter(([key]) => !fixedKeys.has(key)).map(([key, label]) => `
        <label><input type="checkbox" data-column="${{key}}" ${{hidden.has(key) ? "" : "checked"}}> ${{label}}</label>
      `).join("");
      el.querySelectorAll("input").forEach(input => {{
        input.addEventListener("change", () => {{
          if (input.checked) hidden.delete(input.dataset.column);
          else hidden.add(input.dataset.column);
          localStorage.setItem("paperStatusHiddenColumns", JSON.stringify([...hidden]));
          renderTable();
        }});
      }});
    }}

    function showAllColumns() {{
      hidden.clear();
      localStorage.setItem("paperStatusHiddenColumns", JSON.stringify([]));
      renderToggles();
      renderTable();
    }}

    function renderTable() {{
      const cols = shownColumns();
      document.getElementById("tableHead").innerHTML = cols.map(([key, label]) => `<th data-key="${{key}}">${{label}}</th>`).join("");
      document.getElementById("tableBody").innerHTML = sortedRows().map(row => {{
        return `<tr style="background-color:${{row.bg}};">${{cols.map(([key]) => {{
          const value = key === "status" ? row.statusDot : row[key];
          const htmlValue = key === "authors" ? formatAuthors(row) : cell(value);
          const extraClass = key === "similarity" ? similarityClass(value) : "";
          const classAttr = extraClass ? ` class="${{extraClass}}"` : "";
          return `<td data-key="${{key}}"${{classAttr}} style="background-color:${{row.bg}};">${{htmlValue}}</td>`;
        }}).join("")}}</tr>`;
      }}).join("");
    }}

    document.querySelectorAll(".controls button[data-sort]").forEach(button => {{
      button.addEventListener("click", () => {{
        currentSort = button.dataset.sort;
        document.querySelectorAll(".controls button[data-sort]").forEach(b => b.classList.toggle("active", b === button));
        renderTable();
      }});
    }});
    document.querySelectorAll(".controls button[data-title-width]").forEach(button => {{
      button.addEventListener("click", () => {{
        titleWidth = button.dataset.titleWidth;
        localStorage.setItem("paperStatusTitleWidth", titleWidth);
        applyTitleWidth();
      }});
    }});
    document.getElementById("showAllColumns").addEventListener("click", showAllColumns);
    applyTitleWidth();
    renderToggles();
    renderTable();
  </script>
</body>
</html>
"""


def main():
    rows = enrich_rows(parse_rows())
    (ROOT / "status_data.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "index.html").write_text(render(rows), encoding="utf-8")
    print(f"generated {len(rows)} rows")


if __name__ == "__main__":
    main()
