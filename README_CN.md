# Codex 动漫圣地巡礼规划 Skills

[English README](README.md)

这是一个用于 Codex 的动漫圣地巡礼规划 Skill 集合。

本项目可以根据用户输入的动漫名称，通过 Bangumi 搜索并确认作品，再使用确认后的 Bangumi ID 从 Anitabi 获取圣地巡礼点位，并结合用户的出行日期、可用时间、起点位置、终点偏好、最长可接受步行距离、天气信息、地图链接和指定输出语言，生成可编辑的 HTML 圣地巡礼计划表。

本项目支持两种使用方式：

* **一站式 Skill**：使用一个 Skill 完成完整的圣地巡礼规划流程。
* **分阶段 Skill 链**：按步骤完成作品搜索、出行信息收集、点位获取、路线规划、地点信息补充和 HTML 行程表生成。

## 在线示例

可以通过 GitHub Pages 查看生成后的路线示例：

* [Route A：全量点位路线](https://icecream-lcx.github.io/anime-pilgrimage-skills/pilgrimage_route_A.html)
* [Route B：时间适配路线](https://icecream-lcx.github.io/anime-pilgrimage-skills/pilgrimage_route_B.html)

Route A 覆盖所有具有有效坐标的 Anitabi 点位；Route B 则根据用户可用出行时间生成时间适配路线。

示例页面为生成后的 HTML 结果。天气、路线耗时、营业时间、价格和交通信息仅供参考，实际出行前请再次确认。

## 功能特点

* 通过 Bangumi 按作品名称或关键词搜索动漫作品。

* 使用确认后的 Bangumi ID 从 Anitabi 获取圣地巡礼点位。

* 生成可编辑的 HTML 圣地巡礼路线表。

* 支持用户指定输出语言，例如中文、英文、日文、韩文或双语输出。

* 在没有 Google Maps API Key 的情况下，支持 Google Maps URL-only 降级模式。

* 支持询问用户单段最长可接受步行距离。

* 支持生成 Google Maps 单点链接和路线链接。

* 使用纯坐标形式生成 Google Maps 点位链接，降低地点搜索失败的概率。

* 支持终点默认规则：用户未指定终点时，默认最终返回出发地。

* 保留两类路线概念：

  * **Route A：全量点位路线** —— 覆盖所有具有有效坐标的 Anitabi 点位。
  * **Route B：时间适配路线** —— 根据用户可用时间筛选更适合实际出行的点位。

* 支持多天行程规划：

  * Route A 始终保留为全量点位路线。
  * Route B 可以按天拆分，例如 Route B Day 1、Route B Day 2。

* Route B 支持交互式编辑：

  * 将未纳入当前路线的 Anitabi 点位重新加入路线。
  * 拖动点位调整路线顺序。
  * 删除不想去的点位。
  * 重新生成 Google Maps 路线链接。
  * 重新估算到达和离开时间。

* 保持 `shared/` 目录作为稳定源码目录。

* 临时辅助脚本应生成到 `_codex_generated/` 或 `_scratch/`，而不是写入 `shared/`。

## 项目结构

```text
anime-pilgrimage-skills/
├── README.md
├── README_CN.md
├── LICENSE
├── .gitignore
├── .gitattributes
├── .agents/
│   └── skills/
│       ├── anime-pilgrimage-all-in-one/
│       ├── pilgrimage-00-orchestrator/
│       ├── pilgrimage-01-anime-search-confirm/
│       ├── pilgrimage-02-trip-profile/
│       ├── pilgrimage-03-anitabi-points/
│       ├── pilgrimage-04-route-weather/
│       ├── pilgrimage-05-place-hours-prices/
│       ├── pilgrimage-06-html-plan/
│       ├── pilgrimage-constraints/
│       └── shared/
├── examples/
└── docs/
```

主要目录说明：

* `anime-pilgrimage-all-in-one/`：一站式动漫圣地巡礼规划 Skill。
* `pilgrimage-00-orchestrator/`：分阶段流程总控 Skill。
* `pilgrimage-01-anime-search-confirm/`：动漫作品搜索与确认。
* `pilgrimage-02-trip-profile/`：出行信息收集。
* `pilgrimage-03-anitabi-points/`：Anitabi 巡礼点位获取。
* `pilgrimage-04-route-weather/`：路线与天气规划。
* `pilgrimage-05-place-hours-prices/`：地点营业时间与价格信息补充。
* `pilgrimage-06-html-plan/`：可编辑 HTML 行程表生成。
* `pilgrimage-constraints/`：统一约束规则，包括路线结构、多天行程、多语言输出、终点默认规则和文件生成策略。
* `shared/`：公共脚本和输出数据协议。
* `examples/`：整理后的示例输出。
* `docs/`：GitHub Pages 示例页面。

## 安装方式

将 Skill 文件夹复制到 Codex 支持的 Skill 目录中。

项目级安装：

```text
your-project/
└── .agents/
    └── skills/
```

全局级安装：

```text
$HOME/.agents/skills/
```

请保持以下目录都位于 `.agents/skills/` 下：

```text
anime-pilgrimage-all-in-one/
pilgrimage-00-orchestrator/
pilgrimage-01-anime-search-confirm/
pilgrimage-02-trip-profile/
pilgrimage-03-anitabi-points/
pilgrimage-04-route-weather/
pilgrimage-05-place-hours-prices/
pilgrimage-06-html-plan/
pilgrimage-constraints/
shared/
```

这些 Skills 需要共同使用统一约束文件、公共脚本和输出数据协议。

## 使用方法

### 一站式 Skill

```text
$anime-pilgrimage-all-in-one 帮我规划《孤独摇滚！》下北泽圣地巡礼，日期是 2026-07-10，上午 9 点到晚上 7 点，从下北泽站出发，回到下北泽站。
```

若用户没有提供终点，则默认最终返回出发地。

示例：

```text
$anime-pilgrimage-all-in-one 帮我规划《冰菓》两天圣地巡礼，日期是 2026-06-19 和 2026-06-20，从高山站出发，早上 9 点到晚上 18 点。
```

在这个示例中，用户没有指定终点，因此路线应默认返回出发地。

### 指定输出语言

路线表可以根据用户需求生成不同语言版本。

示例：

```text
$anime-pilgrimage-all-in-one Generate a two-day Hyouka pilgrimage route in English.
```

```text
$anime-pilgrimage-all-in-one 用日文生成《冰菓》的两天圣地巡礼路线。
```

```text
$anime-pilgrimage-all-in-one 帮我生成《孤独摇滚！》中英双语圣地巡礼路线。
```

若用户没有明确指定输出语言，则根据用户最近一次请求的主要语言自动推断。

## 分阶段 Skill 链

从总控 Skill 开始：

```text
$pilgrimage-00-orchestrator
```

随后 Codex 将按以下阶段执行：

1. `$pilgrimage-01-anime-search-confirm`
2. `$pilgrimage-02-trip-profile`
3. `$pilgrimage-03-anitabi-points`
4. `$pilgrimage-04-route-weather`
5. `$pilgrimage-05-place-hours-prices`
6. `$pilgrimage-06-html-plan`

每个阶段应输出符合以下文件中定义的数据协议：

```text
.agents/skills/shared/references/output-contracts.md
```

统一约束规则定义在：

```text
.agents/skills/pilgrimage-constraints/references/pilgrimage-constraints.md
```

所有圣地巡礼相关 Skill 都应遵守这些约束。

## 可选环境变量

* `BANGUMI_ACCESS_TOKEN`：可选，Bangumi 访问令牌。
* `BANGUMI_USER_AGENT`：推荐配置。例如：`AnimePilgrimageSkill/0.1 (contact@example.com)`。
* `GOOGLE_MAPS_API_KEY`：可选。配置后可使用 Google Routes API 和 Places API。
* `OSRM_BASE_URL`：可选。默认可使用 `https://router.project-osrm.org`。当点位存在坐标时，可用于开放地图路线距离粗略估算。

当未配置 `GOOGLE_MAPS_API_KEY` 时，项目会使用 Google Maps URL-only 模式。在该模式下，项目可以生成 Google Maps 路线链接和地点链接，但不能自动获取 Google 的实时路线耗时、营业时间、评分或价格等级。

## 路线概念

### Route A：全量点位路线

Route A 包含所有具有有效坐标的 Anitabi 巡礼点位。

规则：

* Route A 必须始终存在。
* Route A 覆盖所有有效 Anitabi 坐标点。
* Route A 不根据用户可用时间进行筛选。
* 多天行程中也必须保留 Route A。
* 若点位过多导致单个 Google Maps 链接不稳定，则自动拆分为多个连续路线链接。

Route A 适合查看全部巡礼点位的空间分布。用户可以在 HTML 页面中删除不想去的点位，并根据剩余点位重新生成路线链接。

推荐输出文件名：

```text
pilgrimage_route_A.html
```

### Route B：时间适配路线

Route B 会根据用户可用时间、起点、终点、最长可接受步行距离、预计停留时间和天气信息，筛选更适合实际出行的点位。

Route B HTML 页面支持：

* 将未纳入当前路线的 Anitabi 点位重新加入路线。
* 拖动点位调整路线顺序。
* 删除不想去的点位。
* 重新生成 Google Maps 路线链接。
* 重新估算到达和离开时间。

对于多天行程，Route B 可以拆分为每天一个页面。

推荐输出文件名：

```text
pilgrimage_route_B_day_1.html
pilgrimage_route_B_day_2.html
pilgrimage_route_B_day_3.html
```

为了兼容单日路线，也可以使用：

```text
pilgrimage_route_B.html
```

## 多天行程规则

对于多天行程，不能用每日 Route B 页面替代 Route A。

两天行程的期望输出为：

```text
pilgrimage_route_A.html
pilgrimage_route_B_day_1.html
pilgrimage_route_B_day_2.html
```

Route A 应覆盖整个行程中的所有有效 Anitabi 点位。

Route B 可以按天拆分，并根据每天可用时间筛选适合当天完成的点位。

Route B 中未被纳入的点位应保留并显示在 HTML 页面中，方便用户手动加入路线。

## 终点默认规则

若用户没有指定终点，则默认终点为起点。

规则：

* 用户提供终点时，使用用户指定的终点。
* 用户未提供终点时，将起点复制为终点。
* Route A 和 Route B 都应遵守该规则。
* 多天行程中，若用户没有提供每天的终点，则每天默认返回当天出发点或酒店。

推荐 JSON 字段：

```json
{
  "start_location": {
    "name": "",
    "address": "",
    "lat": null,
    "lng": null
  },
  "end_location": {
    "name": "",
    "address": "",
    "lat": null,
    "lng": null
  },
  "end_location_policy": "user_specified|return_to_start"
}
```

## 语言输出规则

路线表的输出语言应跟随用户需求。

规则：

* 用户明确指定语言时，使用用户指定语言。
* 用户要求双语输出时，生成双语标签和说明。
* 用户没有指定语言时，根据用户最近一次请求的主要语言进行推断。
* 专有名词和技术术语在必要时可以保留原文。

推荐 JSON 字段：

```json
{
  "output_language": {
    "primary": "zh-CN",
    "secondary": null,
    "mode": "single",
    "source": "user_requested|inferred|default"
  }
}
```

支持示例：

```text
zh-CN        简体中文
zh-TW        繁體中文
en           英文
ja           日文
ko           韩文
fr           法文
es           西班牙文
bilingual    双语输出，例如 zh-CN + en
```

所选语言应影响：

* HTML 页面标题。
* 路线名称。
* 路线提醒。
* 天气摘要。
* 人工确认说明。
* 按钮文字。
* 表格标题。
* 地点备注。
* 交通说明。
* 价格与营业时间说明。
* Route A / Route B 说明。
* 未纳入点位区域。
* 添加、删除、拖动、重建路线、重新计算时间等操作说明。

不要在 HTML 中直接显示内部枚举值，应根据输出语言转换为用户可读文本。

## Google Maps URL-only 模式

当未配置 `GOOGLE_MAPS_API_KEY` 时，项目使用 Google Maps URL-only 模式。

在该模式下，项目可以：

* 使用坐标生成点位链接。
* 使用起点、终点和途经点生成路线链接。
* 将过长路线拆分为多个路线链接。
* 提供需要人工确认的提示。

在该模式下，项目不能自动获取：

* Google 实时路线耗时。
* 公共交通班次。
* 营业时间。
* 评分。
* 价格等级。
* 门票价格。
* 餐厅人均价格。

这些具有时效性的信息应在实际出行前人工确认。

## 时间重新估算

在 Google Maps URL-only 模式下，本地 HTML 不能直接读取 Google Maps 的实时路线耗时。

当用户在 Route B 中调整顺序、添加点位或删除点位时，生成的 HTML 可以：

1. 重新生成 Google Maps 路线链接。
2. 在存在坐标时尝试使用 OSRM / OpenStreetMap 进行距离估算。
3. 若没有可用路线数据，则使用基于距离的粗略估算。
4. 将公共交通耗时标注为需要人工确认。

重新估算的时间仅作为行程规划参考。

## 文件生成规则

`shared/` 目录是稳定源码目录。

在正常生成行程时，Codex 不应在以下目录中创建临时脚本、生成型辅助脚本、实验文件、调试文件或一次性代码：

```text
.agents/skills/shared/scripts/
.agents/skills/shared/references/
```

正常执行时允许写入的位置：

```text
output/
_codex_generated/
_scratch/
tmp/
temp/
```

规则：

* 优先使用 `shared/scripts/` 中已有脚本。
* 临时辅助代码应写入 `_codex_generated/`。
* 临时笔记或实验内容应写入 `_scratch/`。
* 运行生成的行程结果应写入 `output/`。
* 整理后的公开示例可以写入 `examples/`。
* 除非用户明确要求修改 Skill 源码，否则不要修改 `shared/`。

## GitHub 安全输出规则

生成型临时文件夹不应上传到 GitHub。

推荐 `.gitignore` 条目：

```gitignore
output/
_codex_generated/
_scratch/
tmp/
temp/
.env
.env.*
*.key
__pycache__/
*.pyc
*.pyo
.venv/
venv/
env/
*.tmp
*.log
```

`examples/` 文件夹可以用于提交整理后的公开示例。

不要提交私人酒店地址、API Key、Token、`.env` 文件、临时调试脚本或原始个人行程信息。

## 示例

`examples/` 文件夹提供了 *Hyouka* 的圣地巡礼规划示例，包括：

* Route A 全量点位路线。
* Route B 时间适配路线。
* 可编辑 HTML 行程表。
* Anitabi 点位 JSON。
* 路线规划 JSON。

示例中的天气、营业时间、交通耗时和价格信息仅用于展示格式。实际出行前请重新确认所有具有时效性的信息。

## 注意事项

* 请使用官方 API，并遵守各数据源的使用条款。
* Anitabi 点位截图可能包含 `origin` 和 `originURL`，展示拍照参考时应尽量保留来源信息。
* 营业时间、公共交通路线、价格、评分和天气都具有时效性。
* 实际出行前应再次确认天气、交通、营业时间、门票价格和餐厅信息。
* 未配置 Google Maps API Key 时，项目无法自动获取精确的 Google 路线耗时、营业时间、评分和价格等级。
* 生成的路线表仅作为行程规划参考，不保证实际可行性或出行安全。

## 开源许可

推荐使用 MIT License 进行简单开源发布。
