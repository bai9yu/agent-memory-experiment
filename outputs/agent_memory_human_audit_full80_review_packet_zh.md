# full80 人工复核阅读包

本阅读包由盲审 CSV 自动生成，只展示人工判断所需的 query、自动错误类型、Top memory 和 gold memory；不展示 LLM-assisted 预标注，避免人工复核被模型标签锚定。

## 使用方式

- 源盲审表：`outputs/agent_memory_human_audit_full80_blind_review.csv`
- 样本数：80
- 已完整填写：0/80
- 阅读每个样本后，把判断结果回填到源 CSV 的 `human_*` 字段。
- 完成后运行 merge/agreement/readiness 脚本，生成 Human/LLM agreement 和门禁结果。

## 字段取值

| 字段 | 判断问题 | 允许取值 |
|---|---|---|
| `human_auto_reason_correct` | 自动错误类型是否正确 | `yes / partial / no` |
| `human_top_memory_relevant` | Top memory 是否回答或部分回答 query | `yes / partial / no` |
| `human_gold_memory_sufficient` | Gold memory 是否足以支持答案判断 | `yes / no / unclear` |

## 快速填写表

| Review | Audit ID | Query ID | auto_reason_correct | top_memory_relevant | gold_memory_sufficient | Notes |
|---:|---|---|---|---|---|---|
| 1 | audit_039 | q00962 |  |  |  |  |
| 2 | audit_009 | q00889 |  |  |  |  |
| 3 | audit_069 | q01772 |  |  |  |  |
| 4 | audit_010 | q00183 |  |  |  |  |
| 5 | audit_052 | q01246 |  |  |  |  |
| 6 | audit_047 | q01865 |  |  |  |  |
| 7 | audit_014 | q00633 |  |  |  |  |
| 8 | audit_064 | q00695 |  |  |  |  |
| 9 | audit_080 | q01819 |  |  |  |  |
| 10 | audit_076 | q00520 |  |  |  |  |
| 11 | audit_031 | q00459 |  |  |  |  |
| 12 | audit_071 | q01605 |  |  |  |  |
| 13 | audit_066 | q00176 |  |  |  |  |
| 14 | audit_051 | q01147 |  |  |  |  |
| 15 | audit_034 | q00645 |  |  |  |  |
| 16 | audit_016 | q01031 |  |  |  |  |
| 17 | audit_022 | q01655 |  |  |  |  |
| 18 | audit_046 | q01783 |  |  |  |  |
| 19 | audit_054 | q01340 |  |  |  |  |
| 20 | audit_001 | q00349 |  |  |  |  |
| 21 | audit_073 | q01811 |  |  |  |  |
| 22 | audit_049 | q00547 |  |  |  |  |
| 23 | audit_063 | q00589 |  |  |  |  |
| 24 | audit_012 | q00367 |  |  |  |  |
| 25 | audit_038 | q00957 |  |  |  |  |
| 26 | audit_060 | q01337 |  |  |  |  |
| 27 | audit_007 | q00442 |  |  |  |  |
| 28 | audit_025 | q00970 |  |  |  |  |
| 29 | audit_062 | q00573 |  |  |  |  |
| 30 | audit_053 | q01314 |  |  |  |  |
| 31 | audit_024 | q00882 |  |  |  |  |
| 32 | audit_042 | q01294 |  |  |  |  |
| 33 | audit_020 | q01345 |  |  |  |  |
| 34 | audit_048 | q01924 |  |  |  |  |
| 35 | audit_035 | q00667 |  |  |  |  |
| 36 | audit_037 | q00900 |  |  |  |  |
| 37 | audit_030 | q00410 |  |  |  |  |
| 38 | audit_058 | q01136 |  |  |  |  |
| 39 | audit_032 | q00568 |  |  |  |  |
| 40 | audit_074 | q01884 |  |  |  |  |
| 41 | audit_026 | q00016 |  |  |  |  |
| 42 | audit_006 | q00028 |  |  |  |  |
| 43 | audit_077 | q00555 |  |  |  |  |
| 44 | audit_019 | q01169 |  |  |  |  |
| 45 | audit_023 | q00071 |  |  |  |  |
| 46 | audit_061 | q01814 |  |  |  |  |
| 47 | audit_072 | q01670 |  |  |  |  |
| 48 | audit_017 | q01052 |  |  |  |  |
| 49 | audit_003 | q01639 |  |  |  |  |
| 50 | audit_059 | q01316 |  |  |  |  |
| 51 | audit_027 | q00056 |  |  |  |  |
| 52 | audit_078 | q01242 |  |  |  |  |
| 53 | audit_044 | q01741 |  |  |  |  |
| 54 | audit_055 | q01576 |  |  |  |  |
| 55 | audit_050 | q00715 |  |  |  |  |
| 56 | audit_029 | q00340 |  |  |  |  |
| 57 | audit_004 | q01760 |  |  |  |  |
| 58 | audit_002 | q01430 |  |  |  |  |
| 59 | audit_018 | q01055 |  |  |  |  |
| 60 | audit_075 | q00133 |  |  |  |  |
| 61 | audit_067 | q00475 |  |  |  |  |
| 62 | audit_065 | q01789 |  |  |  |  |
| 63 | audit_068 | q01349 |  |  |  |  |
| 64 | audit_070 | q01182 |  |  |  |  |
| 65 | audit_056 | q01803 |  |  |  |  |
| 66 | audit_013 | q00502 |  |  |  |  |
| 67 | audit_028 | q00314 |  |  |  |  |
| 68 | audit_008 | q00583 |  |  |  |  |
| 69 | audit_033 | q00609 |  |  |  |  |
| 70 | audit_041 | q01233 |  |  |  |  |
| 71 | audit_079 | q01663 |  |  |  |  |
| 72 | audit_045 | q01756 |  |  |  |  |
| 73 | audit_057 | q00982 |  |  |  |  |
| 74 | audit_011 | q00304 |  |  |  |  |
| 75 | audit_036 | q00858 |  |  |  |  |
| 76 | audit_040 | q01164 |  |  |  |  |
| 77 | audit_021 | q01547 |  |  |  |  |
| 78 | audit_043 | q01366 |  |  |  |  |
| 79 | audit_015 | q00973 |  |  |  |  |
| 80 | audit_005 | q01915 |  |  |  |  |

