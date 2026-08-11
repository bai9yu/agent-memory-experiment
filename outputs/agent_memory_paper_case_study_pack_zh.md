# 论文 Case Study Pack

本文件从已缓存的 candidate reranker 代表性案例中抽取少量可放入论文 qualitative analysis 的成功、失败和稳定案例。它用于帮助解释主表指标背后的具体排序行为；这些案例仍是自动抽取，不能替代人工错误复核。

## 摘要表

| Bucket | Query | Type | ΔMRR | Base Rank | Rerank Rank | Takeaway |
| --- | --- | --- | --- | --- | --- | --- |
| success_large_gain | q01041 | 1 | 0.9667 | 30 | 1 | 重排器把更具体、答案承载更强的记忆提前，说明 intrinsic candidate features 可以纠正 fixed type-aware 的主题邻近但答案不足问题。 |
| success_large_gain | q01035 | 1 | 0.9630 | 27 | 1 | 重排器把更具体、答案承载更强的记忆提前，说明 intrinsic candidate features 可以纠正 fixed type-aware 的主题邻近但答案不足问题。 |
| success_large_gain | q01655 | 2 | 0.9583 | 24 | 1 | 重排器把更具体、答案承载更强的记忆提前，说明 intrinsic candidate features 可以纠正 fixed type-aware 的主题邻近但答案不足问题。 |
| failure_large_regression | q01837 | 1 | -0.9167 | 1 | 12 | 重排器有时会把语义/实体相邻但答案不足的记忆提前，说明方法仍需更强的 multi-evidence 或 answer-aware objective。 |
| failure_large_regression | q01672 | 4 | -0.9091 | 1 | 11 | 重排器有时会把语义/实体相邻但答案不足的记忆提前，说明方法仍需更强的 multi-evidence 或 answer-aware objective。 |
| failure_large_regression | q00311 | 1 | -0.8889 | 1 | 9 | 重排器有时会把语义/实体相邻但答案不足的记忆提前，说明方法仍需更强的 multi-evidence 或 answer-aware objective。 |
| stable_already_correct | q00006 | 2 | 0.0000 | 1 | 1 | 两种方法都已把 gold memory 排到首位，说明部分 query 主要受候选池质量而非重排策略限制。 |
| stable_already_correct | q00009 | 2 | 0.0000 | 1 | 1 | 两种方法都已把 gold memory 排到首位，说明部分 query 主要受候选池质量而非重排策略限制。 |
| stable_already_correct | q00012 | 1 | 0.0000 | 1 | 1 | 两种方法都已把 gold memory 排到首位，说明部分 query 主要受候选池质量而非重排策略限制。 |

## success_large_gain

### `q01041` / Type 1 / ΔMRR 0.9667

- Query: What are the breeds of Audrey's dogs?
- Baseline top (family, rank 30): Audrey's dogs are her only pets.
- Reranker top (family, rank 1): Audrey has four dogs, all mutts: two Jack Russell mixes and two Chihuahua mixes.
- Gold (family): Audrey has four dogs, all mutts: two Jack Russell mixes and two Chihuahua mixes. || Audrey has four dogs: Pepper, Panda, Precious, and Pixie. || Audrey: Pepper and Panda are Lab mixes, and Precious and Pixie are Chihuahua mixes.
- Paper takeaway: 重排器把更具体、答案承载更强的记忆提前，说明 intrinsic candidate features 可以纠正 fixed type-aware 的主题邻近但答案不足问题。

### `q01035` / Type 1 / ΔMRR 0.9630

- Query: What are the names of Andrew's dogs?
- Baseline top (relationship, rank 27): Audrey and Andrew are friends who enjoy outdoor activities with their dogs.
- Reranker top (family, rank 1): Andrew recently adopted a puppy named Toby.
- Gold (event|family|identity): Andrew recently adopted a puppy named Toby. || Andrew lives in a city. || Andrew named his new puppy Buddy.
- Paper takeaway: 重排器把更具体、答案承载更强的记忆提前，说明 intrinsic candidate features 可以纠正 fixed type-aware 的主题邻近但答案不足问题。

### `q01655` / Type 2 / ΔMRR 0.9583

- Query: What was Sam doing on December 4, 2023?
- Baseline top (health, rank 24): Sam is on a diet and living healthier as of August 2023.
- Reranker top (event, rank 1): Sam attended a Weight Watchers meeting yesterday.
- Gold (event): Sam attended a Weight Watchers meeting yesterday.
- Paper takeaway: 重排器把更具体、答案承载更强的记忆提前，说明 intrinsic candidate features 可以纠正 fixed type-aware 的主题邻近但答案不足问题。

