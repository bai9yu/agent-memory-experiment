# Candidate Reranker 按 Query Type 分析

本报告基于 held-out split 的 paired comparison，分析 candidate reranker 相比 fixed `type_aware` 在不同 LoCoMo query type 上的收益和失败案例。

## By Query Type

| Query Type | Pairs | Base MRR | Reranker MRR | Delta MRR | Base R@1 | Reranker R@1 | Base R@5 | Reranker R@5 | Improved | Worsened | Tied |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Type 1 | 413 | 0.508 | 0.537 | 0.0288 | 0.373 | 0.404 | 0.661 | 0.707 | 116 | 131 | 166 |
| Type 2 | 466 | 0.714 | 0.766 | 0.0522 | 0.614 | 0.661 | 0.833 | 0.895 | 87 | 39 | 340 |
| Type 3 | 126 | 0.439 | 0.419 | -0.0194 | 0.341 | 0.349 | 0.548 | 0.492 | 25 | 54 | 47 |
| Type 4 | 1096 | 0.667 | 0.718 | 0.0515 | 0.561 | 0.618 | 0.793 | 0.846 | 257 | 125 | 714 |
| Type 5 | 659 | 0.524 | 0.613 | 0.0887 | 0.423 | 0.513 | 0.645 | 0.756 | 206 | 149 | 304 |

## Interpretation

- 若某类 query 的 Delta MRR 明显为正，说明 candidate-level reranker 能从多检索器候选中学到比固定公式更细的排序边界。
- 若某类 query 的 Worsened 数量较高，需要重点检查 top memory 是否过度依赖某个检索器分数，或 gold memory 是否没有进入候选池。
- 这些结果可用于论文中的细粒度分析表和失败案例小节。

## Representative Cases

### improved / Type 1 / `q01041` / seed 23

- Query: What are the breeds of Audrey's dogs?
- Delta MRR: `0.9667`; baseline rank `30`, reranker rank `1`
- Baseline top: `llm_01350` (family) Audrey's dogs are her only pets.
- Reranker top: `llm_01342` (family) Audrey has four dogs, all mutts: two Jack Russell mixes and two Chihuahua mixes.
- Gold: Audrey has four dogs, all mutts: two Jack Russell mixes and two Chihuahua mixes. || Audrey has four dogs: Pepper, Panda, Precious, and Pixie. || Audrey: Pepper and Panda are Lab mixes, and Precious and Pixie are Chihuahua mixes.

### improved / Type 1 / `q01035` / seed 17

- Query: What are the names of Andrew's dogs?
- Delta MRR: `0.9630`; baseline rank `27`, reranker rank `1`
- Baseline top: `llm_01415` (relationship) Audrey and Andrew are friends who enjoy outdoor activities with their dogs.
- Reranker top: `llm_01276` (family) Andrew recently adopted a puppy named Toby.
- Gold: Andrew recently adopted a puppy named Toby. || Andrew lives in a city. || Andrew named his new puppy Buddy.

### improved / Type 2 / `q01655` / seed 17

- Query: What was Sam doing on December 4, 2023?
- Delta MRR: `0.9583`; baseline rank `24`, reranker rank `1`
- Baseline top: `llm_02079` (health) Sam is on a diet and living healthier as of August 2023.
- Reranker top: `llm_02175` (event) Sam attended a Weight Watchers meeting yesterday.
- Gold: Sam attended a Weight Watchers meeting yesterday.

### improved / Type 3 / `q00566` / seed 31

- Query: How many hikes has Joanna been on?
- Delta MRR: `0.9444`; baseline rank `18`, reranker rank `1`
- Baseline top: `llm_00672` (preference) Joanna's go-to place for writing inspiration is a place with many books.
- Reranker top: `llm_00713` (event) Joanna took a photo at Whispering Falls during her hike.
- Gold: Joanna recently went hiking and saw a gorgeous sunset. || Joanna took a photo at Whispering Falls during her hike. || Joanna took a sunset photo on a hike last summer near Fort Wayne.

### improved / Type 4 / `q01254` / seed 23

- Query: Which football club does John support?
- Delta MRR: `0.9375`; baseline rank `16`, reranker rank `1`
- Baseline top: `llm_00473` (relationship) John's family is his biggest support system.
- Reranker top: `llm_01559` (preference) John is a Manchester City fan.
- Gold: John is a Manchester City fan.

### improved / Type 4 / `q01439` / seed 29

- Query: What music pieces does Deborah listen to during her yoga practice?
- Delta MRR: `0.9333`; baseline rank `15`, reranker rank `1`
- Baseline top: `llm_01828` (hobby) Deborah bought a candle to improve her yoga practice.
- Reranker top: `llm_01832` (preference) Deborah likes instrumental tracks with mellow melodies for yoga, and one favorite is 'Savana'.
- Gold: Deborah likes instrumental tracks with mellow melodies for yoga, and one favorite is 'Savana'. || Deborah recommends the album 'Sleep' for meditation and deep relaxation.

