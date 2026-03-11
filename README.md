# Nutrients Calculator

追踪人体必需营养素摄入量，基于科学依据的时间窗口，报告缺口并给出补充建议。

## 用法

**第一步：** 首次运行时自动生成 `meal_input.json` 模板。

**第二步：** 每次进食后，编辑 `meal_input.json`，在 `foods[]` 中填入吃了什么。支持四种格式：

### 格式一：自动查库（只填名称和重量）

程序内置 68 种常见食物数据库，直接填名称和克数，营养素自动补全。`name` 字段填下表中任意一个写法均可识别（中文、英文、别名都支持）：

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
| **蛋奶** | 鸡蛋 | `鸡蛋` `egg` `cooked egg` `whole egg` |
| | 蛋黄 | `蛋黄` `egg yolk` `yolk` |
| | 牛奶 💧 | `牛奶` `milk` `whole milk` |
| | 希腊酸奶 | `希腊酸奶` `greek yogurt` `Greek yogurt` |
| | 酸奶 | `酸奶` `yogurt` |
| | 硬奶酪 | `硬奶酪` `hard cheese` `cheddar` `cheese` |
| | 黄油 | `黄油` `butter` |
| **豆类** | 老豆腐 | `老豆腐` `firm tofu` `tofu` |
| | 扁豆 | `扁豆` `lentils` `cooked lentils` |
| | 黑豆 | `黑豆` `black beans` `cooked black beans` |
| | 鹰嘴豆 | `鹰嘴豆` `chickpeas` `cooked chickpeas` `garbanzo beans` |
| | 白豆 | `白豆` `white beans` `cooked white beans` `cannellini beans` |
| **谷物** | 面粉 | `面粉` `小麦粉` `all-purpose flour` `wheat flour` |
| | 白米饭 | `白米饭` `white rice` `cooked white rice` `米饭` |
| | 糙米饭 | `糙米饭` `brown rice` `cooked brown rice` |
| | 燕麦 | `燕麦` `oats` `dry oats` `rolled oats` |
| | 燕麦粥 | `燕麦粥` `oatmeal` `cooked oatmeal` `porridge` |
| | 全麦面包 | `全麦面包` `whole wheat bread` `wholemeal bread` |
| | 白面包 | `白面包` `white bread` |
| | 红薯 | `红薯` `sweet potato` `cooked sweet potato` |
| | 土豆 | `土豆` `potato` `boiled potato` `马铃薯` |
| **蔬菜** | 白菜 | `白菜` `大白菜` `napa cabbage` `chinese cabbage` |
| | 菠菜 | `菠菜` `spinach` `cooked spinach` |
| | 西兰花 | `西兰花` `broccoli` |
| | 胡萝卜 | `胡萝卜` `carrot` |
| | 红甜椒 | `红甜椒` `red bell pepper` `red pepper` `甜椒` |
| | 番茄 | `番茄` `tomato` `西红柿` |
| | 南瓜 | `南瓜` `pumpkin` `cooked pumpkin` |
| | 卷心菜 | `卷心菜` `cabbage` |
| | 羽衣甘蓝 | `羽衣甘蓝` `kale` |
| | 芦笋 | `芦笋` `asparagus` `cooked asparagus` |
| | 蘑菇 | `蘑菇` `mushroom` `mushrooms` |
| | 海带 | `海带` `kelp` `seaweed` |
| **水果** | 香蕉 | `香蕉` `banana` |
| | 橙子 | `橙子` `orange` |
| | 苹果 | `苹果` `apple` |
| | 猕猴桃 | `猕猴桃` `kiwifruit` `kiwi` |
| | 草莓 | `草莓` `strawberry` `strawberries` |
| | 牛油果 | `牛油果` `avocado` |
| | 梨 | `梨` `pear` |
| **坚果种子** | 杏仁 | `杏仁` `almonds` `almond` |
| | 核桃 | `核桃` `walnuts` `walnut` |
| | 奇亚籽 | `奇亚籽` `chia seeds` `chia` |
| | 亚麻籽 | `亚麻籽` `flaxseeds` `flax seeds` `linseed` |
| | 南瓜籽 | `南瓜籽` `pumpkin seeds` `pepitas` |
| | 葵花籽 | `葵花籽` `sunflower seeds` `sunflower seed` |
| | 腰果 | `腰果` `cashews` `cashew` |
| | 花生 | `花生` `peanuts` `peanut` `groundnuts` |
| | 巴西坚果 | `巴西坚果` `brazil nut` `brazil nuts` |
| **油盐调料** | 橄榄油 💧 | `橄榄油` `olive oil` |
| | 葵花籽油 💧 | `葵花籽油` `sunflower oil` |
| | 食盐 | `食盐` `table salt` `salt` |
| | 碘盐 | `碘盐` `iodized salt` |
| | 酱油 💧 | `酱油` `soy sauce` |
| | 黑巧克力 | `黑巧克力` `dark chocolate` `dark chocolate 70%` |
| **饮品** | 橙汁 💧 | `橙汁` `orange juice` |
| | 豆浆 💧 | `豆浆` `soy milk` `soymilk` |
| | 绿茶 💧 | `绿茶` `green tea` |
| | 红茶 💧 | `红茶` `black tea` |
| | 咖啡 💧 | `咖啡` `coffee` |