## failure_large_regression

### `q01837` / Type 1 / ΔMRR -0.9167

- Query: What does help Calvin stay connected to the creative process?
- Baseline top (preference, rank 1): Calvin usually watches music videos, concerts, and documentaries about artists and their creative process on TV.
- Reranker top (event, rank 12): Calvin had an inspiring conversation with an artist at the gala, bonding over music and art.
- Gold (preference): Calvin values staying connected and up-to-date on world events to inspire his music and connect with fans. || Calvin usually watches music videos, concerts, and documentaries about artists and their creative process on TV.
- Paper takeaway: 重排器有时会把语义/实体相邻但答案不足的记忆提前，说明方法仍需更强的 multi-evidence 或 answer-aware objective。

### `q01672` / Type 4 / ΔMRR -0.9091

- Query: What did Evan start doing a few years back as a stress-buster?
- Baseline top (hobby, rank 1): Evan has been doing watercolor painting for a few years and got into it through a friend.
- Reranker top (plan, rank 11): Evan is considering trying yoga for stress relief and flexibility.
- Gold (hobby): Evan has been doing watercolor painting for a few years and got into it through a friend.
- Paper takeaway: 重排器有时会把语义/实体相邻但答案不足的记忆提前，说明方法仍需更强的 multi-evidence 或 answer-aware objective。

### `q00311` / Type 1 / ΔMRR -0.8889

- Query: Where has Maria made friends?
- Baseline top (relationship, rank 1): Maria is now friends with one of her fellow volunteers.
- Reranker top (work, rank 9): Maria volunteers at a homeless shelter.
- Gold (event|hobby|other|relationship): Maria is now friends with one of her fellow volunteers. || Maria donated her old car to a homeless shelter she volunteers at yesterday. || Maria volunteers at a homeless shelter.
- Paper takeaway: 重排器有时会把语义/实体相邻但答案不足的记忆提前，说明方法仍需更强的 multi-evidence 或 answer-aware objective。

## stable_already_correct

### `q00006` / Type 2 / ΔMRR 0.0000

- Query: When did Melanie run a charity race?
- Baseline top (event, rank 1): Melanie ran a charity race for mental health last Saturday.
- Reranker top (event, rank 1): Melanie ran a charity race for mental health last Saturday.
- Gold (event): Melanie ran a charity race for mental health last Saturday.
- Paper takeaway: 两种方法都已把 gold memory 排到首位，说明部分 query 主要受候选池质量而非重排策略限制。

### `q00009` / Type 2 / ΔMRR 0.0000

- Query: When did Caroline give a speech at a school?
- Baseline top (event, rank 1): Caroline gave a talk at a school event last week about her transgender journey and encouraged students to get involved in the LGBTQ community.
- Reranker top (event, rank 1): Caroline gave a talk at a school event last week about her transgender journey and encouraged students to get involved in the LGBTQ community.
- Gold (event|identity): Caroline is a transgender woman who started transitioning three years ago. || Caroline gave a talk at a school event last week about her transgender journey and encouraged students to get involved in the LGBTQ community.
- Paper takeaway: 两种方法都已把 gold memory 排到首位，说明部分 query 主要受候选池质量而非重排策略限制。

### `q00012` / Type 1 / ΔMRR 0.0000

- Query: Where did Caroline move from 4 years ago?
- Baseline top (relationship, rank 1): Caroline has known her close friends for 4 years, since she moved from her home country.
- Reranker top (relationship, rank 1): Caroline has known her close friends for 4 years, since she moved from her home country.
- Gold (emotion|family|identity|relationship): Caroline has known her close friends for 4 years, since she moved from her home country. || Caroline went through a tough breakup, and her friends' support was especially important during that time. || Caroline is from Sweden.
- Paper takeaway: 两种方法都已把 gold memory 排到首位，说明部分 query 主要受候选池质量而非重排策略限制。

## 论文写法边界

- 可以写：这些案例展示了 intrinsic reranker 的典型成功模式和失败边界。
- 应谨慎：案例由脚本自动抽取，未经过人工确认；论文中应称为 illustrative examples，而不是 human-verified error analysis。
- 不能写：这些案例已经证明错误分析经过人工验证，或 Type 3 多证据问题已经解决。
