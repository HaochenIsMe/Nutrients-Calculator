# 营养摄入计算器 · Nutrients Calculator

追踪人体必需营养素摄入量，基于科学依据的时间窗口报告缺口，并智能推荐菜肴补充不足。

支持 **桌面 GUI**（Windows / macOS / Linux）和 **Android 手机 App**。

---

## 功能一览

| 功能 | 说明 |
|------|------|
| 📊 营养素追踪 | 32种营养素，按科学时间窗口计算达标率 |
| 🍽 菜肴推荐 | 根据当日营养缺口，从60道中式家常菜中实时推荐 |
| 👤 多用户档案 | 支持多个用户配置文件，个性化计算 BMR / TDEE / RDA |
| 📋 摄入历史 | 完整历史记录，支持按日查看、清空 |
| 🖥 桌面 GUI | tkinter 可视化界面，五个标签页，支持点击列标题排序 |
| 📱 Android App | Kivy 移动端，手机直接使用，可打包为 APK |
| 🍲 中式菜肴库 | 60 道常见中式家常菜，含11项营养素数据 |
| 🥗 食物数据库 | 70 种常见食物，中英文名称均可识别 |

---

## 快速开始

### 桌面 GUI（推荐）

```bash
# 安装依赖（首次）
pip install pillow

# 启动 GUI
python gui.py
```

GUI 包含五个标签页：

1. **记录餐食** — 从食物数据库搜索添加，或手动填写营养标签（格式3 / 格式4）
2. **今日状态** — 当日10项核心营养素达标率，颜色标注不足 / 接近 / 达标
3. **历史记录** — 所有摄入记录倒序展示，支持删除
4. **营养报告** — 按时间窗口的完整32项报告，支持导出 HTML
5. **🍽 推荐菜肴** — 基于今日营养缺口推荐最优菜肴，显示缺口明细

顶部档案栏可切换用户、查看 BMR / TDEE，并管理多用户配置。

### Android 手机 App

在手机上使用，直接下载 APK 安装（无需 PC）。