## 样本卡片

### 1. audit_039 / q00962

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What does Tim want to do after his basketball career? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 3 |
| Top memory | `llm_01051` / `preference`：Tim's favorite basketball player is LeBron James. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00997` | `goal` | John is working on better shooting and making more impact on the court. |
| `llm_00998` | `` | John is looking into endorsements and building his brand for life after basketball. |
| `llm_00999` | `` | John wants to start a foundation and do charity work to make a positive difference. |
| `llm_01000` | `` |  |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 2. audit_009 / q00889

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What does Tim have that serves as a reminder of hard work and is his prized possession? |
| 自动错误类型 | `career_education_neighbor` |
| First rank | 13 |
| Top memory | `llm_01062` / `hobby`：Tim enjoys reading and does it as usual. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01050` | `hobby` | Tim owns a basketball signed by his favorite player, LeBron James. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 3. audit_069 / q01772

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What is the motto of Sam's family? |
| 自动错误类型 | `relationship_neighbor` |
| First rank | 2 |
| Top memory | `llm_02219` / `family`：Sam's family has been a rock for him through everything. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02181` | `family` | Evan's family motto is 'Bring it on Home', from a trip to Banff. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 4. audit_010 / q00183

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What did Melanie find in her neighborhood during her walk? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 24 |
| Top memory | `llm_00077` / `family`：Melanie's family supported her during her move. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00134` | `event` | Caroline saw a rainbow sidewalk for Pride Month in her neighborhood. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 5. audit_052 / q01246

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What did John organize with his friends on May 8, 2022? |
| 自动错误类型 | `other` |
| First rank | 2 |
| Top memory | `llm_01701` / `event`：John organized an online comp with his programmer friends last week. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01530` | `event` | John organized a CS:GO charity tournament with friends yesterday. |
| `llm_01535` | `hobby` | John plays CS:GO and considers it his favorite game. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 6. audit_047 / q01865

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What did Dave open in May 2023? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 6 |
| Top memory | `llm_02272` / `goal`：Dave's dream was to open a car maintenance shop, and he achieved it. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02294` | `event` | Dave opened his car shop last week and celebrated with friends. |
| `llm_02295` | `work` | Dave owns a car shop and is passionate about helping with people's rides. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 7. audit_014 / q00633

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What did Joanna plan to do with the recipe Nate promised to share? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 31 |
| Top memory | `llm_00759` / `plan`：Nate promised to give Joanna the vegan ice cream recipe tomorrow. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00760` | `plan` | Joanna plans to make the vegan ice cream for her family this weekend. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 8. audit_064 / q00695

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What does Nate love most about having turtles? |
| 自动错误类型 | `preference_neighbor` |
| First rank | 6 |
| Top memory | `llm_00637` / `preference`：Nate recommends having pets like turtles for times of stress. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00894` | `hobby` | Nate has pet turtles that bring him peace and calm. |
| `llm_00895` | `preference` | Nate loves that his turtles don't require much looking after. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 9. audit_080 / q01819

