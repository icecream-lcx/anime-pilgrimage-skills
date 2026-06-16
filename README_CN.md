# Codex 动漫圣地巡礼规划 Skills

[English README](README.md)

这是一个用于 Codex 的动漫圣地巡礼规划 Skill 集合。

本项目可以根据用户输入的动漫名称，通过 Bangumi 搜索并确认作品，再使用确认后的 Bangumi ID 从 Anitabi 获取圣地巡礼点位，并结合用户的出行日期、可用时间、起点位置、最长可接受步行距离、天气信息和地图链接，生成可编辑的 HTML 圣地巡礼计划表。

本项目支持两种使用方式：

* **一站式 Skill**：调用一个 Skill 完成完整巡礼规划。
* **分阶段 Skill 链**：按作品搜索、出行信息收集、点位获取、路线规划、HTML 生成等步骤逐步执行。

## 主要功能

* 根据动漫名称或关键词搜索 Bangumi 作品信息。
* 根据 Bangumi ID 获取 Anitabi 圣地巡礼点位。
* 支持无 Google Maps API 的 URL-only 降级模式。
* 支持用户设置单段最长可接受步行距离。
* 自动生成 Google Maps 点位链接和路线链接。
* 生成两种路线方案：

  * **Route A：全量点位路线**，覆盖所有具有有效坐标的 Anitabi 点位。
  * **Route B：时间适配路线**，根据用户时间筛选较适合当天完成的点位。
* Route B 支持交互式编辑：

  * 添加未纳入路线的 Anitabi 点位。
  * 拖动调整点位顺序。
  * 删除不想去的点位。
  * 重新生成路线链接。
  * 重新适配到达和离开时间。
* 生成可编辑、可打印、可另存为 PDF 的 HTML 巡礼计划表。

## 项目结构

```text
anime-pilgrimage-skills/
├── README.md
├── README_CN.md
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
│       └── shared/
└── examples/
    └── hyouka-demo/
```

主要目录说明：

* `anime-pilgrimage-all-in-one/`：一站式完整巡礼规划 Skill。
* `pilgrimage-00-orchestrator/`：分阶段流程总控 Skill。
* `pilgrimage-01-anime-search-confirm/`：动漫作品搜索与确认。
* `pilgrimage-02-trip-profile/`：出行信息收集。
* `pilgrimage-03-anitabi-points/`：Anitabi 巡礼点位获取。
* `pilgrimage-04-route-weather/`：路线与天气规划。
* `pilgrimage-05-place-hours-prices/`：地点营业时间与价格补充。
* `pilgrimage-06-html-plan/`：可编辑 HTML 巡礼计划表生成。
* `shared/`：公共脚本和输出格式约定。

## 安装

将 Skill 文件夹复制到 Codex 支持的 Skill 目录中。

仓库级安装：

```text
your-project/
└── .agents/
    └── skills/
```

全局级安装：

```text
$HOME/.agents/skills/
```

请确保 `shared/` 文件夹和其他 Skill 文件夹位于同一级目录下，因为各个 Skill 需要使用其中的辅助脚本和输出格式约定。

## 使用方法

### 一站式调用

```text
$anime-pilgrimage-all-in-one 帮我规划《孤独摇滚！》下北泽圣地巡礼，日期是 2026-07-10，上午 9 点到晚上 7 点，从下北泽站出发。
```

### 分阶段调用

先调用：

```text
$pilgrimage-00-orchestrator
```

然后 Codex 会按以下阶段执行：

1. `$pilgrimage-01-anime-search-confirm`
2. `$pilgrimage-02-trip-profile`
3. `$pilgrimage-03-anitabi-points`
4. `$pilgrimage-04-route-weather`
5. `$pilgrimage-05-place-hours-prices`
6. `$pilgrimage-06-html-plan`

每个阶段都应按照以下文件中定义的 JSON 格式输出结果：

```text
shared/references/output-contracts.md
```

