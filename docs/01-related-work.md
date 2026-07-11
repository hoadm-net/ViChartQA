# 01 — Bối cảnh & rà soát công trình liên quan

Rà soát thực hiện 07/2026. Mục tiêu: xác định chính xác ViChartQA khác gì với các công trình gần nhất, để phần Related Work của bài báo không bị reviewer A* bác vì "chỉ là bản dịch ChartQA" hoặc "trùng ViInfographicVQA".

> **Trạng thái verify:** toàn bộ số liệu trong file này đã được đối chiếu trực tiếp với bản PDF gốc trên arXiv (tải về, `pdftotext`, đọc trực tiếp bảng số liệu — không dùng tóm tắt search engine) vào 11/07/2026. Vòng verify đầu tiên phát hiện một lỗi đáng kể ở ChartBench (đã sửa, xem ghi chú trong bảng) — chi tiết phương pháp verify xem cuối file.

## 1. Dòng Chart QA tiếng Anh

| Bộ dữ liệu | Nguồn ảnh | Quy mô | Kiểu câu hỏi | Năm |
|---|---|---|---|---|
| FigureQA | Vẽ tự động (Matplotlib) | 180K chart / 2.3M QA | Template, từ vựng cố định | 2017 |
| DVQA | Vẽ tự động | 300K chart / 3.4M QA | Template, từ vựng cố định | 2018 |
| PlotQA | Vẽ tự động | 224K chart / 28M QA | Template, từ vựng mở | 2020 |
| ChartQA | Statista, Pew, OWID, OECD (thực tế) | 20.9K chart / 32.7K QA | Người viết + sinh bằng T5; compositional + visual | 2022 |
| ChartX / ChartVLM | GPT-4 sinh code vẽ hàng loạt | bộ eval 6K chart · 18 loại chart · 7 tác vụ · 22 chủ đề | QA + caption + trích xuất, đa tác vụ | 2024 |
| CharXiv | Bài báo khoa học trên arXiv | 2,323 chart (1.000 val + 1.323 test), 1 câu hỏi suy luận + nhiều câu hỏi mô tả/chart | Mô tả (descriptive) + suy luận (reasoning) | 2024 |
| ChartBench | Tổng hợp, 42 danh mục chart | **toàn bộ: 66.624 chart / ≈600K QA** (train); **riêng test set: 2.100 chart / 18.900 QA** — 2 số này dễ nhầm lẫn, xem ghi chú ⚠️ bên dưới | Acc+ (đúng/sai 2 chiều) + Number QA | 2023–24 |
| ChartQAPro | 157 nền tảng web (thực tế) | 1.341 chart / 1.948 QA | 6 loại: factoid, trắc nghiệm, hội thoại, giả định, fact-check, không trả lời được | 2025 |
| FinChart-Bench | Biểu đồ tài chính thực tế (2015–2024) | 1.200 chart / 7.016 QA (True/False + trắc nghiệm + QA), 25 LVLM được đánh giá | Đa dạng, thiên suy luận tài chính | 2025 |

> ⚠️ **Lỗi đã sửa (11/07/2026):** bản rà soát trước đây trình bày "2.1K chart / 18.9K QA" như thể là quy mô **toàn bộ** ChartBench — thực ra đây chỉ là **tập test**. Toàn bộ dataset (train+test) lớn hơn ~30 lần: 66.624 chart / ≈600K QA (nguồn: Table 9 và Table 10, ChartBench paper, arXiv:2312.15915). Nếu trích ChartBench trong bài, ghi rõ đang nói đến số nào.

**Quan sát quan trọng nhất:** ChartQA gốc (2022) đã gần bão hoà ở một số mô hình mạnh — theo ChartQAPro (arXiv:2504.05506, đã đọc trực tiếp), **Claude Sonnet 3.5 đạt 90.50% trên ChartQA** nhưng chỉ còn **55.81% trên ChartQAPro**. Các benchmark 2024–2025 (CharXiv, ChartQAPro, FinChart-Bench) đều được thiết kế lại để *khó hơn*, thường bằng cách:

