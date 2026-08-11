# priority20 人工复核阅读包

本阅读包由盲审 CSV 自动生成，只展示人工判断所需的 query、自动错误类型、Top memory 和 gold memory；不展示 LLM-assisted 预标注，避免人工复核被模型标签锚定。

## 使用方式

- 源盲审表：`outputs/agent_memory_human_audit_priority20_blind_review.csv`
- 样本数：20
- 已完整填写：0/20
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
| 1 | audit_050 | q00715 |  |  |  |  |
| 2 | audit_076 | q00520 |  |  |  |  |
| 3 | audit_020 | q01345 |  |  |  |  |
| 4 | audit_031 | q00459 |  |  |  |  |
| 5 | audit_002 | q01430 |  |  |  |  |
| 6 | audit_007 | q00442 |  |  |  |  |
| 7 | audit_051 | q01147 |  |  |  |  |
| 8 | audit_056 | q01803 |  |  |  |  |
| 9 | audit_055 | q01576 |  |  |  |  |
| 10 | audit_069 | q01772 |  |  |  |  |
| 11 | audit_025 | q00970 |  |  |  |  |
| 12 | audit_077 | q00555 |  |  |  |  |
| 13 | audit_075 | q00133 |  |  |  |  |
| 14 | audit_010 | q00183 |  |  |  |  |
| 15 | audit_045 | q01756 |  |  |  |  |
| 16 | audit_034 | q00645 |  |  |  |  |
| 17 | audit_019 | q01169 |  |  |  |  |
| 18 | audit_040 | q01164 |  |  |  |  |
| 19 | audit_009 | q00889 |  |  |  |  |
| 20 | audit_006 | q00028 |  |  |  |  |

## 样本卡片

### 1. audit_050 / q00715

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

### 2. audit_076 / q00520

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

### 3. audit_020 / q01345

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

### 4. audit_031 / q00459

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

### 5. audit_002 / q01430

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

### 6. audit_007 / q00442

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

### 7. audit_051 / q01147

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

### 8. audit_056 / q01803

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

### 9. audit_055 / q01576

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

### 10. audit_069 / q01772

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

### 11. audit_025 / q00970

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

### 12. audit_077 / q00555

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

### 13. audit_075 / q00133

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

### 14. audit_010 / q00183

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

### 15. audit_045 / q01756

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

### 16. audit_034 / q00645

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

### 17. audit_019 / q01169

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

### 18. audit_040 / q01164

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

### 19. audit_009 / q00889

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

### 20. audit_006 / q00028

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

