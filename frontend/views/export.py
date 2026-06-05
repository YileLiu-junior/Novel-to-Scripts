"""
export.py
剧本导出页面：将项目数据导出为结构化 YAML 格式剧本。
支持预览 YAML、下载 YAML 文件、下载 Schema 文档。
"""

import streamlit as st
from frontend.utils import exporter


def render(project: dict):
    """
    渲染剧本导出页面。
    :param project: 当前项目字典
    """
    st.header("📋 剧本导出")
    st.caption("将当前项目中的原文、人物、场景、场次整理为结构化 YAML 剧本文件，便于后续编辑、校验和二次创作。")
    st.markdown("---")

    acts_list = project.get("acts", []) or []

    # 如果没有场次，显示提示
    if not acts_list:
        st.warning('当前项目暂无场次，请先在"场次"页面添加场次。')
        st.info("以下将导出基础项目结构（不含场次数据）。")

    st.markdown("---")

    # 生成 YAML
    yaml_text = exporter.generate_yaml(project)

    # YAML 预览区域
    st.subheader("📄 YAML 预览")
    st.code(yaml_text, language="yaml")

    st.markdown("---")

    # 下载按钮区域
    st.subheader("📥 下载")

    col1, col2 = st.columns(2)

    with col1:
        # 下载剧本 YAML
        yaml_filename = exporter.get_download_filename(project)
        st.download_button(
            label="📥 下载剧本 YAML",
            data=yaml_text.encode("utf-8"),
            file_name=yaml_filename,
            mime="text/yaml",
            use_container_width=True,
        )

    with col2:
        # 下载 YAML Schema 文档
        schema_doc_path = _get_schema_doc_path()
        if schema_doc_path:
            with open(schema_doc_path, "r", encoding="utf-8") as f:
                schema_doc_content = f.read()
            st.download_button(
                label="📄 下载 YAML Schema 文档",
                data=schema_doc_content.encode("utf-8"),
                file_name="yaml_schema.md",
                mime="text/markdown",
                use_container_width=True,
            )
        else:
            st.warning("Schema 文档文件未找到。")


def _get_schema_doc_path() -> str | None:
    """
    获取 YAML Schema 文档的路径。
    :return: 文件绝对路径，不存在则返回 None
    """
    import os
    doc_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "docs", "yaml_schema.md"
    )
    if os.path.exists(doc_path):
        return doc_path
    return None
