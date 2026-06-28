"""技能加载器 - 加载 SKILL.md 文件供 DeepAgents 使用"""

from pathlib import Path
from utils.logger import logger


class SkillsLoader:
    """加载 skills 目录下的所有 SKILL.md 文件"""

    def __init__(self, skills_dir: str = None):
        if skills_dir is None:
            self.skills_dir = Path(__file__).parent / "skills"
        else:
            self.skills_dir = Path(skills_dir)

    def load_all(self) -> list[str]:
        """加载所有技能文件，返回技能内容列表"""
        skills = []
        if not self.skills_dir.exists():
            logger.warning(f"技能目录不存在: {self.skills_dir}")
            return skills

        for md_file in sorted(self.skills_dir.glob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                skills.append(content)
                logger.info(f"已加载技能: {md_file.name}")
            except Exception as e:
                logger.error(f"加载技能文件失败 {md_file}: {e}")

        logger.info(f"共加载 {len(skills)} 个技能")
        return skills

    def load_as_system_prompt(self) -> str:
        """将所有技能合并为系统提示词"""
        skills = self.load_all()
        if not skills:
            return ""

        prompt = "你可以使用以下技能，请根据用户问题自主判断是否使用：\n\n"
        for i, skill in enumerate(skills, 1):
            prompt += f"---\n{skill}\n\n"
        return prompt
