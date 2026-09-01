# BCM GEO 真实推荐增长引擎

一套面向 **生成式引擎优化（GEO）**、AI 搜索引用、品牌推荐、传统搜索可见性与业务转化的结果型 Agent Skill。

它不把“做了多少配置”当成果，而是回答：

> 网站是否真的被搜索引擎发现、抓取、收录和排名？品牌是否真的在 AI 回答中被提及、引用、推荐，并带来可验证的访问或转化？

## 核心证据阶梯

```text
可访问 -> 已发现 -> 已抓取 -> 已收录 -> 有排名
       -> 被提及 -> 被引用 -> 被推荐 -> 有转化
```

只能报告已经直接验证的最高状态，不能跳级推断：

- HTTP 200 不等于已收录；
- 平台接收 URL 不等于已抓取；
- `llms.txt` 或结构化数据上线不等于 AI 已采用；
- 单次品牌提及不等于稳定推荐；
- 单次推荐不等于产生流量或成交。

## 我们自己的特色

- **真实推荐闭环**：基线盲测、限制层诊断、受控发布、抓取窗口、同题复测、转化归因。
- **不以内部评分自证成功**：分数只帮助排序，不能代替外部证据。
- **严格匹配样本**：前后对比必须匹配提示词哈希、平台、地区和语言。
- **覆盖国内与国际场景**：面向 Google、Bing、百度及可观测的主流 AI 回答系统。
- **多网站意图治理**：一个商业意图明确一个首选站点和页面，避免内部竞争与重复内容。
- **站内与站外协同**：实体事实、可引用证据、独立佐证、内容可回答性与落地转化共同优化。
- **生产发布门禁**：备份、源站、公网边缘、渲染结果、平台回执、监控和回滚分层验收。
- **零运行依赖**：配套脚本完全离线、无密钥、无隐藏网络请求。
- **跨工具证据格式**：提供严格 CSV 导入、版本化 JSON Schema 和隐私风险可控的案例导出。
- **结论发布闸门**：实施完成、外部结果、观察变化与因果估计分别采用不同证据门槛。
- **多语言诊断完整性**：中文和其他语言采用本地化规则，不把英文词数、代词或大写率当通用 GEO 标准。

## 安装

```bash
git clone https://github.com/yht0912/bcm-geo-optimizer.git \
  "$HOME/.agents/skills/bcm-geo-optimizer"
```

如 Codex 使用独立技能目录，可链接共享源：

```bash
ln -s "$HOME/.agents/skills/bcm-geo-optimizer" \
  "$HOME/.codex/skills/bcm-geo-optimizer"
```

安装后新建会话，使 Agent 重新加载技能目录。

## 使用示例

```text
使用 $bcm-geo-optimizer 为我的网站建立 ChatGPT、Gemini、Perplexity、
Google、Bing 和百度基线，并制定有验收标准的 90 天优化计划。
```

```text
使用 $bcm-geo-optimizer 对比改版前后的同题 AI 回答，
只统计匹配样本，不做因果夸大。
```

## 离线证据工具

生成结果记分卡：

```bash
python3 scripts/geo_outcome_scorecard.py \
  --input examples/evidence-sample.json \
  --output /tmp/geo-scorecard.json
```

比较基线与复测：

```bash
python3 scripts/geo_delta_compare.py \
  --baseline examples/evidence-baseline.json \
  --retest examples/evidence-retest.json \
  --output /tmp/geo-delta.json
```

生成透明、限制层优先的行动队列：

```bash
python3 scripts/geo_action_prioritizer.py \
  --input examples/actions-sample.json \
  --output /tmp/geo-action-queue.json
```

将表格导出转换为标准证据包：

```bash
python3 scripts/geo_csv_import.py \
  --input examples/evidence-sample.csv \
  --study-id example-study \
  --purpose "合成数据导入检查" \
  --output /tmp/geo-evidence.json
```

生成稳定可匹配的去标识化复核副本：

```bash
export GEO_ANONYMIZATION_SALT='使用至少16字节且不得入库的随机值'
python3 scripts/geo_privacy_export.py \
  --input /tmp/geo-evidence.json \
  --time-granularity day \
  --output /tmp/geo-evidence-public.json
```

对外发布前校验结果结论：

```bash
python3 scripts/geo_claim_gate.py \
  --input examples/outcome-claims-sample.json \
  --output /tmp/geo-claim-gate.json \
  --strict
```

脚本只验证和汇总输入的真实观察，不访问平台、不制造证据、不自动声称因果关系。

隐私导出只能降低披露风险，不能保证绝对匿名；对外分享前必须复核残余识别风险。详见[数据互操作与隐私导出](references/data-interoperability.md)。

标准数据契约：

- [证据包 JSON Schema](schemas/evidence-bundle.schema.json)
- [行动包 JSON Schema](schemas/action-bundle.schema.json)
- [结果结论 JSON Schema](schemas/outcome-claim.schema.json)

## 质量验证

```bash
python3 scripts/validate_package.py
python3 -m unittest discover -s tests -v
```

完整方法见 [SKILL.md](SKILL.md)，数据规范见 [证据契约](references/evidence-contract.md)。示例数据全部为合成数据，不代表任何真实平台表现。

## 独立实现声明

本项目围绕真实推荐结果、生产验证与业务归因独立设计和实现，不包含从其他 GEO 项目复制的源代码、提示词、评分公式、文档表达或视觉资产。详见[方法与知识产权边界](references/methodology-and-ip.md)。

## 许可证

BCM 原创公开实现采用 [MIT](LICENSE) 许可证，原始版权归南昌包参谋品牌策划有限公司；
该许可不包含 BCM 商标、生产服务、凭据、客户数据或私有策略。详见
[权属边界](OWNERSHIP.md)、[来源记录](PROVENANCE.md)、
[第三方说明](THIRD_PARTY_NOTICES.md)和[商标政策](TRADEMARKS.md)。