- Dùng chart thực tế "trong tự nhiên" thay vì crawl từ vài nguồn quen thuộc (CharXiv dùng arXiv, ChartQAPro dùng 157 nền tảng web khác nhau).
- Đa dạng hoá **định dạng câu hỏi**, không chỉ factoid: trắc nghiệm, giả định ("nếu xu hướng tiếp diễn..."), fact-checking (đúng/sai một phát biểu), hội thoại nhiều lượt, và câu hỏi cố tình không trả lời được từ chart.
- Kết quả trên ChartQAPro: GPT-4o đạt 37.67%, Claude Sonnet 3.5 đạt 55.81% (giảm từ 90.50% trên ChartQA). Baseline người đạt 85.02%. Tương tự, CharXiv cho thấy GPT-4o chỉ đạt 47.1% trên câu hỏi suy luận (so với 84.5% ở câu hỏi mô tả đơn giản), human 80.5%/92.1%.

**Hệ quả cho ViChartQA:** nếu chỉ dịch nguyên taxonomy ChartQA 2022 sang tiếng Việt, benchmark có nguy cơ bị đánh giá là lỗi thời ngay từ vòng review. Taxonomy câu hỏi phải học theo hướng ChartQAPro (xem [docs/02-dataset-design.md](02-dataset-design.md#taxonomy-câu-hỏi)).

## 2. Dòng chart-VLM chuyên biệt (mô hình)

| Mô hình | Backbone | Ý tưởng chính |
|---|---|---|
| ChartLlama | LLaVA-1.5 | Pipeline nhiều bước dùng GPT-4 sinh dữ liệu instruction (bảng số liệu → ảnh chart → câu hỏi) |
| ChartGemma | PaliGemma (nhỏ) | Sinh dữ liệu instruction trực tiếp từ ảnh chart; mô hình nhỏ nhưng cạnh tranh |
| TinyChart | LLaVA-based, 3B tham số | Token-merging cho ảnh độ phân giải cao + Program-of-Thought (sinh code Python để tính toán); vượt cả ChartLlama/ChartAst (13B) và GPT-4V trên ChartQA. EMNLP 2024 |
| ChartMoE | InternLM-XComposer + Mixture-of-Experts connector | Nâng SOTA trên ChartQA từ 80.48% lên **84.64%**; kèm bộ dữ liệu ChartMoE-Align (~1 triệu bộ chart-table-JSON-code) |
| Chart-R1 / Chart-RVR / Chart-RL | Nhiều backbone khác nhau | RL với phần thưởng có thể kiểm chứng (RLVR) cho suy luận chart — xu hướng nổi lên 2025–2026 (chưa đọc sâu từng bài, chỉ xác nhận tồn tại xu hướng qua tiêu đề/abstract) |

**Điểm chung:** không mô hình nào huấn luyện từ đầu — tất cả fine-tune một VLM backbone có sẵn. Xu hướng mới nhất (Chart-R1/RVR/RL) chuyển từ SFT thuần sang **RL với phần thưởng kiểm chứng được** (đáp án số có thể so khớp tự động), tận dụng đúng đặc điểm của chart QA là nhiều câu trả lời có thể verify bằng heuristic. Đây là lý do ViChartQA nên giữ lại/công bố kèm **bảng dữ liệu gốc** của mỗi chart (xem [docs/02](02-dataset-design.md)) — vừa hỗ trợ đánh giá, vừa mở đường cho hướng RLVR nếu nhóm có thời gian.

## 3. Dòng VQA / đa phương thức tiếng Việt

| Bộ dữ liệu | Miền ảnh | Quy mô | Đặc điểm | Năm |
|---|---|---|---|---|
| ViVQA | Ảnh tổng quát (nguồn ảnh từ MS COCO, câu hỏi tiếng Việt) | 10.328 ảnh / 15.000 QA | Hierarchical Co-Attention baseline, Accuracy 0.3496 | 2021 |
| EVJVQA | Ảnh chụp tại Việt Nam | 5.000 ảnh / 33.000+ QA | 3 ngôn ngữ VI/EN/JA, shared task VLSP 2022, 62 đội tham gia | 2022 |
| OpenViVQA | Ảnh tổng quát (thu thập qua Google search) | 11.199 ảnh / 37.914 QA | Câu trả lời mở, viết tay hoàn toàn (không dịch máy) | 2023 |
| ViOCRVQA / ViTextVQA | Ảnh có chữ (biển hiệu, tài liệu) | quy mô vừa–lớn | Đọc hiểu văn bản trong ảnh, thiên về OCR | 2024 |
| VMMU | Đa nhiệm: STEM, biểu diễn dữ liệu, suy luận thị giác | 2.5K QA / 7 tác vụ | Proprietary VLM mạnh nhất chỉ ~66%; nghẽn ở suy luận đa phương thức, **không phải** OCR | 2025 |
| ViInfographicVQA | Infographic (kinh tế, y tế, xã hội…) | 6.7K ảnh / 20.4K QA | Pipeline VLM hỗ trợ trích xuất vùng (text box, chart, icon) + xác minh người; có cả single-image và multi-image reasoning | 2025 |

### So sánh trực tiếp với ViInfographicVQA

Đây là công trình gần nhất về mặt miền dữ liệu (kinh tế nằm trong 5 chủ đề của ViInfographicVQA) và quy trình gán nhãn (VLM-assisted + xác minh người — ViChartQA sẽ dùng cùng triết lý pipeline, xem docs/02). Khác biệt cần làm rõ trong bài:

- **Đơn vị ảnh khác nhau về bản chất.** Infographic là bố cục hỗn hợp (icon, khối văn bản, chart nhỏ, trang trí) — câu hỏi chủ yếu là đọc-trích xuất (span-based, ANLS ~71–75% cho câu dạng trích xuất). Chart là một cấu trúc dữ liệu có trục/chuỗi/mốc rõ ràng — câu hỏi đòi hỏi *tính toán trên dữ liệu* (tổng, hiệu, so sánh xu hướng), không chỉ trích xuất.
- **Miền hẹp hơn nhưng sâu hơn.** ViInfographicVQA phủ 5 chủ đề rộng (kinh tế, y tế, văn hoá-xã hội, thiên tai, thể thao-nghệ thuật). ViChartQA chỉ tập trung khoa học + kinh tế nhưng đào sâu suy luận số học/logic trên từng chart — gần với triết lý ChartQA gốc hơn là InfographicVQA gốc.
- **Không trùng lặp nguồn ảnh nếu chọn đúng.** ViInfographicVQA lấy từ infographics.vn (Thông tấn xã Việt Nam). ViChartQA nên ưu tiên nguồn khác (GSO, báo cáo khoa học/kinh tế chuyên ngành) để tránh chồng lấn ảnh gốc — xem [docs/02](02-dataset-design.md#nguồn-dữ-liệu).

### So sánh với VMMU

VMMU không tập trung vào chart mà là benchmark đa nhiệm (STEM, suy luận trừu tượng, quy tắc thị giác). Điểm hữu ích nhất từ VMMU cho ViChartQA là **luận điểm khoa học**: khoảng cách giữa OCR tiếng Việt (đã tốt) và suy luận đa phương thức thật sự (còn yếu, ~66% ở mô hình mạnh nhất) — ViChartQA có thể trích dẫn VMMU để củng cố motivation, đồng thời chứng minh khoảng cách này cụ thể hơn trên một tác vụ có cấu trúc rõ (chart) thay vì đa nhiệm rời rạc.

## 4b. Dòng multi-hop QA trên dữ liệu có cấu trúc (text + table/chart)

> **Bổ sung 11/07/2026 sau khi đổi hướng dataset** (xem README, docs/02). Claim chính của ViChartQA chuyển từ "chart-only, chart tiếng Việt độ khó cao" sang "multi-hop reasoning kết hợp text + chart trong cùng bài viết" — dòng công trình gần nhất **không phải** ChartQA/CharXiv (chart cô lập) mà là các dataset multi-hop text+table dưới đây. Phải trích dẫn và định vị rõ trong bài, nếu không reviewer sẽ coi ViChartQA là "phiên bản chart hoá của HybridQA" mà không biết nhóm đã cân nhắc điều đó.
>
> **Giới hạn verify:** số liệu bảng dưới lấy qua WebSearch/trang GitHub/HuggingFace chính thức của từng dataset (không phải đọc trực tiếp PDF + `pdftotext` như quy trình đã áp dụng cho bảng ở mục 1) — **cần Pod A/E đối chiếu lại với paper gốc trước khi đưa vào bản thảo cuối**, theo đúng nguyên tắc verify của repo này.

| Dataset | Nguồn | Quy mô | Đặc điểm multi-hop |
|---|---|---|---|
| [HybridQA](https://arxiv.org/abs/2004.07347) | Bảng Wikipedia + đoạn văn liên kết thực thể | 62,682 train / 3,466 dev / 3,463 test (~69.6K QA) | Multi-hop bắt buộc qua bảng + đoạn văn ngoài bảng |
| [TAT-QA](https://arxiv.org/abs/2105.07624) | 182 báo cáo tài chính thực tế | 16,552 QA / 2,757 hybrid context | 1 bảng + ≥2 đoạn văn liên quan; nhiều câu cần numerical reasoning qua cả hai |
| [MultiHiertt](https://arxiv.org/pdf/2206.01347) | Báo cáo tài chính, bảng phân cấp (hierarchical) | 10,440 QA / 2,513 document, trung bình 3.89 bảng/document | Tự báo cáo rõ **48.74%** câu hỏi cần cả text+table (10.24% chỉ cần text, 33.09%+7.93% chỉ cần bảng) — mốc tham chiếu hữu ích để đặt ngưỡng tỷ trọng multi-hop cho ViChartQA |
| [SlideVQA](https://arxiv.org/abs/2301.04883) | Slide thuyết trình (SlideShare), có chart/table/text trong ảnh | 14,500 QA / 2,600 slide deck / 52K ảnh | Multi-hop qua **nhiều ảnh** (không chỉ text+bảng thuần), có annotate expression số học — gần với setup "nhiều chart trong 1 bài" của ViChartQA nhất |
| [DCQA](https://arxiv.org/pdf/2310.18983) | Document **synthetic** (dựng tự động), chart chèn vào layout giả | 50,010 document / 699,051 QA | Tên gọi giống "document-level chart QA" nhưng document là tổng hợp máy dựng, câu hỏi vẫn chỉ xoay quanh chart (template-based) — **không** phải multi-hop text+chart thật; cần nêu rõ khác biệt này khi trích dẫn |
| [DocHop-QA](https://arxiv.org/abs/2508.15851) (2025) | Bài báo PubMed thật, multi-document | 11,379 instance | Multi-hop multimodal thật (text + table + layout cue), nhưng miền y sinh tiếng Anh, sinh câu hỏi bằng pipeline LLM — gần nhất về mặt "document thật + multi-hop thật" nhưng khác domain/ngôn ngữ |

**Khoảng trống còn lại sau khi trừ hết bảng trên:** chưa có dataset nào kết hợp (a) **tiếng Việt**, (b) document **thật** (không synthetic như DCQA), (c) multi-hop bắt buộc đọc **ảnh chart** (không phải bảng số liệu như HybridQA/TAT-QA/MultiHiertt), (d) miền khoa học/kinh tế Việt Nam. Đây là góc claim chính xác của ViChartQA — không phải "chưa ai làm multi-hop chart" (sai) mà là "chưa ai làm multi-hop chart-ảnh-thật tiếng Việt".

**Ngưỡng tỷ trọng đề xuất:** dựa theo MultiHiertt (48.74% câu hỏi thật sự multi-hop), ViChartQA nên đặt mục tiêu **≥50% câu hỏi ở test set** yêu cầu evidence từ ≥2 nguồn (text+chart hoặc chart+chart) để có căn cứ so sánh khi viết bài — không cần ép 100%, phần còn lại là câu hỏi single-chart tự nhiên phát sinh từ cùng document, vẫn dùng được để so sánh trực tiếp với ChartQA/ChartQAPro.

## 4. Mô hình VLM tiếng Việt hiện có (ứng viên backbone)

| Mô hình | Kiến trúc | Ghi chú |
|---|---|---|
| Vintern-1B / -1B-v2 / -3B (5CD-AI) | InternViT-300M-448px + Qwen2-0.5B-Instruct, nối bằng MLP (xác nhận trực tiếp trong paper arXiv:2408.12480) | Huấn luyện trên 3M+ cặp ảnh-hỏi-đáp tiếng Việt; OpenViVQA-dev 7.7/10, ViTextVQA-dev 7.7/10 (đánh giá kiểu GPT-4o-as-judge, v2) |
| LaVy | — | VLM tiếng Việt tổng quát, không chuyên biệt cho tài liệu/chart (chưa đọc sâu bài này) |

> ⚠️ **Cần phân biệt nguồn khi trích dẫn Vintern:** bài báo arXiv (2408.12480) chỉ nhắc "chart" đúng **một lần**, ở dạng liệt kê chung chung ("understanding documents, charts, infographics"), **không có** benchmark Chart-VQA riêng hay điểm MTVQA nào trong bài. Claim "Vintern có Chart-VQA, MTVQA tiếng Việt xếp hạng 3 (31.7 điểm)" mà bản rà soát trước đây đưa ra chỉ xuất hiện trên **trang model card Hugging Face** (nội dung có thể chỉnh sửa liên tục, không qua peer review) — không phải trong bài báo đã công bố. Trước khi dùng làm luận điểm trong bài, cần: (1) tự đo lại Vintern trên một tập chart mẫu, hoặc (2) trích dẫn model card như một nguồn thứ cấp, ghi rõ đây không phải số liệu từ bài báo.

## 5. Kết luận: năm khoảng trống ViChartQA lấp

1. **Multi-hop text + chart-ảnh-thật, tiếng Việt** — khoảng trống chính (xem mục 4b): không trùng ChartQA/CharXiv (chart cô lập, không multi-hop), không trùng HybridQA/TAT-QA/MultiHiertt (multi-hop nhưng dùng bảng chứ không phải ảnh chart), không trùng DCQA (document synthetic, không multi-hop thật), không trùng DocHop-QA (multi-hop thật nhưng tiếng Anh/y sinh).
2. **Document thật, không phải chart cô lập** — mỗi mẫu là bài viết (title + content + 1-3 chart), kế thừa đúng thực tế nguồn dữ liệu tiếng Việt (chart tiếng Việt chất lượng tốt chủ yếu nằm trong bài báo/báo cáo, không phải kho chart rời như Statista).
3. **Độ khó phù hợp 2026** — vẫn giữ tinh thần ChartQAPro/CharXiv (đa dạng dạng câu hỏi, tránh benchmark bị "giải" ngay khi công bố), cộng thêm lớp khó multi-hop mà cả hai benchmark đó không có.
4. **Miền chuyên môn, mở rộng theo nguồn cung thực tế** — ưu tiên kinh tế (đã xác nhận nguồn dồi dào), mở sang khoa học/giáo dục/y tế/môi trường/năng lượng nếu tìm được nguồn cùng dạng document (xem [docs/02](02-dataset-design.md#miền-dữ-liệu)) — khác với ảnh tổng quát của ViVQA/OpenViVQA/EVJVQA.
5. **Mô hình mở cạnh tranh trong miền hẹp** — không cần thắng GPT-4o/Gemini toàn diện, chỉ cần thắng trên đúng miền tiếng Việt với chi phí thấp hơn nhiều (đúng mô-típ ChartGemma/ChartMoE).

## Nguồn & phương pháp verify

Xem danh sách đầy đủ kèm liên kết arXiv tại cuối artifact kế hoạch đã chia sẻ với nhóm, hoặc README gốc.

**Vòng verify 11/07/2026:** toàn bộ số liệu trong bảng ở trên (trừ Chart-R1/RVR/RL và LaVy, chỉ xác nhận qua abstract/tiêu đề) đã được kiểm chứng bằng cách tải PDF gốc từ arXiv/ACL Anthology, chuyển sang text bằng `pdftotext -layout`, và đọc trực tiếp phần abstract + bảng số liệu — không dùng bản tóm tắt của công cụ tìm kiếm. Vòng này phát hiện và sửa 1 lỗi đáng kể (ChartBench: nhầm quy mô test-set thành toàn bộ dataset) và bổ sung số liệu cho 2 mục trước đó chỉ mô tả mơ hồ (FinChart-Bench, ChartX). Đã đối chiếu chéo repo GitHub `vis-nlp/ChartQAPro` — khớp với thông tin trong paper.

**Giới hạn còn lại:** số liệu vẫn có thể lỗi thời nếu các paper này ra bản cập nhật (arXiv cho phép sửa version) sau 07/2026 — kiểm tra lại version mới nhất trước khi đưa vào bản thảo cuối cùng. Không tự suy diễn số liệu nào ngoài những gì trích được trực tiếp từ text.
