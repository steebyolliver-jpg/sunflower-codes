# 上线方案与发布记录

2026-09-14 用户确认使用下述公开仓库和 GitHub Pages 方案。现已完成发布，最终地址为 https://steebyolliver-jpg.github.io/sunflower-codes/ 。

首次 push 发布运行 34827949859 成功；随后手动运行 [34828022155](https://github.com/steebyolliver-jpg/sunflower-codes/actions/runs/34828022155) 成功。线上 HTTP 200，70 条兑换码，成功检查时间为北京时间 2026-09-14 17:27:18，自动化状态 enabled。线上 Chromium 手机模拟 9 条操作流程通过；未来每日触发及真实 iPhone 验收尚需实际证据。

## 推荐发布对象

- 使用本机已登录的 GitHub 账号 `steebyolliver-jpg`。
- 已创建独立公开仓库 [sunflower-codes](https://github.com/steebyolliver-jpg/sunflower-codes)。
- 仅上传本工具文件；不上传 FDE 其他记录、用户原始截图、个人浏览器数据或任何凭据。
- GitHub Pages 发布 `dist/`；GitHub Actions 每日北京时间 09:17 检查官方来源并发布新码库。定时触发可能延迟，不是精确闹钟。
- 源代码与兑换码目录将公开，使用勾选仍只在手机本地，不上传。
- 最终地址以 GitHub Pages 返回并实际回读的地址为准，不预先声称候选地址已存在。

## 执行步骤（1–6 已完成，7 待用户验收）

1. 在工具目录初始化独立 Git 仓库，精确检查上传范围。
2. 创建 `steebyolliver-jpg/sunflower-codes` 公开仓库，上传已验证源码至 `main`。
3. 启用 Pages 的 GitHub Actions 发布源，使用现有 `.github/workflows/daily-update.yml`。
4. 手动触发一次同一工作流；检查采集、数据保存、发布的实际结果。
5. 读取最终 HTTPS 链接中的首页及 `data/codes.json`，核对时间、数量、状态和最新官方码。
6. 保留首次运行链接与发布证据；每天自动触发是否成功需未来实际运行记录，不能把配置存在当作每日执行已验证。
7. 用户在 iPhone Safari 实测复制至微信、勾选、重开及添加到主屏幕。

不安装新软件、不购买域名、不消费模型 API。若账号权限、Pages 资格或网络访问受阻，仅做一次安全检查和一次低风险重试，报告真实阻塞，不擅自换平台。

## 运维

- GitHub Actions 可能延迟或被禁用；页面显示最近成功检查时间，超过 36 小时标为待更新。
- 采集失败会保留旧码库、发布失败状态并以失败结果结束任务；可在 GitHub Actions 手动重新运行。
- GitHub 文档说明公开仓库长期没有活动时定时工作流可能自动停用。本工作流每天提交检查时间，但仍需关注任务是否被手动停用或发生持续失败。
- 若必须调整平台、账号、公开范围或费用，需要重新说明并确认。

依据：[GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)、[GitHub schedule 事件](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)，核查日期 2026-09-14。
