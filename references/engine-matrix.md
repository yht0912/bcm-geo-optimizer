# Engine Matrix

## General rule

Use official data and observed answers when available. Provider behavior changes; verify current documentation before implementing provider-specific assumptions.

| Surface | Primary evidence | High-value checks | Common overclaim |
|---|---|---|---|
| Google Search / AI surfaces | Search Console readback, public results, observed AI answer | index coverage, canonical, structured facts, source quality | submission equals index or AI use |
| Microsoft Bing / Copilot | Webmaster readback, IndexNow receipt, public results, observed answer | crawl/index state, entity consistency, cited sources | IndexNow receipt equals ranking |
| Baidu | resource platform readback, public results, observed answer | verification, crawl/index signals, mobile/public accessibility | push success equals inclusion |
| Other domestic search engines | official console where available, public result sampling | ownership, sitemap, crawl access, regional performance | verified site equals traffic |
| ChatGPT | observed answer with provider/model/time, referral analytics | source citations, entity and decision facts, repeatability | one mention equals stable recommendation |
| Claude | observed answer with provider/model/time | answer usefulness, cited evidence when surfaced | generated answer equals indexed knowledge |
| Gemini | observed answer and source links | Google ecosystem retrieval, source clarity, freshness | Search Console data proves Gemini use |
| Perplexity | observed answer and cited URLs | citation eligibility, concise proof, source diversity | citation alone equals endorsement |

## Provider-independent tests

For each chosen engine:

1. Can it access the public page?
2. Can official tools confirm ownership and provide real data readback?
3. Is the intended canonical page discoverable and indexed?
4. Does the observed answer mention, cite, recommend, reject, or omit the brand?
5. Which sources and selection criteria appear in that answer?
6. Does the cited page convert the intended visitor?

## Freshness

Record collection time and verify current platform documentation before changing APIs, authentication, or submission methods. Do not hard-code assumptions about provider crawling, training, retrieval, or ranking.