| 项目 | 内容 |
|---|---|
| Query type | 2 |
| Query | When was Calvin's album released? |
| 自动错误类型 | `temporal_neighbor` |
| First rank | 2 |
| Top memory | `llm_02489` / `event`：Calvin released a new album. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02397` | `emotion` | Calvin released his album on September 11, 2023. |
| `llm_02398` | `event` | Calvin is motivated by the positive reception of his album to continue making music. |
| `llm_02406` | `relationship` | Calvin and Dave have a friendly relationship and enjoy chatting about music and hobbies. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 10. audit_076 / q00520

| 项目 | 内容 |
|---|---|
| Query type | 2 |
| Query | When did Joanna start writing her third screenplay? |
| 自动错误类型 | `temporal_neighbor` |
| First rank | 5 |
| Top memory | `llm_00734` / `work`：Joanna recently finished writing a screenplay. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00723` | `work` | Joanna has written her third book, which is about loss, identity, and connection. |
| `llm_00724` | `` | Joanna's third book is personal and based on a story she had for ages but just got the courage to write. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 11. audit_031 / q00459

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | Who inspired John to start volunteering? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 4 |
| Top memory | `llm_00455` / `emotion`：John found volunteering at the career fair rewarding and was inspired to help kids with lack of resources. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00410` | `relationship` | Maria started volunteering to make a difference, inspired by her aunt who believed in volunteering and helped her family when struggling. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 12. audit_071 / q01605

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | What kind of healthy food suggestions has Evan given to Sam? |
| 自动错误类型 | `semantic_neighbor` |
| First rank | 20 |
| Top memory | `llm_02208` / `plan`：Evan plans to send Sam recipes for healthy snacks and cookies. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02041` | `health` | Sam agreed to try swapping soda for flavored seltzer water and candy for dark chocolate with high cocoa content. |
| `llm_02050` | `hobby` | Evan is reading 'The Great Gatsby' and finds it gripping. |
| `llm_02052` | `plan` | Evan suggested flavored seltzer water as an alternative to soda and recommended air-popped popcorn or fruit as low-calorie snacks. |
| `llm_02205` | `preference` |  |
| `llm_02206` | `` |  |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 13. audit_066 / q00176

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What did Caroline and her family see during their camping trip last year? |
| 自动错误类型 | `relationship_neighbor` |
| First rank | 3 |
| Top memory | `llm_00053` / `event`：Caroline had a picnic with friends and family last week. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00095` | `event` | Melanie's best camping memory is seeing the Perseid meteor shower during a camping trip last year. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 14. audit_051 / q01147

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What type of jewelry does Andrew make? |
| 自动错误类型 | `other` |
| First rank | 2 |
| Top memory | `llm_01177` / `preference`：Andrew does not have any pets currently, but he loves animals. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01367` | `hobby` | Audrey makes jewelry from recycled objects like bottle caps, buttons, and broken jewelry. |
| `llm_01371` | `preference` | Audrey values combining creativity and sustainability in her jewelry making. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 15. audit_034 / q00645

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What type of ice cream does Joanna mention that Nate makes and is delicious? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 12 |
| Top memory | `llm_00897` / `event`：Nate offered Joanna some of his coconut milk ice cream. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00778` | `hobby` | Nate loves making dairy-free desserts, especially coconut milk ice cream. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 16. audit_016 / q01031

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | What has Andrew done with his dogs? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 29 |
| Top memory | `llm_01420` / `identity`：Andrew has two dogs named Toby and Buddy. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01298` | `hobby` | Andrew plans to take Toby hiking on a local trail. |
| `llm_01392` | `plan` | Andrew enjoys taking walks with Buddy. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 17. audit_022 / q01655

