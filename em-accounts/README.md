# EM 期刊账号登记（子目录）

记录「在本人的 Editorial Manager 上，哪些期刊已经有账号」。

## 线上只显示 5 个字段

| 字段 | 说明 |
|---|---|
| journal | 期刊名 |
| publisher | 出版社 |
| username | 注册时用的用户名 |
| registered_at | 注册邮件日期 |
| status | 有账号 / 待核实 |

**本目录内的任何文件都不含、也不允许含：登录链接、一次性设密链接、重置链接、密码。**
需要这些信息时，只在本人电脑的私有目录 `hermes_work\em-accounts-local\` 内查看，该目录不在本仓库、不进 git、不上 Pages。

## 文件

- `accounts.public.json` — 唯一数据源，5 个字段，安全可公开
- `index.html` — 只看不改的静态页，读取上面的 json

## 数据来源

Gmail 中 41 封 Editorial Manager 注册通知（2025-06 ~ 2026-09），去重后 35 本期刊。
