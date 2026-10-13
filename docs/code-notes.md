# 代码要点

本文收录**少量经过审查的原始代码节选**，用来说明几个「只有真跑过才知道」的处理。

> **收录标准**：节选不得包含任何客户标识（系统名、地址、账号、料号、单价、页面内元素 ID）。
> 本文正文中的框架类名属于 ExtJS 公开知识，可以保留。
> 完整源码**未**公开——原工具服务于具体客户的系统，全量发布不合适。
> 分析与验证过程见 [analysis-method.md](analysis-method.md)。

---

## 一、ExtJS 的展开图标是「切换」而不是「展开」

这是整个采集器里最值得讲的一个坑。

**现象**：树形菜单里点父节点的展开图标，有时子节点反而**消失**了，后续点击全部超时。

**原因**：ExtJS 的 `expander` 图标是**切换（toggle）**语义。如果父节点本来就处于展开状态，再点一下就会把它**收起**。

**常见但错误的做法**：以「点击有没有抛异常」作为成功判据。

```python
# ✗ 这样写会在"父节点已展开"时把树点收起来，而且自己不知道
node.click()
return True
```

**实际采用的做法**：每点一次都**回头确认子节点是否真的出现**——检查的是后置条件，不是点击动作本身。

```python
def ensure_child_visible(page, parent: str, child: str, tries: int = 4) -> bool:
    """确保父节点已展开且子节点可见。

    ExtJS 的 expander 是「切换」而非「展开」：若父节点本来就处于展开态，
    点一下反而会收起，导致子节点消失、后续点击超时。这里每点一次都回头
    确认子节点是否真的出现，没出现就再点一次（相当于把状态拨回来）。
    """
    for _ in range(tries):
        try:
            node = page.locator(f'span.x-tree-node-text:text-is("{child}")').first
            node.wait_for(state="visible", timeout=3000)
            return True
        except Exception:
            pass
        try:
            row = page.locator(f'tr:has(span.x-tree-node-text:text-is("{parent}"))').first
            row.wait_for(state="visible", timeout=6000)
            row.locator('img.x-tree-expander').first.click(force=True, timeout=5000)
            page.wait_for_timeout(2500)
        except Exception:
            page.wait_for_timeout(1500)
    return False
```

几点值得注意：

| 做法 | 为什么 |
|---|---|
| 先查子节点可见 → 直接返回 | 已经是想要的状态就不动，**从根上避免误收起** |
| 失败后重新点 expander | 点一次等于把状态「拨回来」，而不是记录一个失败的布尔值 |
| `tries=4` 有界重试 | 不无限循环；仍然失败就返回 `False`，由上层决定怎么办 |
| 返回 `bool` 而非抛异常 | 调用方可以给出业务化提示（「展开菜单失败」），而不是抛栈给用户看 |

**通用教训**：自动化一个**有状态的界面**时，「动作是否执行成功」和「界面是否达到期望状态」是两件事。
判据要取后者。这条不限于 ExtJS——任何可切换的控件（折叠面板、开关、多选）都适用。

---

## 二、同名按钮只点可见的那个

ERP 的工具栏上，「查询」这类按钮**同时存在于多处**：单据编辑页有一个，列表页也有一个。
按文本选择器抓会抓到多个，点错那个就什么也不会发生。

实际处理：按候选顺序逐个尝试，**只点当前可见的**。

```python
def click_ext_button(page, text: str, desc: str, timeout=10000):
    """点击 ExtJS 工具栏按钮（非原生 button）：同名按钮可能存在多个
    （如单据编辑页与列表页都有「查询」），只点击可见的那个。"""
    selectors = [
        f'span.x-btn-inner:text-is("{text}")',
        f'.x-btn:has(span.x-btn-inner:text-is("{text}"))',
        f'a:has-text("{text}")',
        f'button:has-text("{text}")',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel)
            loc.first.wait_for(state="attached", timeout=timeout)
            for i in range(min(loc.count(), 8)):
                cand = loc.nth(i)
                if cand.is_visible():
                    cand.click()
                    log(f"已点击: {desc}")
                    return True
        except Exception:
            continue
    log(f"点击 [{desc}] 失败: 所有候选均不可见或未找到")
```

设计要点：

- **多套选择器依次降级**：ExtJS 不同版本/主题的 DOM 结构会变，写死一套很容易在升级后失效
- **只点可见的**：`is_visible()` 是关键判据，不是「找得到就点」
- **有上限**（`min(count, 8)`）：防止某个选择器意外匹配到上百个元素时空转
- **失败返回 `None` 并记日志**：调用方能看到「点了但没成」，而不是静默继续

---

## 三、为什么这两个函数值得单列

它们代表了这类工作的**真实难点**：不是「调用 Playwright API」，而是——

1. **理解被操作界面的状态语义**（toggle 还是 set）
2. **为不确定性设计判据**（后置条件优于动作返回）
3. **在会变的外部上做兼容**（多套选择器、降级）

这些都不是从文档里读来的，是被真实的失败逼出来的。

---

## 四、关于完整源码

本仓库**不包含**完整源码。原因：

- 原工具对接的是**具体客户的 ERP 系统**，源码中包含该系统与相关业务实体的标识
- 完整发布需要客户/雇主层面的确认，超出本仓库的范围

本文的节选经过逐行审查，确认不含此类标识后才收录。

如果你需要评估更完整的实现，可以在面试中提供脱敏后的局部代码讲解。