| 项目 | 内容 |
|---|---|
| Query type | 2 |
| Query | What was Sam doing on December 4, 2023? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 24 |
| Top memory | `llm_02079` / `health`：Sam is on a diet and living healthier as of August 2023. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02175` | `event` | Sam attended a Weight Watchers meeting yesterday. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 18. audit_046 / q01783

| 项目 | 内容 |
|---|---|
| Query type | 2 |
| Query | When did Calvin first travel to Tokyo? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 8 |
| Top memory | `llm_02451` / `plan`：Calvin is going to Tokyo next month after the tour ends. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02261` | `event` | Calvin attended a music festival in Tokyo recently and found it enriching. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 19. audit_054 / q01340

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What games were played at the gaming tournament organized by James on 31 October, 2022? |
| 自动错误类型 | `other` |
| First rank | 8 |
| Top memory | `llm_01477` / `event`：James received gaming tips from a team member at the tournament. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01713` | `event` | John organized a gaming tournament with his buddies last night, playing Fortnite, Overwatch, and Apex Legends, to raise money for a children's hospital. |
| `llm_01714` | `` | John and his gaming pals raised a decent amount of money for a children's hospital during the gaming tournament. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 20. audit_001 / q00349

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | What activities has Maria done with her church friends? |
| 自动错误类型 | `activity_neighbor` |
| First rank | 3 |
| Top memory | `llm_00605` / `event`：Maria did community work with friends from church yesterday. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00576` | `event` | Maria went hiking with church friends last weekend and found it refreshing. |
| `llm_00568` | `goal` | Maria had a picnic with friends from church last weekend. |
| `llm_00602` | `plan` | John lost his job at a mechanical engineering company. |
| `llm_00603` | `work` |  |
| `llm_00604` | `` |  |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 21. audit_073 / q01811

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | What does Calvin do to relax? |
| 自动错误类型 | `semantic_neighbor` |
| First rank | 3 |
| Top memory | `llm_02423` / `hobby`：Calvin has a project he works on to chill out. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02286` | `emotion` | Calvin relaxes by taking long drives in his car. |
| `llm_02287` | `hobby` | Calvin has been enjoying learning about Japanese culture. |
| `llm_02288` | `` | Calvin is experiencing creative block with his music. |
| `llm_02303` | `` |  |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 22. audit_049 / q00547

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | How many times has Joanna's scripts been rejected? |
| 自动错误类型 | `other` |
| First rank | 3 |
| Top memory | `llm_00869` / `event`：Joanna submitted a few more scripts last week. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00737` | `event` | Joanna received a rejection letter from a major company for her screenplay, which made her feel disheartened. |
| `llm_00738` | `work` | Joanna has written a screenplay. |
| `llm_00842` | `` | Joanna recently received another rejection from a production company. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 23. audit_063 / q00589

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What is Nate's favorite book series about? |
| 自动错误类型 | `preference_neighbor` |
| First rank | 3 |
| Top memory | `llm_00699` / `preference`：Nate's favorite movie trilogy is a fantasy/sci-fi series with great world building and battles. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00700` | `preference` | Nate recommends a book series with adventures, magic, and great characters. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 24. audit_012 / q00367

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | How many dogs has Maria adopted from the dog shelter she volunteers at? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 32 |
| Top memory | `llm_00459` / `event`：Maria recently gave talks at the homeless shelter where she volunteers. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00615` | `event` | Maria got a puppy named Coco two weeks ago. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 25. audit_038 / q00957

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | How long did Tim and his high school basketball teammates play together? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 6 |
| Top memory | `llm_00965` / `education`：Tim is focusing on school and reading fantasy books. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00975` | `event` | John played on a high school sports team with friends for four years. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 26. audit_060 / q01337

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What kind of gig was James offered at the game dev non-profit organization? |
| 自动错误类型 | `persona_confusion` |
| First rank | 2 |
| Top memory | `llm_01687` / `event`：John got an email about a volunteer gig at a game dev non-profit. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01689` | `work` | John was offered a programming mentor role for game developers at a non-profit. |
| `llm_01690` | `` | John will be teaching coding and assisting with projects as a programming mentor. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 27. audit_007 / q00442

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What happened to John's job in August 2023? |
| 自动错误类型 | `career_education_neighbor` |
| First rank | 4 |
| Top memory | `llm_01643` / `plan`：John has a day off tomorrow (27 August 2022). |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00602` | `goal` | John lost his job at a mechanical engineering company. |
| `llm_00603` | `plan` | John is looking for opportunities in the tech industry. |
| `llm_00604` | `work` | John found a potential job at a tech company that needs his mechanical skills for their hardware team. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 28. audit_025 / q00970

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | Who is one of Tim's sources of inspiration for painting? |
| 自动错误类型 | `identity_neighbor` |
| First rank | 18 |
| Top memory | `llm_01034` / `preference`：Tim draws inspiration for his writing from books, movies, real-life experiences, and certain authors. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01035` | `preference` | Tim is inspired by J.K. Rowling and takes notes on her style for his own writing. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 29. audit_062 / q00573

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | What are Nate's favorite desserts? |
| 自动错误类型 | `preference_neighbor` |
| First rank | 5 |
| Top memory | `llm_00807` / `preference`：Nate's favorite dish from his cooking show is coconut milk ice cream. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00646` | `event` | Nate discovered he can make coconut milk ice cream and tried it. |
| `llm_00649` | `hobby` | Nate likes coconut milk, chocolate, and mixed berry flavors for dairy-free desserts. |
| `llm_00650` | `preference` | Nate made a dairy-free chocolate cake with berries recently. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 30. audit_053 / q01314

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What was the main goal of the money raised from the political campaign organized by John and his friends in May 2022? |
| 自动错误类型 | `other` |
| First rank | 6 |
| Top memory | `llm_01714` / `event`：John and his gaming pals raised a decent amount of money for a children's hospital during the gaming tournament. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01531` | `event` | John's CS:GO tournament raised money for a dog shelter near his street. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 31. audit_024 / q00882

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | Who is one of Tim's sources of inspiration for writing? |
| 自动错误类型 | `identity_neighbor` |
| First rank | 2 |
| Top memory | `llm_01034` / `preference`：Tim draws inspiration for his writing from books, movies, real-life experiences, and certain authors. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01035` | `preference` | Tim is inspired by J.K. Rowling and takes notes on her style for his own writing. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 32. audit_042 / q01294

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What does John feel about starting the journey as a programming mentor for game developers? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 2 |
| Top memory | `llm_01689` / `work`：John was offered a programming mentor role for game developers at a non-profit. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01691` | `emotion` | John feels excited and inspired about starting the mentoring journey. |
| `llm_01692` | `preference` | John finds sharing knowledge and seeing others reach their potential rewarding. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 33. audit_020 / q01345

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What game is James hooked on playing on 5 November, 2022? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 23 |
| Top memory | `llm_01618` / `hobby`：John is currently playing 'The Witcher 3' and is hooked on its storytelling and characters. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01724` | `hobby` | John is currently playing FIFA 23, a football game with online multiplayer. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 34. audit_048 / q01924

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | Which city is featured in the photograph Dave showed Calvin? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 2 |
| Top memory | `llm_02380` / `plan`：Calvin and Dave plan to meet up when Calvin is in Boston. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02481` | `event` | Dave took a photograph of a sunset in Boston. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 35. audit_035 / q00667

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What does Joanna do while she writes? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 2 |
| Top memory | `llm_00726` / `preference`：Joanna writes best when being true to herself, even if it's hard. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00838` | `relationship` | Joanna has a stuffed animal dog named Tilly that Nate gave her, and she keeps it with her while writing. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 36. audit_037 / q00900

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | How did "The Alchemist" impact John's perspective on following dreams? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 2 |
| Top memory | `llm_01002` / `preference`：John read and loved 'The Alchemist'. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01076` | `event` | John recently finished rereading 'The Alchemist' and found it inspiring. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 37. audit_030 / q00410

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | How does John plan to honor the memories of his beloved pet? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 13 |
| Top memory | `llm_00508` / `emotion`：John is grieving the loss of his dog Max but finds comfort in memories. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00509` | `goal` | John wants his kids to learn unconditional love and loyalty from the bond with Max. |
| `llm_00510` | `plan` | John is considering adopting a rescue dog to teach his kids responsibility and compassion. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 38. audit_058 / q01136

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What are some of the personalities of Andrew's four fur babies? |
| 自动错误类型 | `persona_confusion` |
| First rank | 3 |
| Top memory | `llm_01289` / `family`：Audrey has four dogs, which she considers her 'fur babies' and says they are more important to her than anything. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01290` | `family` | Audrey's four dogs have distinct personalities: the oldest is relaxed, the second is playful, the third is naughty but cuddly, and the youngest is adventurous. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 39. audit_032 / q00568

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | What activities does Nate do with his turtles? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 4 |
| Top memory | `llm_00663` / `family`：Nate has pet turtles. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00850` | `preference` | Nate enjoys watching his turtles eat fruit because they get excited. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 40. audit_074 / q01884

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What did Calvin and his friends record in August 2023? |
| 自动错误类型 | `semantic_neighbor` |
| First rank | 5 |
| Top memory | `llm_02397` / `event`：Calvin released his album on September 11, 2023. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02381` | `event` | Calvin and his friends recorded a podcast yesterday discussing the rap industry. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 41. audit_026 / q00016

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | What activities does Melanie partake in? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 8 |
| Top memory | `llm_00079` / `hobby`：Melanie and her family enjoy hiking in the mountains and exploring forests. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00042` | `event` | Melanie signed up for a pottery class yesterday. |
| `llm_00080` | `plan` | Melanie went camping with her family two weekends ago. |
| `llm_00010` | `` | Melanie is going swimming with the kids after the conversation. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 42. audit_006 / q00028

