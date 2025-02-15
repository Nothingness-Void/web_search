from typing import Dict, Any, List
import asyncio
from framework.plugin_manager.plugin import Plugin
from framework.logger import get_logger
from .config import WebSearchConfig
from .web_searcher import WebSearcher
from dataclasses import dataclass
from framework.workflow.core.block import BlockRegistry
from .blocks import WebSearchBlock
from .blocks import AppendSystemPromptBlock
from framework.ioc.inject import Inject
from framework.ioc.container import DependencyContainer
from framework.workflow.core.workflow.builder import WorkflowBuilder
from framework.workflow.core.workflow.registry import WorkflowRegistry
logger = get_logger("WebSearch")
import os
import os
class WebSearchPlugin(Plugin):
    def __init__(self, block_registry: BlockRegistry , container: DependencyContainer):
        super().__init__()
        self.web_search_config = WebSearchConfig()
        self.searcher = None
        self.block_registry = block_registry
        self.workflow_registry = container.resolve(WorkflowRegistry)
        self.container=container
    def on_load(self):
        logger.info("WebSearchPlugin loading")

        # 注册Block
        try:
            self.block_registry.register("web_search", "search", WebSearchBlock)
        except Exception as e:
            logger.warning(f"WebSearchPlugin failed: {e}")
        try:
            self.block_registry.register("append_systemPrompt", "internal", AppendSystemPromptBlock)
        except Exception as e:
            logger.warning(f"WebSearchPlugin failed: {e}")
        # 获取当前文件的绝对路径
        current_file = os.path.abspath(__file__)

        # 获取当前文件所在目录
        current_dir = os.path.dirname(current_file)

        # 获取上级目录
        parent_dir = os.path.dirname(current_dir)

        # 构建 example 目录的路径
        example_dir = os.path.join(parent_dir, 'example')
        # 获取 example 目录下所有的 yaml 文件
        yaml_files = [f for f in os.listdir(example_dir) if f.endswith('.yaml') or f.endswith('.yml')]

        for yaml in yaml_files:
            logger.info(os.path.join(example_dir, yaml))
            self.workflow_registry.register("search", os.path.splitext(yaml)[0], WorkflowBuilder.load_from_yaml(os.path.join(example_dir, yaml), self.container))
        @dataclass
        class WebSearchEvent:
            """Web搜索事件"""
            query: str

        async def handle_web_search(event: WebSearchEvent):
            """处理web搜索事件"""
            if not self.searcher:
                await self._initialize_searcher()
            return await self.searcher.search(
                event.query,
                max_results=self.web_search_config.max_results,
                timeout=self.web_search_config.timeout,
                fetch_content=self.web_search_config.fetch_content
            )
        try:
            self.event_bus.register(WebSearchEvent, handle_web_search)
        except Exception as e:
            logger.warning(f"WebSearchPlugin failed: {e}")

    def on_start(self):
        logger.info("WebSearchPlugin started")

    def on_stop(self):
        if self.searcher:
            asyncio.create_task(self.searcher.close())

        logger.info("WebSearchPlugin stopped")

    async def _initialize_searcher(self):
        """初始化搜索器"""
        if self.searcher is None:
            self.searcher = await WebSearcher.create()