这样下一个阶段就可以继续读取和使用上一个阶段的结果。

## 可选环境变量

* `BANGUMI_ACCESS_TOKEN`：可选的 Bangumi 访问令牌。
* `BANGUMI_USER_AGENT`：推荐配置。例如：`MiriaGoPlanningSkill/0.1 (contact@example.com)`。
* `GOOGLE_MAPS_API_KEY`：可选。如果配置该变量，Skill 可以使用 Google Routes API 和 Places API。
* `OSRM_BASE_URL`：可选。默认可使用 `https://router.project-osrm.org`。当已有坐标信息时，可用于基于开放地图数据粗略估算距离。

如果没有配置 `GOOGLE_MAPS_API_KEY`，Skill 会进入 Google Maps URL-only 模式。在该模式下，本项目只能生成 Google Maps 路线链接和地点搜索链接，无法自动获取 Google 的实时路线耗时、营业时间、评分和价格等级。

## 路线方案说明

### Route A：全量点位路线

Route A 会覆盖所有具有有效坐标的 Anitabi 点位。

如果点位较多，无法稳定放入一个 Google Maps URL，则会自动拆分为多个连续的 Google Maps 路线链接。这些分段链接合起来可以覆盖完整路线。

Route A 更适合用于查看完整巡礼点位分布。用户可以在 HTML 页面中删除不想去的点位，并根据剩余点位重新生成路线链接。

### Route B：时间适配路线

Route B 会根据用户提供的本地可用时间、起点位置、单段最长可接受步行距离和预计停留时间，筛选较适合当天完成的一部分点位。

Route B 的 HTML 页面支持：

* 添加未纳入路线的 Anitabi 点位。
* 拖动点位调整路线顺序。
* 删除不想去的点位。
* 重新生成 Google Maps 路线链接。
* 重新计算到达和离开时间。

在 Google Maps URL-only 模式下，本地 HTML 无法直接读取 Google Maps 的实时路线耗时。时间重新计算会优先尝试 OSRM / OpenStreetMap 的估算结果；如果不可用，则退回到基于距离的估算。公共交通耗时仍需在出发前通过 Google Maps 人工确认。

## 示例

`examples/hyouka-demo/` 文件夹中提供了一个《冰菓》圣地巡礼规划示例，包括：

* Route A 全量点位路线。
* Route B 时间适配路线。
* 可编辑 HTML 巡礼计划表。
* Anitabi 点位 JSON。
* 路线规划 JSON。

示例中的天气、营业时间、交通耗时和价格信息仅用于展示输出格式。实际出行前，请再次确认所有具有时效性的信息。

## 注意事项

* 请使用官方 API，并遵守相关数据源的使用条款。
* Anitabi 地标截图可能包含 `origin` 和 `originURL` 字段；展示拍照参考图时应保留这些来源信息。
* 营业时间、公共交通路线、价格、评分和天气都具有时效性。
* 出发前请再次确认当地天气、交通、营业时间、门票价格和餐厅信息。
* 未配置 Google Maps API Key 时，本项目无法自动获取精确的 Google 路线耗时、营业时间、评分和价格等级。
* 本项目生成的路线计划仅供规划参考，不构成实际出行可行性或安全性的保证。

## 中文输出要求

最终面向用户的行程、HTML 页面、天气摘要、路线标签、警告文本、状态字段和人工确认提示，默认使用中文。

必要时可以保留 Bangumi、Anitabi、Google Maps、OSRM、OpenStreetMap、API、URL、HTML、CSV、KML 和 JSON 等专有名词或技术名词。

不要在 HTML 中直接输出 `google_maps_url_only`、`balanced_time_fit`、`time_fit`、`unknown`、`scheduled` 或 `manual-added` 等内部枚举值；应将它们转换为中文显示文本。

## License

请根据你的实际情况选择许可证。若只是作为普通开源项目发布，可以考虑使用 MIT License。