| 项目 | 内容 |
|---|---|
| Query type | 3 |
| Query | Would Caroline pursue writing as a career option? |
| 自动错误类型 | `career_education_neighbor` |
| First rank | 5 |
| Top memory | `llm_00045` / `goal`：Caroline is exploring counseling or mental health work as a career. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00058` | `goal` | Caroline is exploring counseling and mental health career options. |
| `llm_00060` | `hobby` | Caroline loves reading and considers books a huge part of her journey. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 43. audit_077 / q00555

| 项目 | 内容 |
|---|---|
| Query type | 2 |
| Query | When did Joanna plan to go over to Nate's and share recipes? |
| 自动错误类型 | `temporal_neighbor` |
| First rank | 6 |
| Top memory | `llm_00718` / `plan`：Joanna and Nate plan to go hiking together sometime. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00863` | `plan` | Joanna plans to visit Nate tomorrow to share desserts and try his lactose-free dessert. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 44. audit_019 / q01169

| 项目 | 内容 |
|---|---|
| Query type | 2 |
| Query | How was John feeling on April 10, 2022? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 377 |
| Top memory | `llm_01116` / `event`：John's favorite basketball game was when his team was down 10 in the 4th and he hit a buzzer-beater shot to win. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01494` | `event` | John visited a canyon two days ago to be alone with nature. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 45. audit_023 / q00071

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | What transgender-specific events has Caroline attended? |
| 自动错误类型 | `identity_neighbor` |
| First rank | 7 |
| Top memory | `llm_00002` / `identity`：Caroline is transgender. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00170` | `event` | Caroline attended a transgender poetry reading last Friday where transgender people shared their stories through poetry. |
| `llm_00171` | `identity` | Caroline is a transgender woman. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 46. audit_061 / q01814

| 项目 | 内容 |
|---|---|
| Query type | 2 |
| Query | Where was Dave in the last two weeks of August 2023? |
| 自动错误类型 | `persona_confusion` |
| First rank | 8 |
| Top memory | `llm_01958` / `event`：Deborah attended a community meetup last Friday (August 25, 2023) where they shared stories. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02365` | `event` | Dave attended a car workshop in San Francisco and was inspired by the passion and dedication of people in car restoration. |
| `llm_02391` | `hobby` | Dave recently returned from San Francisco with insights on car modification. |
| `llm_02392` | `relationship` | Dave is interested in car modification and finds it satisfying to give old cars new life. |
| `llm_02396` | `` |  |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 47. audit_072 / q01670

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What type of car did Evan get after his old Prius broke down? |
| 自动错误类型 | `semantic_neighbor` |
| First rank | 2 |
| Top memory | `llm_02172` / `event`：Evan recently bought a new Prius that broke down. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02023` | `event` | Evan recently bought a new Prius after his old one broke down and he repaired and sold it. |
| `llm_02024` | `` | Evan went on a family trip to the Rockies last week and hiked the trails. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 48. audit_017 / q01052

| 项目 | 内容 |
|---|---|
| Query type | 3 |
| Query | What is something that Andrew could do to make birdwatching hobby to fit in his city schedule? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 54 |
| Top memory | `llm_01356` / `hobby`：Andrew is experienced in birdwatching and offered to give Audrey advice and plan a birdwatching trip together. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01374` | `event` | Andrew had a busy week and played board games with his girlfriend Toby last Tuesday. |
| `llm_01375` | `preference` | Andrew's girlfriend is named Toby. |
| `llm_01178` | `relationship` | Andrew's favorite animal is birds, specifically eagles, which he finds strong and graceful. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 49. audit_003 / q01639