### improved / Type 5 / `q01582` / seed 31

- Query: Where did Jolene get married?
- Delta MRR: `0.9286`; baseline rank `14`, reranker rank `1`
- Baseline top: `llm_01770` (event) Jolene did a mini retreat last Wednesday to assess where she is in life.
- Reranker top: `llm_01990` (hobby) Deborah discovered her love for surfing at the beach where she got married.
- Gold: Deborah got married at a beach that is special to her. || Deborah discovered her love for surfing at the beach where she got married.

### worsened / Type 1 / `q01837` / seed 13

- Query: What does help Calvin stay connected to the creative process?
- Delta MRR: `-0.9167`; baseline rank `1`, reranker rank `12`
- Baseline top: `llm_02492` (preference) Calvin usually watches music videos, concerts, and documentaries about artists and their creative process on TV.
- Reranker top: `llm_02510` (event) Calvin had an inspiring conversation with an artist at the gala, bonding over music and art.
- Gold: Calvin values staying connected and up-to-date on world events to inspire his music and connect with fans. || Calvin usually watches music videos, concerts, and documentaries about artists and their creative process on TV.

### improved / Type 2 / `q00516` / seed 13

- Query: Which outdoor spot did Joanna visit in May?
- Delta MRR: `0.9091`; baseline rank `11`, reranker rank `1`
- Baseline top: `llm_00769` (goal) Joanna recently started writing a book because her movie did well.
- Reranker top: `llm_00713` (event) Joanna took a photo at Whispering Falls during her hike.
- Gold: Joanna took a photo at Whispering Falls during her hike.

### worsened / Type 4 / `q01672` / seed 17

- Query: What did Evan start doing a few years back as a stress-buster?
- Delta MRR: `-0.9091`; baseline rank `1`, reranker rank `11`
- Baseline top: `llm_02027` (hobby) Evan has been doing watercolor painting for a few years and got into it through a friend.
- Reranker top: `llm_02174` (plan) Evan is considering trying yoga for stress relief and flexibility.
- Gold: Evan has been doing watercolor painting for a few years and got into it through a friend.

### improved / Type 5 / `q01129` / seed 29

- Query: How did Andrew describe the dog he met at the pet store?
- Delta MRR: `0.9091`; baseline rank `11`, reranker rank `1`
- Baseline top: `llm_01185` (goal) Andrew is considering getting a dog.
- Reranker top: `llm_01225` (event) Audrey found the workshop flyer at her local pet store.
- Gold: Audrey found the workshop flyer at her local pet store. || Audrey: The workshop Audrey signed up for is a positive reinforcement training class.

### worsened / Type 1 / `q00311` / seed 13

- Query: Where has Maria made friends?
- Delta MRR: `-0.8889`; baseline rank `1`, reranker rank `9`
- Baseline top: `llm_00397` (relationship) Maria is now friends with one of her fellow volunteers.
- Reranker top: `llm_00438` (work) Maria volunteers at a homeless shelter.
- Gold: Maria is now friends with one of her fellow volunteers. || Maria donated her old car to a homeless shelter she volunteers at yesterday. || Maria volunteers at a homeless shelter.

### worsened / Type 3 / `q00811` / seed 23

- Query: What other exercises can help John with his basketball performance?
- Delta MRR: `-0.8750`; baseline rank `1`, reranker rank `8`
- Baseline top: `llm_00962` (plan) John adapted his workout routine to balance basketball and strength training.
- Reranker top: `llm_01165` (preference) John is interested in basketball and believes it brings people together and creates positive impact.
- Gold: John recently found a new gym to stay fit for professional basketball. || John adapted his workout routine to balance basketball and strength training. || John is trying yoga to gain extra strength and flexibility.

### worsened / Type 3 / `q00811` / seed 13

- Query: What other exercises can help John with his basketball performance?
- Delta MRR: `-0.8000`; baseline rank `1`, reranker rank `5`
- Baseline top: `llm_00962` (plan) John adapted his workout routine to balance basketball and strength training.
- Reranker top: `llm_01154` (hobby) John practices basketball every day to stay in shape and improve.
- Gold: John recently found a new gym to stay fit for professional basketball. || John adapted his workout routine to balance basketball and strength training. || John is trying yoga to gain extra strength and flexibility.

### worsened / Type 5 / `q01944` / seed 13

- Query: What type of cars does Calvin work on at his shop?
- Delta MRR: `-0.7500`; baseline rank `1`, reranker rank `4`
- Baseline top: `llm_02277` (plan) Dave invited Calvin to visit his shop.
- Reranker top: `llm_02273` (goal) Dave's next dream is to work on classic cars.
- Gold: Dave's shop handles regular maintenance and full restorations of classic cars. || Dave invited Calvin to visit his shop.

### worsened / Type 5 / `q01555` / seed 29

