# 01 — Bối cảnh & rà soát công trình liên quan

Mục tiêu: xác định ViChartQA khác gì với các công trình gần nhất, để Related Work không bị xem là "bản dịch ChartQA" hoặc "trùng ViInfographicVQA".

## 1. Dòng Chart QA tiếng Anh

| Bộ dữ liệu | Nguồn ảnh | Quy mô | Kiểu câu hỏi | Năm |
|---|---|---|---|---|
| FigureQA | Vẽ tự động (Matplotlib) | 180K chart / 2.3M QA | Template, từ vựng cố định | 2017 |
| DVQA | Vẽ tự động | 300K chart / 3.4M QA | Template, từ vựng cố định | 2018 |
| PlotQA | Vẽ tự động | 224K chart / 28M QA | Template, từ vựng mở | 2020 |
| ChartQA | Statista, Pew, OWID, OECD (thực tế) | 20.9K chart / 32.7K QA | Người viết + sinh bằng T5; compositional + visual | 2022 |
| ChartX / ChartVLM | GPT-4 sinh code vẽ hàng loạt | bộ eval 6K chart · 18 loại chart · 7 tác vụ · 22 chủ đề | QA + caption + trích xuất, đa tác vụ | 2024 |
| CharXiv | Bài báo khoa học trên arXiv | 2,323 chart (1.000 val + 1.323 test) | Mô tả (descriptive) + suy luận (reasoning) | 2024 |
| ChartBench | Tổng hợp, 42 danh mục chart | Toàn bộ: 66.624 chart / ≈600K QA (train); riêng test set: 2.100 chart / 18.900 QA | Acc+ (đúng/sai 2 chiều) + Number QA | 2023–24 |
| ChartQAPro | 157 nền tảng web (thực tế) | 1.341 chart / 1.948 QA | 6 loại: factoid, trắc nghiệm, hội thoại, giả định, fact-check, không trả lời được | 2025 |
| FinChart-Bench | Biểu đồ tài chính thực tế (2015–2024) | 1.200 chart / 7.016 QA, 25 LVLM được đánh giá | Đa dạng, thiên suy luận tài chính | 2025 |

ChartBench: toàn bộ dataset và tập test là hai số khác nhau (66.624 vs 2.100 chart) — ghi rõ đang trích số nào.

ChartQA đã gần bão hoà ở một số mô hình mạnh: Claude Sonnet 3.5 đạt 90.50% trên ChartQA nhưng 55.81% trên ChartQAPro. GPT-4o đạt 37.67% trên ChartQAPro; human baseline 85.02%. CharXiv: GPT-4o 47.1% trên câu hỏi suy luận (84.5% mô tả đơn giản), human 80.5%/92.1%. Các benchmark 2024–2025 khó hơn ChartQA gốc bằng cách dùng chart "trong tự nhiên" từ nhiều nguồn (CharXiv: arXiv, ChartQAPro: 157 nguồn web), và đa dạng định dạng câu hỏi (trắc nghiệm, giả định, fact-check, hội thoại, không trả lời được).