| 项目 | 内容 |
|---|---|
| Query type | 2 |
| Query | Which activity do Evan and Sam plan on doing together during September 2023? |
| 自动错误类型 | `activity_neighbor` |
| First rank | 6 |
| Top memory | `llm_02142` / `plan`：Evan and Sam plan to go on a hike together soon. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02110` | `plan` | Sam and Evan plan to have a painting session next Saturday. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 50. audit_059 / q01316

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What did James create for the charitable foundation that helped generate reports for analysis? |
| 自动错误类型 | `persona_confusion` |
| First rank | 2 |
| Top memory | `llm_01537` / `event`：John volunteered his programming skills for a social cause by creating a software tool for a charitable foundation. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01538` | `event` | John built an application for a charitable foundation to replace paper records and manual inventory tracking, now used on smartphones. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 51. audit_027 / q00056

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | What subject have Caroline and Melanie both painted? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 3 |
| Top memory | `llm_00191` / `relationship`：Caroline and Melanie have a supportive friendship and are there for each other. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00128` | `event` | Caroline has not tried pottery yet. |
| `llm_00068` | `hobby` | Melanie and her kids enjoy painting together, especially nature-inspired paintings. |
| `llm_00069` | `` | Melanie and her kids painted a nature-inspired painting together last weekend. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 52. audit_078 / q01242

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What kind of assignment was giving John a hard time at work? |
| 自动错误类型 | `temporal_neighbor` |
| First rank | 6 |
| Top memory | `llm_00529` / `work`：John tries to organize his time to balance work and family. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01502` | `emotion` | John is currently very busy with work and has many deadlines. |
| `llm_01503` | `work` | John is working on a difficult coding project involving an algorithm and is stuck. |
| `llm_01504` | `` | John hates being stuck and not making progress on his work. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 53. audit_044 / q01741

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | Why did Evan apologize to his partner? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 3 |
| Top memory | `llm_02211` / `identity`：Evan is married to his partner. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02236` | `event` | Evan apologized to his partner for a drunken night involving damage to rose bushes. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 54. audit_055 / q01576

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | Why did Deborah get the new plant on 30 August, 2023? |
| 自动错误类型 | `other` |
| First rank | 8 |
| Top memory | `llm_01958` / `event`：Deborah attended a community meetup last Friday (August 25, 2023) where they shared stories. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01949` | `event` | Jolene recently got a new plant as a reminder to nurture herself and embrace fresh starts. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 55. audit_050 / q00715

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | Who did Joanna plan to invite to her gaming party in June 2022? |
| 自动错误类型 | `other` |
| First rank | 8 |
| Top memory | `llm_00801` / `plan`：Joanna and Nate plan to see each other soon. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00744` | `plan` | Nate is organizing a gaming party two weekends later, inviting tournament friends and old teammates. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 56. audit_029 / q00340

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | What states has Maria vacationed at? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 2 |
| Top memory | `llm_00559` / `hobby`：Maria has been taking regular 'me-time' walks at a nearby park. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00531` | `event` | Maria has a picture from a vacation in Florida with her family, feeling gratitude. |
| `llm_00517` | `` | Maria went on a family road trip to Oregon when she was younger. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 57. audit_004 / q01760

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What sports activity has Sam been doing to stay active while dealing with the knee injury? |
| 自动错误类型 | `activity_neighbor` |
| First rank | 3 |
| Top memory | `llm_02164` / `health`：Sam has been dealing with discomfort that limits his movement. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02094` | `health` | Evan is planning to do physical therapy for his knee and hopes to get an appointment soon. |
| `llm_02095` | `plan` | Evan is swimming to stay active while his knee heals. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 58. audit_002 / q01430

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | Which locations does Deborah practice her yoga at? |
| 自动错误类型 | `activity_neighbor` |
| First rank | 12 |
| Top memory | `llm_01830` / `preference`：Deborah likes candles and essential oils for her yoga practice. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01745` | `event` | Deborah's mother passed away. |
| `llm_01755` | `preference` | Deborah met her new neighbor Anna yesterday at yoga in the park. |
| `llm_01761` | `relationship` | Deborah teaches yoga and spends a lot of time doing so. |
| `llm_01762` | `work` |  |
| `llm_01782` | `` |  |
| `llm_01783` | `` |  |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 59. audit_018 / q01055