- Query: Who are the authors mentioned by Jolene that she enjoys reading during her yoga practice?
- Delta MRR: `-0.7500`; baseline rank `1`, reranker rank `4`
- Baseline top: `llm_01831` (preference) Jolene likes listening to Nils Frahm and Olafur Arnalds during yoga.
- Reranker top: `llm_01828` (hobby) Deborah bought a candle to improve her yoga practice.
- Gold: Jolene likes listening to Nils Frahm and Olafur Arnalds during yoga.

### worsened / Type 2 / `q01795` / seed 23

- Query: When was Calvin's concert in Tokyo?
- Delta MRR: `-0.6667`; baseline rank `1`, reranker rank `3`
- Baseline top: `llm_02296` (event) Calvin has an upcoming music performance in Tokyo this month.
- Reranker top: `llm_02450` (event) Calvin performed in Tokyo during the tour and found the crowd energy amazing.
- Gold: Calvin has an upcoming music performance in Tokyo this month. || Calvin toured with Frank Ocean last week, including a performance in Tokyo. || Calvin felt alive and energized performing in Tokyo, describing the crowd as insane.

### worsened / Type 4 / `q00265` / seed 13

- Query: What book is Jon currently reading?
- Delta MRR: `-0.5000`; baseline rank `1`, reranker rank `2`
- Baseline top: `llm_00297` (hobby) Jon is reading 'The Lean Startup' to get tips for his business.
- Reranker top: `llm_01029` (hobby) Tim is currently reading a book and is hooked on it.
- Gold: Jon is reading 'The Lean Startup' to get tips for his business.

### improved / Type 3 / `q01193` / seed 13

- Query: What additional country did James visit during his trip to Canada?
- Delta MRR: `0.5000`; baseline rank `2`, reranker rank `1`
- Baseline top: `llm_01589` (plan) James plans to visit Vancouver in addition to Toronto.
- Reranker top: `llm_01599` (event) James recently traveled to Nuuk, adding another country to his bucket list.
- Gold: James recently traveled to Nuuk, adding another country to his bucket list.

### worsened / Type 2 / `q00216` / seed 13

- Query: When did Jon go to a fair to get more exposure for his dance studio?
- Delta MRR: `-0.1905`; baseline rank `3`, reranker rank `7`
- Baseline top: `llm_00285` (event) Jon lost his job, which motivated him to start his dance studio.
- Reranker top: `llm_00285` (event) Jon lost his job, which motivated him to start his dance studio.
- Gold: Jon attended a fair yesterday to showcase his studio and got some possible leads. || Jon runs a business (studio) and finds it challenging, learning that confidence is important for success.

### tied / Type 2 / `q00006` / seed 13

- Query: When did Melanie run a charity race?
- Delta MRR: `0.0000`; baseline rank `1`, reranker rank `1`
- Baseline top: `llm_00011` (event) Melanie ran a charity race for mental health last Saturday.
- Reranker top: `llm_00011` (event) Melanie ran a charity race for mental health last Saturday.
- Gold: Melanie ran a charity race for mental health last Saturday.

### tied / Type 2 / `q00009` / seed 13

- Query: When did Caroline give a speech at a school?
- Delta MRR: `0.0000`; baseline rank `1`, reranker rank `1`
- Baseline top: `llm_00020` (event) Caroline gave a talk at a school event last week about her transgender journey and encouraged students to get involved in the LGBTQ community.
- Reranker top: `llm_00020` (event) Caroline gave a talk at a school event last week about her transgender journey and encouraged students to get involved in the LGBTQ community.
- Gold: Caroline is a transgender woman who started transitioning three years ago. || Caroline gave a talk at a school event last week about her transgender journey and encouraged students to get involved in the LGBTQ community.

### tied / Type 1 / `q00012` / seed 13

- Query: Where did Caroline move from 4 years ago?
- Delta MRR: `0.0000`; baseline rank `1`, reranker rank `1`
- Baseline top: `llm_00022` (relationship) Caroline has known her close friends for 4 years, since she moved from her home country.
- Reranker top: `llm_00022` (relationship) Caroline has known her close friends for 4 years, since she moved from her home country.
- Gold: Caroline has known her close friends for 4 years, since she moved from her home country. || Caroline went through a tough breakup, and her friends' support was especially important during that time. || Caroline is from Sweden.

### tied / Type 3 / `q00060` / seed 13

- Query: Would Caroline be considered religious?
- Delta MRR: `0.0000`; baseline rank `1`, reranker rank `1`
- Baseline top: `llm_00107` (event) Caroline recently had a negative experience on a hike when she encountered religious conservatives who upset her, making her think about the work needed for LGBTQ rights.
- Reranker top: `llm_00107` (event) Caroline recently had a negative experience on a hike when she encountered religious conservatives who upset her, making her think about the work needed for LGBTQ rights.
- Gold: Caroline is a transgender woman. || Caroline made a stained glass window for a local church, inspired by her journey as a transgender woman. || Caroline recently had a negative experience on a hike when she encountered religious conservatives who upset her, making her think about the work needed for LGBTQ rights.