如需自行构建 APK，参见下方 [构建 Android APK](#构建-android-apk)。

App 功能与桌面 GUI 对应：记录餐食、今日状态、菜肴推荐、历史记录、用户档案。

### 命令行（高级用法）

```bash
# 读取 data/meal_input.json 并记录本次摄入
python nutrients_calculator.py

# 仅查看当前营养状态，不记录摄入
python nutrients_calculator.py --status

# 查看最近 N 条记录（默认10条）
python nutrients_calculator.py --history 20
```

---

## 用户档案与个性化 RDA

每个用户可设置：

| 字段 | 说明 |
|------|------|
| 姓名 | 用于切换识别 |
| 性别 | 影响蛋白质、铁等 RDA |
| 年龄 | 影响钙、维生素D等 RDA |
| 体重 (kg) | 用于计算 BMR 和蛋白质需求 |
| 身高 (cm) | 用于 Mifflin-St Jeor 公式 |
| 活动量 | 1.2（久坐）/ 1.375（轻度）/ 1.55（中度）/ 1.725（积极） |

程序使用 **Mifflin-St Jeor 公式** 计算 BMR，再乘活动系数得到 TDEE，并据此个性化蛋白质、脂肪、碳水化合物的 RDA。

---

## 菜肴推荐算法

推荐基于**今日营养缺口最大化补充**原则：

1. 计算今日各营养素距目标的缺口
2. 对数据库中每道菜打分：`Σ min(菜肴含量, 缺口) / RDA × 缺口 / RDA`
3. 返回得分最高的 N 道菜，并标注主要补充的营养素

菜肴数据库包含 60 道中式家常菜，涵盖主食、荤菜、素菜、汤品、凉菜、豆制品六类。可通过 GUI「菜肴编辑」功能修改任意菜肴的营养数据。

---

## 食物输入格式

GUI 中的「手动填写」和命令行 `meal_input.json` 均支持以下四种格式：

### 格式一：自动查库（只填名称和重量）

内置 70 种常见食物，直接填名称和克数，营养素自动补全：

```json
{ "name": "鸡胸肉", "amount_g": 150 }
```

### 格式二：液体食物（ml / l）

```json
{ "name": "牛奶", "amount_ml": 250 }
```

### 格式三：手动输入——按参考量换算

适合有营养成分表的包装食品，填写每100g数据 + 实际摄入量：

```json
{ "name": "自制沙拉", "amount_g": 200,
  "nutrients_per_100g": { "protein": 5.0, "fat": 8.0, "vitamin_c": 30.0 } }
```

液体标签（如每200ml）：

```json
{ "name": "番茄汁", "amount_ml": 300, "serving_ml": 200,
  "nutrients_per_100g": { "vitamin_c": 18.0, "potassium": 300.0 } }
```

非100g参考量（如每28g）：

```json
{ "name": "谷物棒", "amount_g": 56, "serving_g": 28,
  "nutrients_per_100g": { "protein": 5.0, "carbohydrates": 20.0 } }
```

### 格式四：手动输入——直接填本次总量

适合标签直接标注"每份"绝对数值的产品：

```json
{ "name": "蛋白棒",
  "nutrients_total": { "protein": 20.0, "fat": 5.0, "carbohydrates": 30.0 } }
```

---

## 内置食物数据库（70种）

| 类别 | 食物 | 可用名称 |
|------|------|---------|
| **肉禽** | 鸡胸肉 | `鸡胸肉` `chicken breast` `鸡肉` |
| | 牛肉 | `牛肉` `beef` `lean beef` |
| | 猪肉 | `猪肉` `pork` `pork loin` |
| | 牛肝 | `牛肝` `beef liver` `liver` |
| **水产** | 三文鱼 | `三文鱼` `salmon` |
| | 金枪鱼罐头 | `金枪鱼罐头` `canned tuna` `tuna` |
| | 沙丁鱼罐头 | `沙丁鱼罐头` `canned sardines` `sardines` |
| | 虾 | `虾` `shrimp` `prawns` |
| | 牡蛎 | `牡蛎` `oysters` `oyster` |
| | 鳕鱼 | `鳕鱼` `cod` |
| **蛋奶** | 鸡蛋 | `鸡蛋` `egg` `whole egg` |
| | 蛋黄 | `蛋黄` `egg yolk` `yolk` |
| | 牛奶 💧 | `牛奶` `milk` `whole milk` |
| | 希腊酸奶 | `希腊酸奶` `greek yogurt` |
| | 硬奶酪 | `硬奶酪` `hard cheese` `cheddar` `cheese` |
| **豆类** | 老豆腐 | `老豆腐` `firm tofu` `tofu` |
| | 扁豆 | `扁豆` `lentils` |
| | 黑豆 | `黑豆` `black beans` |
| | 鹰嘴豆 | `鹰嘴豆` `chickpeas` |
| **谷物** | 白米饭 | `白米饭` `white rice` `米饭` |
| | 糙米饭 | `糙米饭` `brown rice` |
| | 燕麦 | `燕麦` `oats` `rolled oats` |
| | 全麦面包 | `全麦面包` `whole wheat bread` |
| | 白面包 | `白面包` `white bread` |
| | 红薯 | `红薯` `sweet potato` |
| | 土豆 | `土豆` `potato` `马铃薯` |
| **蔬菜** | 菠菜 | `菠菜` `spinach` |
| | 西兰花 | `西兰花` `broccoli` |
| | 胡萝卜 | `胡萝卜` `carrot` |
| | 番茄 | `番茄` `tomato` `西红柿` |
| | 蘑菇 | `蘑菇` `mushroom` |
| | 海带 | `海带` `kelp` `seaweed` |
| **水果** | 香蕉 | `香蕉` `banana` |
| | 橙子 | `橙子` `orange` |
| | 苹果 | `苹果` `apple` |
| | 猕猴桃 | `猕猴桃` `kiwi` |
| | 牛油果 | `牛油果` `avocado` |
| **坚果** | 杏仁 | `杏仁` `almonds` |
| | 核桃 | `核桃` `walnuts` |
| | 奇亚籽 | `奇亚籽` `chia seeds` |
| | 花生 | `花生` `peanuts` |
| **油盐** | 橄榄油 💧 | `橄榄油` `olive oil` |
| | 食盐 | `食盐` `salt` |
| | 碘盐 | `碘盐` `iodized salt` |
| | 酱油 💧 | `酱油` `soy sauce` |
| **饮品** | 橙汁 💧 | `橙汁` `orange juice` |
| | 豆浆 💧 | `豆浆` `soy milk` |
| | 咖啡 💧 | `咖啡` `coffee` |

> 💧 液体食物，建议用 `amount_ml` 输入。名称匹配不区分大小写。

---

## 营养素 Key 列表

格式3（`nutrients_per_100g`）和格式4（`nutrients_total`）可使用的所有 key：

| Key | 营养素 | 单位 |
|-----|--------|------|
| `protein` | 蛋白质 | g |
| `fat` | 脂肪 | g |
| `carbohydrates` | 碳水化合物 | g |
| `fiber` | 膳食纤维 | g |
| `sugar` | 糖 | g |
| `vitamin_a` | 维生素A | mcg RAE |
| `vitamin_c` | 维生素C | mg |
| `vitamin_d` | 维生素D | mcg |
| `vitamin_e` | 维生素E | mg |
| `vitamin_k` | 维生素K | mcg |
| `vitamin_b1` | 维生素B1 Thiamine | mg |
| `vitamin_b2` | 维生素B2 Riboflavin | mg |
| `vitamin_b3` | 维生素B3 Niacin | mg NE |
| `vitamin_b5` | 维生素B5 | mg |
| `vitamin_b6` | 维生素B6 | mg |
| `vitamin_b7` | 维生素B7 Biotin | mcg |
| `vitamin_b9` | 维生素B9 Folate | mcg DFE |
| `vitamin_b12` | 维生素B12 | mcg |
| `calcium` | 钙 | mg |
| `phosphorus` | 磷 | mg |
| `magnesium` | 镁 | mg |
| `potassium` | 钾 | mg |
| `sodium` | 钠 | mg |
| `iron` | 铁 | mg |
| `zinc` | 锌 | mg |
| `selenium` | 硒 | mcg |
| `iodine` | 碘 | mcg |
| `copper` | 铜 | mg |
| `manganese` | 锰 | mg |
| `omega3` | Omega-3 | g |
| `salt_equivalent` | **食盐相当量** | g（自动换算为钠） |

> **食盐相当量换算**：`食盐相当量(g) × 400 = 钠(mg)`，依据 WHO 及 GB 28050-2011 标准。

---

## 工作原理

### 时间窗口

程序为每种营养素设定时间窗口（每日 / 近7天 / 近14天 / 近30天），基于该营养素在人体内的储存时长：

| 窗口 | 营养素 |
|------|--------|
| 每日 | 蛋白质、碳水、脂肪、维生素C、钙、铁等（无显著体内储备） |
| 近7天 | 脂溶性维生素 A、D、E、K（储存于肝脏和脂肪组织） |
| 近14天 | 碘（甲状腺储量约50-70天，取保守估算） |
| 近30天 | 维生素B12、硒（肝脏储量可维持数月） |

### 个性化 RDA

使用 **Mifflin-St Jeor 公式** 计算基础代谢率（BMR），乘以活动系数得到 TDEE，再据此推算：

- 蛋白质：0.83 g × 体重(kg)（WHO/FAO 2007 推荐）
- 脂肪：TDEE × 30% ÷ 9
- 碳水：TDEE × 55% ÷ 4
- 其他营养素：按用户性别和年龄查阅 WHO / IOM 标准

---

## 构建 Android APK

Buildozer 仅支持 Linux 构建环境（可用 WSL）。

### 方法一：GitHub Actions（推荐，无需本地 Linux）

推送代码到 GitHub，Actions 自动构建 APK：

```bash
git push origin main
```

进入 GitHub 仓库 → **Actions** → 选择最新构建 → 下载 **Artifacts** 中的 APK 文件。

发布正式版本（创建 Release）：

```bash
git tag v1.0
git push --tags
```

标签推送会自动触发 GitHub Release 并附带 APK。

### 方法二：本地 WSL 构建

```bash
# 在 WSL Ubuntu 中：
sudo apt update && sudo apt install -y python3-pip git zip unzip openjdk-17-jdk build-essential
pip3 install buildozer cython

cd /mnt/d/Projects/nutrients-calculator
buildozer android debug

# APK 输出至 bin/ 目录
# 首次构建约 25 分钟（需下载 Android SDK/NDK ~2GB）
```

---

## 文件结构

```
nutrients-calculator/
├── main.py                   # Android 入口（Buildozer 要求）
├── gui.py                    # 桌面 GUI（tkinter）
├── kivy_main.py              # 移动端 UI（Kivy / Android）
├── nutrients_calculator.py   # 核心计算引擎 + CLI
├── nutrients_data.py         # 32种营养素的 RDA、时间窗口、食物来源
├── food_database.py          # 食物数据库（70种）
├── dish_database.py          # 中式菜肴数据库（60道）
├── dish_recommender.py       # 菜肴推荐算法
├── user_profiles.py          # 多用户档案管理 + 个性化 RDA
├── buildozer.spec            # Android 打包配置
├── .github/workflows/
│   └── build-apk.yml         # GitHub Actions APK 自动构建
└── data/                     # 运行时数据（本地，不提交到 git）
    ├── intake_log.jsonl      # 摄入历史记录
    ├── meal_input.json       # CLI 输入模板
    ├── profiles.json         # 用户档案存储
    ├── dish_overrides.json   # 菜肴数据自定义覆盖
    └── outputs/              # HTML 报告（按日期分目录）
```

---

## 依赖

| 环境 | 依赖 |
|------|------|
| 桌面 GUI | Python 3.10+，`pillow`（`pip install pillow`） |
| Android App | `kivy`（`pip install kivy`）；APK 构建需要 Buildozer + Linux |
| 命令行 | Python 3.10+，无需第三方库 |