| 项目 | 内容 |
|---|---|
| Query type | 2 |
| Query | When did Andrew make his dogs a fun indoor area? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 39 |
| Top memory | `llm_01251` / `preference`：Andrew recommended a doggy daycare near him with a big indoor space for dogs. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01431` | `event` | Andrew plans to take Scout, Toby, and Buddy to a nearby park for Scout's first adventure. |
| `llm_01432` | `plan` | Andrew and his girlfriend are keeping Scout on a leash while he gets used to being outside. |
| `llm_01433` | `` | Andrew and his girlfriend bought essentials for Scout including a bed, toys, and puppy pads. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 60. audit_075 / q00133

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | How long has Melanie been creating art? |
| 自动错误类型 | `temporal_neighbor` |
| First rank | 11 |
| Top memory | `llm_00154` / `hobby`：Melanie has been into art for seven years, focusing on painting and pottery. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00153` | `hobby` | Caroline has been creating art since she was 17. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 61. audit_067 / q00475

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | How long was Max a part of Maria's family? |
| 自动错误类型 | `relationship_neighbor` |
| First rank | 2 |
| Top memory | `llm_00513` / `event`：Maria's pet Max recently died. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00507` | `event` | John's family dog Max died recently after being part of the family for 10 years. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 62. audit_065 / q01789

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | Which types of cars does Dave like the most? |
| 自动错误类型 | `preference_neighbor` |
| First rank | 5 |
| Top memory | `llm_02404` / `hobby`：Dave has a garage with cars that he is proud of. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02271` | `event` | Dave opened his own car maintenance shop. |
| `llm_02272` | `goal` | Dave's dream was to open a car maintenance shop, and he achieved it. |
| `llm_02273` | `hobby` | Dave's next dream is to work on classic cars. |
| `llm_02253` | `work` |  |
| `llm_02267` | `` |  |
| `llm_02274` | `` |  |
| `llm_02275` | `` |  |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 63. audit_068 / q01349

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | Which of Deborah`s family and friends have passed away? |
| 自动错误类型 | `relationship_neighbor` |
| First rank | 4 |
| Top memory | `llm_01988` / `family`：Deborah's mom has passed away. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01729` | `emotion` | Deborah's mother passed away a few years ago. |
| `llm_01739` | `event` | Deborah's father passed away two days before January 27, 2023. |
| `llm_01740` | `family` | Deborah is coping with her father's death by spending time with family and cherishing memories. |
| `llm_01779` | `preference` |  |
| `llm_01780` | `` |  |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 64. audit_070 / q01182

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | What kind of games has James tried to develop? |
| 自动错误类型 | `semantic_neighbor` |
| First rank | 17 |
| Top memory | `llm_01456` / `hobby`：James has been exploring different styles of gaming recently. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01438` | `event` | James is currently enjoying playing The Witcher 3. |
| `llm_01698` | `hobby` | James released his first game for the gaming community recently. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 65. audit_056 / q01803

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | Who inspired Dave's passion for car engineering? |
| 自动错误类型 | `other` |
| First rank | 19 |
| Top memory | `llm_02365` / `event`：Dave attended a car workshop in San Francisco and was inspired by the passion and dedication of people in car restoration. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02348` | `event` | Dave grew up working on cars with his dad, and refurbishing cars is like therapy for him. |
| `llm_02349` | `hobby` | Dave has fond memories of working on cars with his dad as a kid, including one summer spent restoring an old car together. |
| `llm_02472` | `work` | Dave is an automotive engineer. |
| `llm_02473` | `` |  |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 66. audit_013 / q00502

| 项目 | 内容 |
|---|---|
| Query type | 3 |
| Query | What pets wouldn't cause any discomfort to Joanna? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 26 |
| Top memory | `llm_00719` / `health`：Joanna has allergies that prevent her from getting pets. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00638` | `health` | Joanna is allergic to most reptiles and animals with fur, causing puffy and itchy face. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 67. audit_028 / q00314

| 项目 | 内容 |
|---|---|
| Query type | 1 |
| Query | Who gave Maria's family money when she was younger and her family was going through tough times? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 3 |
| Top memory | `llm_00517` / `event`：Maria went on a family road trip to Oregon when she was younger. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00416` | `family` | Maria had financial problems in her youth and relied on help from her auntie. |
| `llm_00410` | `relationship` | Maria started volunteering to make a difference, inspired by her aunt who believed in volunteering and helped her family when struggling. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 68. audit_008 / q00583