> 💧 表示液体食物，建议用 `amount_ml` 输入。名称匹配不区分大小写，忽略空格差异。

```json
{
  "foods": [
    { "name": "鸡胸肉", "amount_g": 150 },
    { "name": "brown rice", "amount_g": 100 }
  ]
}
```

### 格式二：液体食物（用 ml 或 l）

液体食物支持 `amount_ml` / `amount_l`，程序按密度自动换算克数：

```json
{
  "foods": [
    { "name": "牛奶", "amount_ml": 250 },
    { "name": "橄榄油", "amount_ml": 15 },
    { "name": "橙汁", "amount_l": 0.3 }
  ]
}
```

### 格式三：手动输入——按参考量换算

适合有营养成分表的食物。填写 `nutrients_per_100g`（标签上那份量的营养值）+ 参考量 + 实际摄入量，程序自动按比例换算。

> 只要填了任意一个非零营养素值，程序即视为手动模式，不调用内置数据库。

**3a：固体，标签以每100g为基准（最常见）**

```json
{ "name": "自制沙拉", "amount_g": 200,
  "nutrients_per_100g": { "protein": 5.0, "fat": 8.0, "vitamin_c": 30.0 } }
```

**3b：饮料/液体，标签以每 N ml 为基准**

加 `serving_ml` 指定标签参考量，再填 `amount_ml` 表示实际喝了多少毫升：

```json
{ "name": "番茄汁",
  "amount_ml": 300,
  "serving_ml": 200,
  "nutrients_per_100g": { "vitamin_c": 18.0, "sodium": 150.0, "potassium": 300.0 } }
```
→ 程序计算：300ml ÷ 200ml × 标签值（喝了1.5份）

**3c：固体，标签以非100g为基准（如每28g）**

加 `serving_g` 覆盖默认的100：

```json
{ "name": "谷物棒", "amount_g": 56, "serving_g": 28,
  "nutrients_per_100g": { "protein": 5.0, "carbohydrates": 20.0 } }
```
→ 程序计算：56g ÷ 28g × 标签值（吃了2份）

### 格式四：手动输入——本次摄入总量

适合包装食品，产品标签上直接写明了"本份"的营养总量（如每份蛋白质20g）。使用 `nutrients_total` 填写这一份的绝对值，**不需要填重量**：

```json
{
  "foods": [
    {
      "name": "蛋白棒",
      "nutrients_total": {
        "protein": 20.0,
        "fat": 5.0,
        "carbohydrates": 30.0,
        "vitamin_b6": 0.5
      }
    }
  ]
}
```

所有可用的 key 见下方「营养素 Key 列表」。不知道的项目直接省略（或填 `0`）即可。

**第三步：** 运行程序：

```bash
python -X utf8 nutrients_calculator.py
```

程序会记录本次摄入，并在 `outputs/YYYY-MM-DD/` 目录下生成带时间戳的 HTML 报告，同时在终端输出简要状态。

**第四步：** 手动清空 `meal_input.json` 的 `foods[]`，下次进食时重新填写。

---

### 其他命令

```bash
# 只查看当前状态，不读取 meal_input.json
python -X utf8 nutrients_calculator.py --status

# 查看最近 N 条摄入记录（默认 10 条）
python -X utf8 nutrients_calculator.py --history
python -X utf8 nutrients_calculator.py --history 20
```

---

## HTML 报告内容

报告保存在 `outputs/YYYY-MM-DD/report_HHMMSS.html`，包含：

- **本次摄入摘要**：列出本次记录的食物，以及自动查库时的提示
- **营养素一览表**：按时间尺度排序（今日 → 近7天 → 近14天 → 近30天），显示当前窗口摄入量、RDA目标、达标率和进度条
- **补充建议**：仅对未达标营养素列出推荐食物，按补充效率升序排列（所需最少克数的食物排在前面）
- **单位换算表**：g / mg / mcg 换算速查
- **缺乏风险**：列出各营养素缺乏可能引发的疾病

---

## 工作原理

程序为每种营养素设定**时间窗口**（每日 / 近7天 / 近14天 / 近30天），基于该营养素在人体内的储存时长来确定。例如：

