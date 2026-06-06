# 人物管理卡片布局修复报告

## 1. 修改文件列表

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/views/characters.py` | **重写** | 恢复卡片式网格布局，简化卡片内容，保留所有功能 |

## 2. 布局恢复

使用 `st.columns(4)` 实现每行 4 张卡片的网格布局：

```python
_CARDS_PER_ROW = 4

for i in range(0, len(card_chars), _CARDS_PER_ROW):
    row_chars = card_chars[i:i + _CARDS_PER_ROW]
    cols = st.columns(_CARDS_PER_ROW)
    for idx, char in enumerate(row_chars):
        with cols[idx]:
            _render_single_character_card(char, ...)
```

- 每个人物在独立的 column 中渲染
- 卡片使用 `st.container(border=True)` 包裹，有统一边框
- 添加人物卡片同样使用 column 布局，与人物卡片风格一致

## 3. 头像下方显示修改

### 已移除的内容

头像下方不再显示：
- `别名：xxx`
- `风格：xxx`（voice_profile 的 rhythm + diction）
- 长描述文本

### 当前显示内容

头像下方只显示：
1. **人物名称**（单行，省略号截断，15px 粗体，白色）
2. **叙事角色**（可选，11px，灰色，单行省略）
3. **描述摘要**（可选，最多两行，11px，截断 40 字）

所有文本均使用 CSS 防止溢出：
```css
white-space: nowrap;
overflow: hidden;
text-overflow: ellipsis;
max-width: 100%;
```

## 4. 编辑/删除/添加功能

### 编辑
- 点击卡片底部"编辑"按钮 → 进入全宽编辑表单
- 编辑表单字段：name, aliases, narrative_role, voice_profile.rhythm, voice_profile.diction, description
- 保存后调用 `PUT /frontend-data`，成功后刷新页面

### 删除
- 点击卡片底部"删除"按钮 → 显示二次确认（确认删除 / 取消）
- 确认后调用保存接口，从列表移除该人物

### 添加
- "添加人物"卡片与人物卡片风格一致（圆形 + 号图标 + "添加人物"文字）
- 点击"点击添加"按钮 → 在卡片下方展开添加表单
- 添加表单字段与编辑表单完全一致
- 添加成功后新卡片立即出现在网格中

所有功能均通过 `frontend_data` API 持久化到后端，刷新后数据保留。

## 5. 人物关系区域

人物关系区域仍然在页面底部：
- 使用 `st.markdown("---")` 分隔线分隔
- 使用 `st.subheader("人物关系")` 标题
- 实时从当前 `characters_list` 构建 `ID → name` 映射
- 使用 `st.dataframe` 展示关系表格
- 修改人物名称后，关系区域同步显示新名称

## 6. 验收结果

| 序号 | 验收标准 | 状态 |
|------|----------|------|
| 1 | 人物管理页面恢复为卡片式布局 | ✅ 使用 `st.columns(4)` 网格布局 |
| 2 | 每个人物是一张独立卡片 | ✅ `st.container(border=True)` 包裹 |
| 3 | 人物头像下方只显示人物名称 | ✅ 已移除别名、风格等长文本 |
| 4 | 不再显示"别名：xxx"和"风格：xxx"在头像下方 | ✅ 完全移除 |
| 5 | 别名、风格等长内容不会造成页面混乱 | ✅ 仅在编辑表单中显示 |
| 6 | 编辑、删除按钮仍然可用 | ✅ 保留完整功能 |
| 7 | 添加人物仍然是卡片式入口 | ✅ 添加卡片与人物卡片风格一致 |
| 8 | 人物关系仍然在页面底部 | ✅ 使用分隔线和子标题展示 |
| 9 | 卡片内容不会溢出 | ✅ 所有文本均有 `ellipsis` 截断 |
| 10 | 页面刷新后数据仍然正常显示 | ✅ 通过 `frontend_data` API 持久化 |