| 项目 | 内容 |
|---|---|
| Query type | 3 |
| Query | What kind of job is Joanna beginning to preform the duties of because of her movie scripts? |
| 自动错误类型 | `career_education_neighbor` |
| First rank | 3 |
| Top memory | `llm_00769` / `goal`：Joanna recently started writing a book because her movie did well. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00889` | `goal` | Joanna is filming her own movie based on her road-trip script. |
| `llm_00890` | `work` | Joanna's movie is based on her road-trip script. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 69. audit_033 / q00609

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What are the main ingredients of the ice cream recipe shared by Nate? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 10 |
| Top memory | `llm_00759` / `plan`：Nate promised to give Joanna the vegan ice cream recipe tomorrow. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00688` | `hobby` | Nate makes dairy-free ice cream with coconut milk, vanilla extract, sugar, and a pinch of salt. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 70. audit_041 / q01233

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | What game was James playing in the online gaming tournament in April 2022? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 20 |
| Top memory | `llm_01583` / `event`：James won an online gaming tournament last week. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01480` | `hobby` | James's favorite game is Apex Legends, which he plays with his team. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 71. audit_079 / q01663

| 项目 | 内容 |
|---|---|
| Query type | 2 |
| Query | When did Evan finish the painting that's hanging in the exhibit? |
| 自动错误类型 | `temporal_neighbor` |
| First rank | 2 |
| Top memory | `llm_02083` / `hobby`：Evan started painting years ago after a friend gave him a painting that inspired him. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02189` | `emotion` | Evan finished a contemporary figurative painting a few days ago. |
| `llm_02191` | `hobby` | Evan is proud of his painting. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 72. audit_045 / q01756

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What food did Evan share a photo of on 19 August, 2023? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 3 |
| Top memory | `llm_02082` / `hobby`：Evan started taking painting classes a few days before August 19, 2023. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02079` | `health` | Sam is on a diet and living healthier as of August 2023. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 73. audit_057 / q00982

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What instrument is John learning to play in December 2023? |
| 自动错误类型 | `persona_confusion` |
| First rank | 2 |
| Top memory | `llm_01465` / `hobby`：James is learning an instrument and started a few days ago. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01098` | `hobby` | Tim is learning to play the violin. |
| `llm_01100` | `preference` | Tim is mostly into classical music but wants to try jazz and film scores on the violin. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 74. audit_011 / q00304

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What plans does Gina have after receiving advice at the networking event? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 503 |
| Top memory | `llm_00355` / `event`：Jon attended a networking event where he met investors and got good advice. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00356` | `plan` | Jon is sprucing up his business plan and tweaking his pitch to investors. |
| `llm_00357` | `` | Jon is working on an online platform to showcase the dance studio's offerings. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 75. audit_036 / q00858

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | How long did John and his high school basketball teammates play together? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 2 |
| Top memory | `llm_00949` / `education`：John played basketball through middle and high school and earned a college scholarship. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_00975` | `event` | John played on a high school sports team with friends for four years. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 76. audit_040 / q01164

| 项目 | 内容 |
|---|---|
| Query type | 3 |
| Query | Does James live in Connecticut? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 10 |
| Top memory | `llm_01716` / `relationship`：James and Samantha have decided to move in together. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01482` | `event` | James adopted a puppy from a shelter in Stamford last week and named it Ned. |
| `llm_01483` | `family` | James has a dog named Ned. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 77. audit_021 / q01547

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What cool stuff did Deborah accomplish at the retreat on 9 February, 2023? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 391 |
| Top memory | `llm_01851` / `plan`：Deborah is preparing for a yoga retreat with friends. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01772` | `goal` | Jolene is working on an engineering project and came up with neat solutions. |
| `llm_01773` | `plan` | Jolene is interested in green tech and wants to make a difference in disadvantaged areas. |
| `llm_01774` | `work` | Jolene has an idea for a volunteer program where engineers teach STEM to underprivileged kids. |
| `llm_01775` | `` |  |
| `llm_01776` | `` |  |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 78. audit_043 / q01366

| 项目 | 内容 |
|---|---|
| Query type | 3 |
| Query | In what country did Jolene buy snake Seraphim? |
| 自动错误类型 | `memory_type_mismatch` |
| First rank | 2 |
| Top memory | `llm_01800` / `family`：Jolene has a pet snake named Seraphim. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01749` | `other` | Jolene has a second snake named Seraphim, which she bought a year ago in Paris. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 79. audit_015 / q00973

| 项目 | 内容 |
|---|---|
| Query type | 5 |
| Query | What type of meal does Tim often cook using a slow cooker? |
| 自动错误类型 | `gold_below_top20` |
| First rank | 21 |
| Top memory | `llm_00969` / `family`：Tim's family has a Thanksgiving tradition of preparing a feast, sharing what they're thankful for, and watching movies. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_01046` | `preference` | John often makes honey garlic chicken with roasted vegetables. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

### 80. audit_005 / q01915

| 项目 | 内容 |
|---|---|
| Query type | 4 |
| Query | How does Calvin describe his music in relation to capturing feelings? |
| 自动错误类型 | `activity_neighbor` |
| First rank | 4 |
| Top memory | `llm_02389` / `preference`：Calvin values staying true to himself and being unique in his music. |

**Gold memory**

| Gold ID | Type | Text |
|---|---|---|
| `llm_02463` | `preference` | Calvin uses music as a form of therapy to express himself and work through emotions. |

**待填写**

- `human_auto_reason_correct`: 
- `human_top_memory_relevant`: 
- `human_gold_memory_sufficient`: 
- `human_manual_reason`: 
- `human_auditor_notes`: 