- **维生素C、蛋白质、钙** 等：每日窗口（无显著体内储备，需每日补充）
- **脂溶性维生素 A/D/E/K**：近7天窗口（储存于肝脏和脂肪组织）
- **碘**：近14天窗口（甲状腺可储存约50-70天的量）
- **维生素B12、硒**：近30天窗口（肝脏储量可维持数年/数月）

每次运行程序时，在对应窗口内累加摄入量，与 RDA（推荐每日摄入量 × 窗口天数）对比，输出达标率。

---

## 手动输入时的营养素 Key 列表

格式3（`nutrients_per_100g`）和格式4（`nutrients_total`）中可使用的所有 key：

| Key | 营养素名称 | 单位 |
|-----|-----------|------|
| `protein` | 蛋白质 Protein | g |
| `fat` | 脂肪 Fat | g |
| `carbohydrates` | 碳水化合物 Carbohydrates | g |
| `fiber` | 膳食纤维 Dietary Fiber | g |
| `vitamin_a` | 维生素A Vitamin A | mcg RAE |
| `vitamin_c` | 维生素C Vitamin C | mg |
| `vitamin_d` | 维生素D Vitamin D | mcg |
| `vitamin_e` | 维生素E Vitamin E | mg |
| `vitamin_k` | 维生素K Vitamin K | mcg |
| `vitamin_b1` | 维生素B1 Thiamine | mg |
| `vitamin_b2` | 维生素B2 Riboflavin | mg |
| `vitamin_b3` | 维生素B3 Niacin | mg NE |
| `vitamin_b5` | 维生素B5 Pantothenic Acid | mg |
| `vitamin_b6` | 维生素B6 Pyridoxine | mg |
| `vitamin_b7` | 维生素B7 Biotin | mcg |
| `vitamin_b9` | 维生素B9 Folate | mcg DFE |
| `vitamin_b12` | 维生素B12 Cobalamin | mcg |
| `calcium` | 钙 Calcium | mg |
| `phosphorus` | 磷 Phosphorus | mg |
| `magnesium` | 镁 Magnesium | mg |
| `potassium` | 钾 Potassium | mg |
| `sodium` | 钠 Sodium | mg |
| `iron` | 铁 Iron | mg |
| `zinc` | 锌 Zinc | mg |
| `selenium` | 硒 Selenium | mcg |
| `iodine` | 碘 Iodine | mcg |
| `copper` | 铜 Copper | mg |
| `manganese` | 锰 Manganese | mg |
| `chromium` | 铬 Chromium | mcg |
| `molybdenum` | 钼 Molybdenum | mcg |
| `fluoride` | 氟 Fluoride | mg |
| `omega3` | Omega-3脂肪酸 | g |
| `salt_equivalent` | **食盐相当量** Salt Equivalent | **g**（自动换算为钠） |

不知道的项目直接省略即可，只填你知道的。

> **食盐相当量换算**：`食盐相当量(g) × 400 = 钠(mg)`，依据 WHO 及 GB 28050-2011 标准。产品标签只写"食盐相当量"时，填 `salt_equivalent` 即可，程序自动累加到钠。`sodium` 和 `salt_equivalent` 可同时填写，效果叠加。

---

## 营养素覆盖范围（32种）

| 类别 | 营养素 |
|------|--------|
| 宏量营养素 | 蛋白质、脂肪、碳水化合物、膳食纤维 |
| 脂溶性维生素 | A、D、E、K |
| B族维生素 | B1、B2、B3、B5、B6、B7、B9、B12 |
| 维生素C | C |
| 常量矿物质 | 钙、磷、镁、钾、钠 |
| 微量矿物质 | 铁、锌、硒、碘、铜、锰、铬、钼、氟 |
| 脂肪酸 | Omega-3 |

RDA 参考 WHO / IOM 成年人标准（约62.5kg体重）。

---

## 内置食物数据库（70种）

涵盖肉禽蛋奶、水产、蔬菜、水果、豆类、谷物、坚果、食用油、饮品等9大类。液体食物（牛奶、豆浆、橄榄油等）包含密度数据，支持 ml/l 输入。

食物名称支持中文、英文及常见别名匹配（如"三文鱼"="鲑鱼"="Salmon"）。

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `meal_input.json` | 用户填写本次进食内容（输入，非持久存储） |
| `intake_log.jsonl` | 历史摄入记录（程序自动维护，每行一条记录） |
| `nutrients_data.py` | 营养素数据库（RDA、时间窗口、食物来源、缺乏疾病） |
| `food_database.py` | 内置食物营养数据（70种食物） |
| `nutrients_calculator.py` | 主程序 |
| `outputs/YYYY-MM-DD/` | HTML报告，按日期分目录存储 |

---

## 依赖

Python 3.10+，无需安装第三方库。