Taxonomy câu hỏi của ViChartQA học theo hướng ChartQAPro — xem [docs/02](02-dataset-design.md#taxonomy-câu-hỏi).

## 2. Dòng chart-VLM chuyên biệt (mô hình)

| Mô hình | Backbone | Ý tưởng chính |
|---|---|---|
| ChartLlama | LLaVA-1.5 | Pipeline nhiều bước dùng GPT-4 sinh dữ liệu instruction |
| ChartGemma | PaliGemma (nhỏ) | Sinh dữ liệu instruction trực tiếp từ ảnh chart; nhỏ nhưng cạnh tranh |
| TinyChart | LLaVA-based, 3B tham số | Token-merging + Program-of-Thought; vượt ChartLlama/ChartAst (13B) và GPT-4V trên ChartQA |
| ChartMoE | InternLM-XComposer + Mixture-of-Experts connector | SOTA ChartQA 80.48% → 84.64%; kèm dataset ChartMoE-Align (~1 triệu bộ chart-table-JSON-code) |
| Chart-R1 / Chart-RVR / Chart-RL | Nhiều backbone khác nhau | RL với phần thưởng kiểm chứng được (RLVR) — xu hướng 2025–2026 |

Không mô hình nào huấn luyện từ đầu — tất cả fine-tune một backbone có sẵn. ViChartQA giữ lại bảng dữ liệu gốc của mỗi chart (xem [docs/02](02-dataset-design.md)) để hỗ trợ đánh giá và hướng RLVR.

## 3. Dòng VQA / đa phương thức tiếng Việt

| Bộ dữ liệu | Miền ảnh | Quy mô | Đặc điểm | Năm |
|---|---|---|---|---|
| ViVQA | Ảnh tổng quát (MS COCO, câu hỏi tiếng Việt) | 10.328 ảnh / 15.000 QA | Hierarchical Co-Attention baseline, Accuracy 0.3496 | 2021 |
| EVJVQA | Ảnh chụp tại Việt Nam | 5.000 ảnh / 33.000+ QA | 3 ngôn ngữ VI/EN/JA, shared task VLSP 2022 | 2022 |
| OpenViVQA | Ảnh tổng quát (Google search) | 11.199 ảnh / 37.914 QA | Câu trả lời mở, viết tay hoàn toàn | 2023 |
| ViOCRVQA / ViTextVQA | Ảnh có chữ | quy mô vừa–lớn | Đọc hiểu văn bản trong ảnh, thiên về OCR | 2024 |
| VMMU | STEM, biểu diễn dữ liệu, suy luận thị giác | 2.5K QA / 7 tác vụ | Proprietary VLM mạnh nhất chỉ ~66%; nghẽn ở suy luận, không phải OCR | 2025 |
| ViInfographicVQA | Infographic (kinh tế, y tế, xã hội…) | 6.7K ảnh / 20.4K QA | VLM hỗ trợ trích xuất + xác minh người; single & multi-image | 2025 |

### So sánh trực tiếp với ViInfographicVQA

Infographic là bố cục hỗn hợp (icon, text, chart nhỏ), câu hỏi chủ yếu đọc-trích xuất (ANLS ~71–75%). Chart là cấu trúc dữ liệu rõ (trục/chuỗi/mốc), câu hỏi đòi hỏi tính toán trên dữ liệu. ViInfographicVQA phủ 5 chủ đề rộng; ViChartQA tập trung khoa học+kinh tế, đào sâu suy luận số học/logic. Nguồn ảnh khác nhau: ViInfographicVQA dùng infographics.vn, ViChartQA ưu tiên GSO/báo cáo chuyên ngành.

### So sánh với VMMU

Không tập trung chart, là benchmark đa nhiệm. Luận điểm hữu ích: khoảng cách OCR tiếng Việt (tốt) vs suy luận đa phương thức (yếu, ~66% ở mô hình mạnh nhất).

## 4b. Dòng multi-hop QA trên dữ liệu có cấu trúc (text + table/chart)

Claim chính của ViChartQA là multi-hop reasoning kết hợp text + chart trong cùng bài viết — dòng công trình gần nhất không phải ChartQA/CharXiv (chart cô lập) mà là các dataset multi-hop text+table dưới đây.

> Số liệu bảng này cần verify lại qua paper gốc trước bản thảo cuối.

| Dataset | Nguồn | Quy mô | Đặc điểm multi-hop |
|---|---|---|---|
| [HybridQA](https://arxiv.org/abs/2004.07347) | Bảng Wikipedia + đoạn văn liên kết thực thể | 62,682 train / 3,466 dev / 3,463 test | Multi-hop bắt buộc qua bảng + đoạn văn ngoài bảng |
| [TAT-QA](https://arxiv.org/abs/2105.07624) | 182 báo cáo tài chính thực tế | 16,552 QA / 2,757 hybrid context | 1 bảng + ≥2 đoạn văn liên quan |
| [MultiHiertt](https://arxiv.org/pdf/2206.01347) | Báo cáo tài chính, bảng phân cấp | 10,440 QA / 2,513 document, 3.89 bảng/document | 48.74% câu hỏi cần cả text+table |
| [SlideVQA](https://arxiv.org/abs/2301.04883) | Slide thuyết trình (SlideShare) | 14,500 QA / 2,600 deck / 52K ảnh | Multi-hop qua nhiều ảnh, gần với setup ViChartQA nhất |
| [DCQA](https://arxiv.org/pdf/2310.18983) | Document synthetic | 50,010 document / 699,051 QA | Không phải multi-hop text+chart thật, câu hỏi vẫn template-based quanh chart |
| [DocHop-QA](https://arxiv.org/abs/2508.15851) | Bài báo PubMed thật, multi-document | 11,379 instance | Multi-hop multimodal thật nhưng miền y sinh tiếng Anh |

Khoảng trống: chưa có dataset kết hợp (a) tiếng Việt, (b) document thật (không synthetic), (c) multi-hop qua ảnh chart (không phải bảng số liệu), (d) miền khoa học/kinh tế Việt Nam.

Ngưỡng tỷ trọng: neo theo MultiHiertt (48.74% multi-hop thật) — ViChartQA đặt mục tiêu ≥50% câu hỏi test set yêu cầu evidence từ ≥2 nguồn.

## 4. Mô hình VLM tiếng Việt hiện có (ứng viên backbone)

| Mô hình | Kiến trúc | Ghi chú |
|---|---|---|
| Vintern-1B / -1B-v2 / -3B (5CD-AI) | InternViT-300M-448px + Qwen2-0.5B-Instruct, MLP | 3M+ cặp ảnh-hỏi-đáp tiếng Việt; OpenViVQA-dev 7.7/10, ViTextVQA-dev 7.7/10 |
| LaVy | — | VLM tiếng Việt tổng quát, không chuyên biệt tài liệu/chart |

Bài báo arXiv của Vintern (2408.12480) chỉ nhắc "chart" 1 lần, chung chung — không có benchmark Chart-VQA hay điểm MTVQA. Claim "Chart-VQA, MTVQA hạng 3 (31.7 điểm)" chỉ có trên model card Hugging Face (không peer-review) — cần tự đo lại hoặc trích dẫn model card như nguồn thứ cấp, ghi rõ không phải từ paper.

## 5. Kết luận: năm khoảng trống ViChartQA lấp

1. **Multi-hop text + chart-ảnh-thật, tiếng Việt** — không trùng ChartQA/CharXiv (chart cô lập), HybridQA/TAT-QA/MultiHiertt (multi-hop nhưng bảng không phải ảnh), DCQA (synthetic), DocHop-QA (multi-hop thật nhưng tiếng Anh/y sinh).
2. **Document thật** — mỗi mẫu là bài viết (title + content + 1-3 chart).
3. **Độ khó phù hợp 2026** — tinh thần ChartQAPro/CharXiv cộng thêm lớp khó multi-hop.
4. **Miền chuyên môn, mở rộng theo nguồn cung** — ưu tiên kinh tế, mở sang khoa học/giáo dục/y tế/môi trường/năng lượng.
5. **Mô hình mở cạnh tranh trong miền hẹp** — không cần thắng GPT-4o/Gemini toàn diện.
