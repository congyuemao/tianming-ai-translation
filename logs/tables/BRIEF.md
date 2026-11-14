# 对照表采集说明（给分章采集的子代理）

书：Nigel Harris, *The Mandate of Heaven: Marx and Mao in Modern China*（1978；Haymarket 2015 重印）。中文版《天命：马克思与毛泽东在现代中国》。作者是英国国际社会主义派（IS/SWP）的理论家，立场鲜明，文笔尖锐，常用反讽。中文版面向想认真了解这段历史的普通中文读者，润色方针是去翻译腔、按中文骨架重写，可以适度用成语俗语，但不改事实、立场、语气强度，不丢信息，不加作者没有的判断。

这一步**只采集、不改稿**：不要修改 `each_chapter/` 下任何文件。只写下面两个输出文件。

## 输入
- 英文底本：`source/en/<章名>.md`（PDF 文字层抽取，`<!--p.N-->` 标原书页码；注释在章末）。
- 现中文译稿：`each_chapter/<章名>.md`（第8章 `09_...` 已经过一次润色，其余是原译稿）。
- 仓库根目录：`C:\Dev\tianming-ai-translation`。

两份都要从头读完，逐段对照。

## 输出一：成语俗语歇后语对照表 `logs/tables/idioms/<章节前缀>.jsonl`
每行一个 JSON 对象（UTF-8，LF 换行，`ensure_ascii=False`），字段：

```json
{"file":"09_ch08_temporary_contract_labour.md","page":"119","type":"比喻习语","en":"set them at each other's throats","context":"a tactic excellently designed to divide the opposition and set them at each other's throats","meaning":"挑动他们互相争斗、自相残杀","current_zh":"使受压迫者自相残杀","suggest":"窝里斗","alt":["自相残杀","互相掐起来"],"note":"口语，贬义，对象是被分化的反抗者，力度相当；不带额外判断"}
```

- `type` 取值：
  - `比喻习语`：英文本身是比喻、习语、固定搭配、俗语、典故（如 set them at each other's throats, paper tiger, a storm in a teacup, swing into reverse, close ranks, the lion's share, pay lip service）。**这一类要求全收**，一个不漏。
  - `平实可活用`：英文是平实陈述，但有一个中文成语或俗语能分毫不差地表达，且放进去明显更自然（如“换了名字本质没变”→“换汤不换药”）。**这一类要挑**，宁缺毋滥，每章一般不超过 10 条。
- `en` 写表达本身，`context` 写它所在的完整英文句子（过长可截取，保留关键部分）。
- `meaning`：这个说法在本句语境中的确切意思，含褒贬、轻重。
- `current_zh`：现译稿里对应的那几个字到一句话（照抄）。
- `suggest`：推荐用的中文说法（成语、俗语、歇后语，或者干脆是平实的中文，如果找不到贴切的现成说法就写平实译法并在 note 里说明）。`alt`：备选，可空数组。
- `note`：为什么贴切；分寸上的风险（本义是否相符、是否多出判断、褒贬是否一致、是否带中国特有的画面而场景在外国、是否太口语或太文）。

分寸：
- 用之前确认成语的本义、褒贬、轻重，拿不准就不推荐，写平实译法。
- 作者的定义、理论推理处不放成语，比喻放在说理前后。
- 场景在苏联、欧洲、印度等地时，避开中国特有典故（“三顾茅庐”“负荆请罪”之类）。
- 歇后语少用，只在作者语气本身俏皮、放进去不显油滑时推荐。
- 不碰引号里来自中文原始文献的引文（《人民日报》、毛泽东著作、红卫兵报刊等的中文原话）。
- 讽刺、反话不放这里，放进输出二。

## 输出二：讽刺反话对照表 `logs/tables/irony/<章节前缀>.jsonl`
采集作者的反讽、挖苦、说反话、明褒暗贬，以及带讽刺意味的引号用法（如把 “rebels”“leadership”“socialist” 加引号表示不以为然）。字段：

```json
{"file":"09_ch08_temporary_contract_labour.md","page":"125","en":"The source of the trouble afflicting the masses was not the conditions of sweated labour, the dedication of the State to the accumulation of capital, it was a strange psychological weakness, “Economism”, incited by “the handful”.","target":"领导层把群众的不满归咎于思想问题的官方说法","how":"自由间接引语，模仿官方口吻，用 strange psychological weakness 揭露其荒唐","current_zh":"（现译稿对应句，照抄）","literal_zh":"群众受苦的根源，不是血汗劳动的处境，不是国家一心致力于资本积累，而是一种奇怪的心理弱点，即“经济主义”，是“那一小撮人”煽动起来的。","suggest":["群众受苦的根源，不在血汗劳动的处境，也不在国家一门心思积累资本，而在群众自己思想觉悟不高，犯了“经济主义”的毛病，又是“那一小撮人”煽动起来的。"],"risk":"“思想觉悟不高”是当时官方常用语，借来反讽贴切；但原文没有“觉悟”一词，属意译，需加译注"}
```

- `literal_zh`：忠实直译，讽刺靠措辞本身体现，不加“照这个说法”“所谓”之类原文没有的提示语，也不意译。**润色时正文先用这一版。** 现译稿已经很忠实的，可以照抄现译稿再顺一顺语句。
- `suggest`：一到两条意译建议，可以借用当时中国的政治说法（觉悟、路线、挂帅、斗私批修……）或中文里现成的反语说法，让中文读者一读就听出讽刺。不能改变讽刺的对象和力度，不能加作者没有的判断。
- `risk`：意译可能用力过猛、改变意思或需要译注的地方，照实写。
- 只是普通加引号标出专名或官方术语、看不出讽刺的，不收。同一个带讽刺的引号用法（如 “rebels”）在一章里反复出现，只收最典型的一两处，并在 how 里说明“本章多处同样用法”。

## 汇报
写完两个文件后，在最后的回复里只给：每章两类各多少条；你拿不准、希望主控看的条目（文件、页码、一句话原因）；发现的现译稿明显错译（文件、页码、原文→现译，一行一条）。不要在回复里重复表格内容。
